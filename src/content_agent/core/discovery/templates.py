"""Template discovery implementation.

ComplianceAsCode documents template parameters in
``docs/templates/template_reference.md``, and rules set them in the ``vars`` of
their ``template`` block. A template's schema combines the two: the documented
parameters with their descriptions, plus how often rules set each one, which
also shows parameters the reference leaves out.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from content_agent.core.discovery.rule_paths import rule_files
from content_agent.core.integration import get_content_repository
from content_agent.models import TemplateParameter, TemplateSchema, TemplateSummary

logger = logging.getLogger(__name__)

# The block runs over indented and blank lines, and Jinja2 statements, which
# rules often put at column 0 inside it
_TEMPLATE_BLOCK = re.compile(
    r"^template:[ \t]*\n((?:[ \t]+.*\n|[ \t]*\n|\{\{?%.*\n)*)", re.MULTILINE
)
_JINJA_STATEMENT = re.compile(r"^\s*\{\{?%.*$", re.MULTILINE)
_JINJA_EXPRESSION = re.compile(r"\{\{\{.*?\}\}\}")
_TOP_BULLET = re.compile(r"^-\s+")
_HEADING = re.compile(r"^#{1,3}\s")
_PARAMETER_ITEM = re.compile(
    r"^(?P<indent>\s+)-\s+\*\*(?P<name>[A-Za-z0-9_]+)\*\*\s*[-–:]?\s*(?P<text>.*)$"
)
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_OPTIONAL = re.compile(r"\boptional\b|\bdefault\b", re.IGNORECASE)
_DEFAULT_CODE = re.compile(r"\bdefault(?: value)?\s*(?:is|:|to)?\s*`(?P<value>[^`]*)`", re.I)
_DEFAULT_WORD = re.compile(r"\bdefault(?: value)?\s+(?:is|:)\s+(?P<value>[\w.-]+)", re.I)

_TYPE_NAMES = {
    bool: "boolean",
    int: "integer",
    float: "number",
    str: "string",
    list: "list",
    dict: "mapping",
}


@dataclass
class _ReferenceEntry:
    """A template's section in template_reference.md."""

    text: str
    description: str | None
    parameters: list[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class _TemplateUse:
    """The vars one rule passes to a template."""

    rule_id: str
    variables: dict[str, Any]
    had_jinja: bool


def _clean_text(lines: list[str]) -> str:
    return _BOLD.sub(r"\1", " ".join(line.strip() for line in lines if line.strip()))


def _first_paragraph(lines: list[str]) -> str | None:
    paragraph: list[str] = []
    for line in lines:
        if not line.strip():
            if paragraph:
                break
            continue
        paragraph.append(line)
    return _clean_text(paragraph) or None


def _parse_reference(content: str) -> dict[str, _ReferenceEntry]:
    """Split template_reference.md into one entry per `#### <template>` section."""
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    in_code = False
    for line in content.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        elif not in_code and line.startswith("#### "):
            current = sections.setdefault(line[5:].strip(), [])
            continue
        elif not in_code and _HEADING.match(line):
            # A higher-level heading ends the template sections under it
            current = None
            continue
        if current is not None:
            current.append(line)
    return {name: _parse_section(lines) for name, lines in sections.items()}


def _parse_section(lines: list[str]) -> _ReferenceEntry:
    """Read a section's description and documented parameters."""
    intro: list[str] = []
    bullets: list[list[str]] = []
    for line in lines:
        if _TOP_BULLET.match(line):
            bullets.append([_TOP_BULLET.sub("", line, count=1)])
        elif bullets:
            bullets[-1].append(line)
        else:
            intro.append(line)

    # Most sections open with a bullet; a few open with a paragraph
    description = _first_paragraph(intro)
    parameters: list[tuple[str, str]] = []
    for bullet in bullets:
        heading = bullet[0].strip()
        if heading.startswith("Parameters:"):
            parameters = _parse_parameters(bullet[1:])
        elif not heading.startswith("Languages:") and description is None:
            description = _first_paragraph(bullet)

    return _ReferenceEntry(
        text="\n".join(lines).strip(), description=description, parameters=parameters
    )


def _parse_parameters(lines: list[str]) -> list[tuple[str, str]]:
    """Read `-   **name** - description` items, with their continuation lines."""
    items: list[tuple[str, list[str]]] = []
    item_indent: int | None = None
    for line in lines:
        match = _PARAMETER_ITEM.match(line)
        if match and (item_indent is None or len(match["indent"]) == item_indent):
            item_indent = len(match["indent"])
            items.append((match["name"], [match["text"]]))
        elif items and line.strip():
            items[-1][1].append(line)

    parameters: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, text in items:
        if name not in seen:
            seen.add(name)
            parameters.append((name, _clean_text(text)))
    return parameters


def _documented_default(description: str) -> str | None:
    match = _DEFAULT_CODE.search(description) or _DEFAULT_WORD.search(description)
    if not match:
        return None
    return match["value"].strip().strip("\"'")


def _read_template_use(rule_file: Path) -> tuple[str, _TemplateUse] | None:
    """Read the template name and vars from a rule's `template` block.

    Only the block is parsed, as YAML. Jinja2 statements are dropped, so the
    vars of every branch are kept, and Jinja2 expressions become a placeholder.
    """
    try:
        text = rule_file.read_text()
    except OSError:
        return None
    match = _TEMPLATE_BLOCK.search(text)
    if not match:
        return None
    block = "template:\n" + match.group(1)
    had_jinja = "{{" in block
    if had_jinja:
        block = _JINJA_EXPRESSION.sub("JINJA_EXPRESSION", _JINJA_STATEMENT.sub("", block))
    try:
        data = (yaml.safe_load(block) or {}).get("template")
    except yaml.YAMLError as e:
        logger.debug(f"Could not read the template block of {rule_file}: {e}")
        return None
    if not isinstance(data, dict) or not data.get("name"):
        return None
    variables = data.get("vars")
    return str(data["name"]), _TemplateUse(
        rule_id=rule_file.parent.name,
        variables=variables if isinstance(variables, dict) else {},
        had_jinja=had_jinja,
    )


def template_uses(repo_path: Path) -> dict[str, list[_TemplateUse]]:
    """Map each template to the rules that use it, reading the rule files on each call."""
    uses: dict[str, list[_TemplateUse]] = {}
    for rule_file in rule_files(repo_path):
        found = _read_template_use(rule_file)
        if found:
            uses.setdefault(found[0], []).append(found[1])
    for template_uses_list in uses.values():
        template_uses_list.sort(key=lambda use: use.rule_id)
    return uses


def _type_name(value: Any) -> str:
    for python_type, name in _TYPE_NAMES.items():
        if isinstance(value, python_type):
            return name
    return "string"


class TemplateDiscovery:
    """Template discovery and schema extraction."""

    def __init__(self) -> None:
        """Initialize template discovery."""
        self.content_repo = get_content_repository()

    def list_templates(self) -> list[TemplateSummary]:
        """List all available templates.

        Returns:
            List of TemplateSummary objects
        """
        logger.debug("Listing all templates")
        templates = []

        templates_dir = self.content_repo.path / "shared" / "templates"
        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return []

        reference = self._load_reference()
        for template_dir in templates_dir.iterdir():
            if not template_dir.is_dir():
                continue

            template_name = template_dir.name
            entry = reference.get(template_name)
            summary = TemplateSummary(
                name=template_name,
                description=entry.description if entry else None,
                language="jinja2",
                category=self._guess_category(template_name),
            )
            templates.append(summary)

        templates.sort(key=lambda t: t.name)
        logger.info(f"Found {len(templates)} templates")
        return templates

    def get_template_schema(self, template_name: str) -> TemplateSchema | None:
        """Get schema for a template.

        Parameters come from the template's section in template_reference.md and
        from the vars of the rules that use the template. A documented parameter
        is required unless its description calls it optional or gives a default,
        or some rules leave it out. A parameter only rules set is required when
        every rule using the template sets it.

        Args:
            template_name: Template name

        Returns:
            TemplateSchema or None if not found
        """
        logger.debug(f"Getting schema for template: {template_name}")

        template_dir = self.content_repo.path / "shared" / "templates" / template_name
        if not template_dir.is_dir():
            logger.warning(f"Template not found: {template_name}")
            return None

        entry = self._load_reference().get(template_name)
        uses = template_uses(self.content_repo.path).get(template_name, [])
        parameters = self._build_parameters(entry, uses)
        example = self._pick_example(uses, {p.name for p in parameters if p.required})

        return TemplateSchema(
            name=template_name,
            description=entry.description if entry else None,
            parameters=parameters,
            supported_languages=self._supported_languages(template_dir),
            used_by_rules=len(uses),
            example_rule=example.rule_id if example else None,
            example_usage=dict(example.variables) if example else None,
            documentation=(entry.text or None) if entry else None,
        )

    def _build_parameters(
        self, entry: _ReferenceEntry | None, uses: list[_TemplateUse]
    ) -> list[TemplateParameter]:
        counts: dict[str, int] = {}
        types: dict[str, set[str]] = {}
        for use in uses:
            seen: set[str] = set()
            for key, value in use.variables.items():
                base = str(key).split("@", 1)[0]
                seen.add(base)
                types.setdefault(base, set()).add(_type_name(value))
            for base in seen:
                counts[base] = counts.get(base, 0) + 1

        def type_of(name: str) -> str:
            found = types.get(name)
            return " | ".join(sorted(found)) if found else "unknown"

        total = len(uses)
        parameters: list[TemplateParameter] = []
        documented = entry.parameters if entry else []
        for name, description in documented:
            used = counts.get(name, 0)
            optional = bool(_OPTIONAL.search(description)) or (total > 0 and used < total)
            parameters.append(
                TemplateParameter(
                    name=name,
                    type=type_of(name),
                    required=not optional,
                    description=description,
                    default=_documented_default(description) if optional else None,
                    used_by_rules=used,
                )
            )

        documented_names = {name for name, _ in documented}
        undocumented = sorted(
            (name for name in counts if name not in documented_names),
            key=lambda name: (-counts[name], name),
        )
        for name in undocumented:
            used = counts[name]
            parameters.append(
                TemplateParameter(
                    name=name,
                    type=type_of(name),
                    required=used == total,
                    description=(
                        "Not in template_reference.md. "
                        f"Set by {used} of the {total} rules that use this template."
                    ),
                    used_by_rules=used,
                )
            )
        return parameters

    def _pick_example(self, uses: list[_TemplateUse], required: set[str]) -> _TemplateUse | None:
        """Pick the smallest real use that sets every required parameter.

        Uses without Jinja2 or product overrides are preferred, since they can be
        copied as they are.
        """
        plain = [
            use
            for use in uses
            if use.variables
            and not use.had_jinja
            and not any("@" in str(key) for key in use.variables)
        ]
        candidates = (
            [use for use in plain if required <= set(use.variables)]
            or plain
            or [use for use in uses if use.variables]
        )
        if not candidates:
            return None
        return min(candidates, key=lambda use: (len(use.variables), use.rule_id))

    def _supported_languages(self, template_dir: Path) -> list[str]:
        config_file = template_dir / "template.yml"
        try:
            data = yaml.safe_load(config_file.read_text()) or {}
        except (OSError, yaml.YAMLError) as e:
            logger.debug(f"Could not read {config_file}: {e}")
            return []
        languages = data.get("supported_languages") if isinstance(data, dict) else None
        return [str(language) for language in languages] if isinstance(languages, list) else []

    def _load_reference(self) -> dict[str, _ReferenceEntry]:
        ref_file = self.content_repo.path / "docs" / "templates" / "template_reference.md"
        if not ref_file.exists():
            logger.debug(f"Template reference file not found: {ref_file}")
            return {}
        try:
            return _parse_reference(ref_file.read_text())
        except Exception as e:
            logger.warning(f"Failed to read template reference file: {e}")
            return {}

    def _guess_category(self, template_name: str) -> str | None:
        """Guess template category from name.

        Args:
            template_name: Template name

        Returns:
            Category or None
        """
        # Simple category guessing based on name patterns
        if "sshd" in template_name or "ssh_" in template_name:
            return "ssh"
        elif "audit" in template_name:
            return "audit"
        elif "kernel" in template_name:
            return "kernel"
        elif "service" in template_name:
            return "services"
        elif "package" in template_name:
            return "packages"
        elif "file" in template_name or "permissions" in template_name:
            return "files"

        return None

    def _get_template_documentation(self, template_name: str) -> str | None:
        """Return a template's section of template_reference.md, or None.

        The section is everything after `#### <template_name>` up to the next
        heading.
        """
        entry = self._load_reference().get(template_name)
        return (entry.text or None) if entry else None


def list_templates() -> list[TemplateSummary]:
    """List all available templates.

    Returns:
        List of TemplateSummary objects
    """
    discovery = TemplateDiscovery()
    return discovery.list_templates()


def get_template_schema(template_name: str) -> TemplateSchema | None:
    """Get schema for a template.

    Args:
        template_name: Template name

    Returns:
        TemplateSchema or None if not found
    """
    discovery = TemplateDiscovery()
    return discovery.get_template_schema(template_name)
