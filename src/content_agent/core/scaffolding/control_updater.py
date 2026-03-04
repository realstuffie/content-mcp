"""Control file requirement updater."""

import logging
import re
from pathlib import Path

import yaml

from content_agent.core.integration import get_content_repository
from content_agent.models.control import ControlUpdateResult

logger = logging.getLogger(__name__)

VALID_STATUSES = frozenset(
    {"automated", "partially_automated", "manual", "not_applicable", "pending"}
)

# Matches `- id: VALUE` with optional quoting and flexible whitespace
_ID_PATTERN = re.compile(r"^(\s*)-\s+id:\s+['\"]?(?P<req_id>[^'\"#\n]+?)['\"]?\s*(?:#.*)?$")


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

        Handles both inline and directory-based control files.
        Uses text-based editing to preserve Jinja2, comments, and formatting.

        Args:
            control_id: Control framework identifier
            requirement_id: Requirement identifier
            rules: List of rule IDs to set
            status: Status to set (default: "automated")
            product: Optional product ID to scope to product-specific controls
        """
        if status not in VALID_STATUSES:
            return ControlUpdateResult(
                file_path=Path("."),
                requirements_added=0,
                requirements_updated=0,
                requirements_unchanged=0,
                success=False,
                errors=[
                    f"Invalid status '{status}'. "
                    f"Must be one of: {', '.join(sorted(VALID_STATUSES))}"
                ],
            )

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
            return ControlUpdateResult(
                file_path=Path("."),
                requirements_added=0,
                requirements_updated=0,
                requirements_unchanged=0,
                success=False,
                errors=[f"Control file not found: {control_id}"],
            )

        # Determine format by checking for controls_dir field
        with open(control_file) as f:
            data = yaml.safe_load(f)

        if data.get("controls_dir"):
            return self._update_directory_format(
                control_file.parent, data["controls_dir"], requirement_id, rules, status
            )
        else:
            return self._update_inline_format(control_file, requirement_id, rules, status)

    def _update_directory_format(
        self,
        controls_dir: Path,
        controls_subdir: str,
        requirement_id: str,
        rules: list[str],
        status: str,
    ) -> ControlUpdateResult:
        """Update a requirement in a directory-based control file."""
        req_file = controls_dir / controls_subdir / f"{requirement_id}.yml"

        if not req_file.exists():
            return ControlUpdateResult(
                file_path=req_file,
                requirements_added=0,
                requirements_updated=0,
                requirements_unchanged=0,
                success=False,
                errors=[f"Requirement file not found: {req_file}"],
            )

        content = req_file.read_text()
        updated = self._update_requirement_in_text(content, requirement_id, rules, status)

        if updated is None:
            return ControlUpdateResult(
                file_path=req_file,
                requirements_added=0,
                requirements_updated=0,
                requirements_unchanged=0,
                success=False,
                errors=[f"Requirement '{requirement_id}' not found in {req_file}"],
            )

        req_file.write_text(updated)

        return ControlUpdateResult(
            file_path=req_file,
            requirements_added=0,
            requirements_updated=1,
            requirements_unchanged=0,
            success=True,
        )

    def _update_inline_format(
        self,
        control_file: Path,
        requirement_id: str,
        rules: list[str],
        status: str,
    ) -> ControlUpdateResult:
        """Update a requirement in an inline (monolithic) control file."""
        content = control_file.read_text()
        updated = self._update_requirement_in_text(content, requirement_id, rules, status)

        if updated is None:
            return ControlUpdateResult(
                file_path=control_file,
                requirements_added=0,
                requirements_updated=0,
                requirements_unchanged=0,
                success=False,
                errors=[f"Requirement '{requirement_id}' not found in {control_file}"],
            )

        control_file.write_text(updated)

        return ControlUpdateResult(
            file_path=control_file,
            requirements_added=0,
            requirements_updated=1,
            requirements_unchanged=0,
            success=True,
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
        """
        lines = content.splitlines(keepends=True)
        req_start = self._find_requirement_start(lines, requirement_id)
        if req_start is None:
            return None

        # Determine the indentation of the `- id:` line
        match = _ID_PATTERN.match(lines[req_start])
        if not match:
            return None
        list_indent = match.group(1)  # spaces before `-`
        # Properties are indented further than the `-`
        prop_indent = list_indent + "  "

        # Find the end of this requirement block
        req_end = self._find_requirement_end(lines, req_start, list_indent)

        # Extract the requirement block lines
        block_lines = lines[req_start:req_end]

        # Update rules and status within the block
        updated_block = self._update_block_fields(block_lines, rules, status, prop_indent)

        # Reconstruct the file
        result_lines = lines[:req_start] + updated_block + lines[req_end:]
        return "".join(result_lines)

    def _find_requirement_start(self, lines: list[str], requirement_id: str) -> int | None:
        """Find the line index of `- id: <requirement_id>`."""
        for i, line in enumerate(lines):
            m = _ID_PATTERN.match(line)
            if m and m.group("req_id").strip() == requirement_id:
                return i
        return None

    def _find_requirement_end(self, lines: list[str], start: int, list_indent: str) -> int:
        """Find the end of a requirement block (exclusive index).

        The block ends at the next list item at the same indent level,
        or at a line with equal/lesser indentation that isn't a continuation.
        """
        indent_len = len(list_indent)
        for i in range(start + 1, len(lines)):
            line = lines[i]
            stripped = line.rstrip("\n\r")

            # Skip blank lines — they could be inside the block
            if not stripped:
                continue

            # Count leading spaces
            line_indent = len(stripped) - len(stripped.lstrip(" "))

            # A new list item at the same indent level ends the block
            if line_indent == indent_len and stripped.lstrip().startswith("- "):
                return i

            # A line at lesser indentation ends the block
            if line_indent < indent_len:
                return i

        return len(lines)

    def _update_block_fields(
        self,
        block_lines: list[str],
        rules: list[str],
        status: str,
        prop_indent: str,
    ) -> list[str]:
        """Update rules and status fields within a requirement block."""
        result: list[str] = []
        i = 0
        found_rules = False
        found_status = False

        while i < len(block_lines):
            line = block_lines[i]
            stripped = line.lstrip()

            # Detect `rules:` field (exact key, not rules_*)
            if stripped.rstrip() == "rules:" or stripped.startswith("rules: "):
                found_rules = True
                result.extend(self._format_rules_block(rules, prop_indent))
                i += 1
                # Skip old rules list items (lines starting with `- ` at deeper indent)
                rules_indent_len = len(line) - len(stripped)
                while i < len(block_lines):
                    next_line = block_lines[i]
                    next_stripped = next_line.lstrip()
                    if not next_stripped:
                        i += 1
                        continue
                    next_indent = len(next_line) - len(next_stripped)
                    if next_indent > rules_indent_len and next_stripped.startswith("- "):
                        i += 1
                    else:
                        break
                continue

            # Detect `status:` field (exact key, not status_justification etc.)
            if stripped.rstrip() == "status:" or stripped.startswith("status: "):
                found_status = True
                result.append(f"{prop_indent}status: {status}\n")
                i += 1
                continue

            result.append(line)
            i += 1

        # Add missing fields before end of block
        if not found_rules:
            result.extend(self._format_rules_block(rules, prop_indent))
        if not found_status:
            result.append(f"{prop_indent}status: {status}\n")

        return result

    def _format_rules_block(self, rules: list[str], indent: str) -> list[str]:
        """Format a rules list as YAML text lines at the given indentation."""
        if not rules:
            return [f"{indent}rules: []\n"]
        lines = [f"{indent}rules:\n"]
        for rule in rules:
            lines.append(f"{indent}    - {rule}\n")
        return lines
