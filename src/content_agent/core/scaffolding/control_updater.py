"""Control file requirement updater."""

import logging
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from content_agent.core.discovery.controls import (
    GENERIC_SUBSTITUTIONS,
    controls_dir_setting,
    find_requirement_file,
    load_control_yaml,
    requirements_directory,
)
from content_agent.core.integration import get_content_repository
from content_agent.core.integration.product_variables import load_product_variables
from content_agent.core.integration.ssg_modules import get_ssg_modules
from content_agent.models.control import CONTROL_STATUSES, ControlUpdateResult

logger = logging.getLogger(__name__)

VALID_STATUSES = frozenset(CONTROL_STATUSES)

# Status names this tool used to accept, and the ComplianceAsCode status to use instead
_RENAMED_STATUSES = {
    "partially_automated": "partial",
    "not_applicable": "not applicable",
}

# Matches `- id: VALUE` and `-   id: VALUE`, with optional quoting
_ID_PATTERN = re.compile(
    r"^(?P<dash_indent> *)-(?P<gap> +)id:\s+['\"]?(?P<req_id>[^'\"#\n]+?)['\"]?\s*(?:#.*)?$"
)
_KEY_PATTERN = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z_][\w-]*):(?:\s|$)")
_JINJA_STATEMENT = re.compile(r"^\s*\{\{?%")


class _UpdateRefused(Exception):
    """The requirement can't be edited safely as text."""


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_blank(line: str) -> bool:
    return not line.strip()


def _plain(value: Any) -> Any:
    """Copy parsed YAML into plain dicts and lists, so key order doesn't matter."""
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _same_id(value: Any, requirement_id: str) -> bool:
    if value is None:
        return False
    if value == requirement_id or str(value) == requirement_id:
        return True
    try:
        # An id like 1.10 is parsed as the number 1.1
        return bool(value == yaml.safe_load(requirement_id))
    except yaml.YAMLError:
        return False


def _find_requirement(controls: Any, requirement_id: str) -> dict[str, Any] | None:
    """Find a requirement in a parsed `controls` list, at any nesting depth."""
    if not isinstance(controls, list):
        return None
    for item in controls:
        if not isinstance(item, dict):
            continue
        if _same_id(item.get("id"), requirement_id):
            return item
        found = _find_requirement(item.get("controls"), requirement_id)
        if found is not None:
            return found
    return None


def _first_line(error: Exception) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


class ControlUpdater:
    """Updates rule mappings in control file requirements."""

    def __init__(self) -> None:
        self.content_repo = get_content_repository()

    def update_requirement_rules(
        self,
        control_id: str,
        requirement_id: str,
        rules: list[str],
        status: str = "automated",
        product: str | None = None,
    ) -> ControlUpdateResult:
        """Update rules and status for a specific requirement.

        Handles both inline and directory-based control files. Edits the text so
        Jinja2, comments, and formatting are kept, and only the requirement's own
        `rules` and `status` keys change; nested requirements are left alone. The
        edited text is parsed before it is written, and the file is left unchanged
        if anything else would change.

        Args:
            control_id: Control framework identifier
            requirement_id: Requirement identifier
            rules: List of rule IDs to set
            status: A ComplianceAsCode control status (default: "automated")
            product: Optional product ID to scope to product-specific controls
        """
        if status not in VALID_STATUSES:
            return self._failure(Path("."), self._invalid_status_message(status))

        # Resolve control file path
        if product is not None:
            from content_agent.core.discovery.controls import ControlDiscovery

            discovery = ControlDiscovery()
            control_file = discovery._resolve_control_file(control_id, product)
        else:
            controls_dir = self.content_repo.path / "controls"
            candidate = controls_dir / f"{control_id}.yml"
            control_file = candidate if candidate.exists() else None

        if control_file is None:
            return self._failure(Path("."), self._missing_control_message(control_id, product))

        substitutions = self._substitutions(product)
        data = controls_dir_setting(control_file)
        found = find_requirement_file(control_file, data, requirement_id)
        if found is None:
            directory = requirements_directory(control_file, data)
            searched = f"{control_file} or {directory}" if directory else str(control_file)
            return self._failure(
                control_file, f"Requirement '{requirement_id}' not found in {searched}"
            )

        return self._update_file(found[0], requirement_id, rules, status, substitutions)

    def _missing_control_message(self, control_id: str, product: str | None) -> str:
        message = f"Control file not found: {control_id}"
        if product is None:
            # Some policies, like nist_800_53, exist only per product
            products = sorted(
                path.parent.parent.name
                for path in self.content_repo.path.glob(f"products/*/controls/{control_id}.yml")
            )
            if products:
                message += (
                    f". It is defined per product ({', '.join(products)}); " "pass one as product."
                )
        return message

    def _update_file(
        self,
        file_path: Path,
        requirement_id: str,
        rules: list[str],
        status: str,
        substitutions: dict[str, Any],
    ) -> ControlUpdateResult:
        """Edit one requirement in a file, after checking the edited text."""
        content = file_path.read_text()
        try:
            updated = self._update_requirement_in_text(content, requirement_id, rules, status)
        except _UpdateRefused as e:
            return self._failure(file_path, f"{e} The file was left unchanged.")

        if updated is None:
            return self._failure(
                file_path, f"Requirement '{requirement_id}' not found in {file_path}"
            )

        problem, warnings = self._check_edit(
            file_path, updated, requirement_id, rules, status, substitutions
        )
        if problem:
            return self._failure(file_path, f"{problem} The file was left unchanged.")

        file_path.write_text(updated)

        return ControlUpdateResult(
            file_path=file_path,
            requirements_added=0,
            requirements_updated=1,
            requirements_unchanged=0,
            success=True,
            warnings=warnings,
        )

    def _update_requirement_in_text(
        self,
        content: str,
        requirement_id: str,
        rules: list[str],
        status: str,
    ) -> str | None:
        """Find and update a requirement block in raw YAML text.

        Returns the updated text, or None if the requirement was not found.

        Raises:
            _UpdateRefused: If Jinja2 conditionals make the edit ambiguous
        """
        lines = content.splitlines(keepends=True)
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"

        start = self._find_requirement_start(lines, requirement_id)
        if start is None:
            return None

        match = _ID_PATTERN.match(lines[start])
        if not match:
            return None
        # The requirement's keys line up with `id`, which is after the dash and
        # its spacing: `- id:` and `-   id:` are both common.
        key_indent = len(match["dash_indent"]) + 1 + len(match["gap"])

        end = self._find_requirement_end(lines, start, key_indent, requirement_id)
        fields = self._own_fields(lines, start, end, key_indent)

        for key in ("rules", "status"):
            if len(fields.get(key, [])) > 1:
                raise _UpdateRefused(
                    f"Requirement '{requirement_id}' has more than one '{key}' key, "
                    "probably inside Jinja2 conditionals. Edit it by hand."
                )

        edits: list[tuple[int, int, list[str]]] = []
        missing: list[str] = []
        status_line = f"{' ' * key_indent}status: {status}\n"

        if "rules" in fields:
            rules_start, rules_end = fields["rules"][0]
            value_lines = lines[rules_start + 1 : rules_end]
            if any(_JINJA_STATEMENT.match(line) for line in value_lines):
                raise _UpdateRefused(
                    f"The rules of requirement '{requirement_id}' use Jinja2 conditionals, "
                    "which replacing the list would drop. Edit it by hand."
                )
            item_indent = next(
                (_indent(line) for line in value_lines if line.lstrip().startswith("- ")),
                key_indent + 4,
            )
            edits.append(
                (rules_start, rules_end, self._format_rules_block(rules, key_indent, item_indent))
            )
        else:
            missing.extend(self._format_rules_block(rules, key_indent, key_indent + 4))

        if "status" in fields:
            status_start, status_end = fields["status"][0]
            edits.append((status_start, status_end, [status_line]))
        else:
            missing.append(status_line)

        if missing:
            # Before nested requirements if there are any, else at the end of the block
            insert_at = fields["controls"][0][0] if "controls" in fields else end
            edits.append((insert_at, insert_at, missing))

        for edit_start, edit_end, replacement in sorted(edits, key=lambda e: e[0], reverse=True):
            lines[edit_start:edit_end] = replacement

        return "".join(lines)

    def _find_requirement_start(self, lines: list[str], requirement_id: str) -> int | None:
        """Find the line index of `- id: <requirement_id>`."""
        for i, line in enumerate(lines):
            m = _ID_PATTERN.match(line)
            if m and m.group("req_id").strip() == requirement_id:
                return i
        return None

    def _find_requirement_end(
        self, lines: list[str], start: int, key_indent: int, requirement_id: str
    ) -> int:
        """Return the index after the requirement's last non-blank line.

        The requirement ends before the first non-blank line indented less than
        its keys, such as the next list item or a comment above it. Trailing blank
        lines are left outside, so separators between requirements stay in place.
        """
        last = start
        for i in range(start + 1, len(lines)):
            line = lines[i]
            if _is_blank(line):
                continue
            if _indent(line) < key_indent:
                if _JINJA_STATEMENT.match(line) and self._continues_after(lines, i, key_indent):
                    raise _UpdateRefused(
                        f"Requirement '{requirement_id}' is split by Jinja2 conditionals. "
                        "Edit it by hand."
                    )
                break
            last = i
        return last + 1

    def _continues_after(self, lines: list[str], index: int, key_indent: int) -> bool:
        """Whether the next line that isn't blank or Jinja2 is still inside the block."""
        for line in lines[index + 1 :]:
            if _is_blank(line) or _JINJA_STATEMENT.match(line):
                continue
            return _indent(line) >= key_indent
        return False

    def _own_fields(
        self, lines: list[str], start: int, end: int, key_indent: int
    ) -> dict[str, list[tuple[int, int]]]:
        """Map each of the requirement's own keys to the line spans holding it.

        A key's span covers the key line and its value: deeper-indented lines, or
        list items at the key's own indent. Trailing blank lines are not included.
        Keys of nested requirements and text inside block scalars are deeper than
        `key_indent`, so they are never treated as the requirement's own.
        """
        fields: dict[str, list[tuple[int, int]]] = {}
        i = start + 1
        while i < end:
            line = lines[i]
            key_match = _KEY_PATTERN.match(line) if _indent(line) == key_indent else None
            if not key_match:
                i += 1
                continue
            j = i + 1
            while j < end:
                following = lines[j]
                if not _is_blank(following):
                    depth = _indent(following)
                    is_value = depth > key_indent or (
                        depth == key_indent and following.lstrip().startswith("- ")
                    )
                    if not is_value:
                        break
                j += 1
            while j > i + 1 and _is_blank(lines[j - 1]):
                j -= 1
            fields.setdefault(key_match["key"], []).append((i, j))
            i = j
        return fields

    def _format_rules_block(self, rules: list[str], key_indent: int, item_indent: int) -> list[str]:
        """Format a rules list as YAML text lines."""
        pad = " " * key_indent
        if not rules:
            return [f"{pad}rules: []\n"]
        return [f"{pad}rules:\n"] + [f"{' ' * item_indent}- {rule}\n" for rule in rules]

    def _check_edit(
        self,
        file_path: Path,
        updated: str,
        requirement_id: str,
        rules: list[str],
        status: str,
        substitutions: dict[str, Any],
    ) -> tuple[str | None, list[str]]:
        """Parse the file before and after the edit, and compare.

        Returns a problem that should stop the write, if any, and warnings.
        Only the requirement's `rules` and `status` may differ.
        """
        try:
            before = load_control_yaml(file_path, substitutions)
        except Exception as e:
            return None, [
                f"{file_path.name} did not parse before the edit ({_first_line(e)}), "
                "so the edit could not be checked"
            ]

        with tempfile.TemporaryDirectory() as tmp:
            edited_file = Path(tmp) / file_path.name
            edited_file.write_text(updated)
            try:
                after = load_control_yaml(edited_file, substitutions)
            except Exception as e:
                return f"The edited file would not parse: {_first_line(e)}.", []

        expected = _plain(before)
        target = (
            _find_requirement(expected.get("controls"), requirement_id)
            if isinstance(expected, dict)
            else None
        )
        if target is None:
            return (
                f"Requirement '{requirement_id}' was not found when parsing {file_path.name}.",
                [],
            )
        target["rules"] = list(rules)
        target["status"] = status

        if _plain(after) != expected:
            return (
                f"The edit would change more of {file_path.name} than the rules and status "
                f"of requirement '{requirement_id}'.",
                [],
            )
        return None, []

    def _substitutions(self, product: str | None) -> dict[str, Any]:
        """Jinja2 variables for parsing control files, as ControlDiscovery uses them."""
        if product:
            try:
                env = load_product_variables(
                    get_ssg_modules().products, self.content_repo.path, product
                )
            except Exception as e:
                logger.debug(f"Product variables unavailable for {product}: {e}")
                env = None
            if env:
                return dict(env)
        return {**GENERIC_SUBSTITUTIONS, "product": product or ""}

    def _invalid_status_message(self, status: str) -> str:
        message = f"Invalid status '{status}'."
        spaced = status.replace("_", " ").strip().lower()
        suggestion = _RENAMED_STATUSES.get(status) or (spaced if spaced in VALID_STATUSES else None)
        if suggestion:
            message += f" Use '{suggestion}' instead."
        return f"{message} Must be one of: {', '.join(CONTROL_STATUSES)}"

    def _failure(self, file_path: Path, error: str) -> ControlUpdateResult:
        return ControlUpdateResult(
            file_path=file_path,
            requirements_added=0,
            requirements_updated=0,
            requirements_unchanged=0,
            success=False,
            errors=[error],
        )
