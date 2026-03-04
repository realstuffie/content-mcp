"""Tests for ControlUpdater."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from content_agent.core.scaffolding.control_updater import ControlUpdater


def _write_inline_control(tmp_path: Path, control_id: str, content: str) -> Path:
    """Write an inline control YAML file and return the controls dir."""
    controls_dir = tmp_path / "controls"
    controls_dir.mkdir(exist_ok=True)
    control_file = controls_dir / f"{control_id}.yml"
    control_file.write_text(textwrap.dedent(content))
    return controls_dir


def _write_directory_control(
    tmp_path: Path,
    control_id: str,
    parent_content: str,
    req_files: dict[str, str],
    controls_subdir: str = "",
) -> Path:
    """Write a directory-based control structure."""
    controls_dir = tmp_path / "controls"
    controls_dir.mkdir(exist_ok=True)
    # Write parent file
    parent_file = controls_dir / f"{control_id}.yml"
    parent_file.write_text(textwrap.dedent(parent_content))
    # Write requirement files
    subdir = controls_dir / (controls_subdir or control_id)
    subdir.mkdir(exist_ok=True)
    for req_id, content in req_files.items():
        req_file = subdir / f"{req_id}.yml"
        req_file.write_text(textwrap.dedent(content))
    return controls_dir


@pytest.fixture()
def mock_content_repo(tmp_path: Path) -> MagicMock:
    """Create a mock content repository pointing at tmp_path."""
    repo = MagicMock()
    repo.path = tmp_path
    return repo


@pytest.fixture()
def updater(mock_content_repo: MagicMock) -> ControlUpdater:
    """Create a ControlUpdater with mocked content repo."""
    with patch(
        "content_agent.core.scaffolding.control_updater.get_content_repository",
        return_value=mock_content_repo,
    ):
        return ControlUpdater()


class TestInlineFormat:
    """Tests for inline (monolithic YAML) control files."""

    def test_replace_existing_rules(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            policy: Test
            title: Test
            id: test
            controls:
                - id: R1
                  title: First
                  status: pending
                  rules:
                      - old_rule_a
                      - old_rule_b
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["new_rule"], "automated")

        assert result.success
        assert result.requirements_updated == 1
        content = (tmp_path / "controls" / "test.yml").read_text()
        assert "new_rule" in content
        assert "old_rule_a" not in content
        assert "old_rule_b" not in content
        assert "status: automated" in content

    def test_add_missing_rules_field(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: First
                  status: pending
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["rule_a"])

        assert result.success
        content = (tmp_path / "controls" / "test.yml").read_text()
        assert "rules:" in content
        assert "rule_a" in content

    def test_add_missing_status_field(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: First
                  rules: []
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["rule_a"], "manual")

        assert result.success
        content = (tmp_path / "controls" / "test.yml").read_text()
        assert "status: manual" in content

    def test_preserves_other_requirements(self, updater: ControlUpdater, tmp_path: Path) -> None:
        original = """\
---
policy: Test
title: Test
id: test
controls:
    - id: R1
      title: First
      status: pending
      rules: []
    - id: R2
      title: Second
      status: automated
      rules:
          - existing_rule
    - id: R3
      title: Third
      status: pending
"""
        controls_dir = tmp_path / "controls"
        controls_dir.mkdir()
        (controls_dir / "test.yml").write_text(original)

        result = updater.update_requirement_rules("test", "R2", ["new_rule"], "manual")

        assert result.success
        content = (controls_dir / "test.yml").read_text()

        # R1 and R3 should be unchanged
        lines_before = original.splitlines()
        lines_after = content.splitlines()

        # Find R1 block in both — should be identical
        r1_start_before = next(i for i, ln in enumerate(lines_before) if "- id: R1" in ln)
        r1_start_after = next(i for i, ln in enumerate(lines_after) if "- id: R1" in ln)
        r2_start_before = next(i for i, ln in enumerate(lines_before) if "- id: R2" in ln)
        r2_start_after = next(i for i, ln in enumerate(lines_after) if "- id: R2" in ln)

        r1_block_before = lines_before[r1_start_before:r2_start_before]
        r1_block_after = lines_after[r1_start_after:r2_start_after]
        assert r1_block_before == r1_block_after

        # R3 block should be identical
        r3_start_before = next(i for i, ln in enumerate(lines_before) if "- id: R3" in ln)
        r3_start_after = next(i for i, ln in enumerate(lines_after) if "- id: R3" in ln)
        r3_block_before = lines_before[r3_start_before:]
        r3_block_after = lines_after[r3_start_after:]
        assert r3_block_before == r3_block_after

        # R2 should have new values
        assert "new_rule" in content
        assert "existing_rule" not in content


class TestDirectoryFormat:
    """Tests for directory-based control files."""

    def test_update_directory_format(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_directory_control(
            tmp_path,
            "srg",
            """\
            ---
            id: srg
            title: SRG
            controls_dir: srg
            """,
            {"SRG-001": """\
                    ---
                    controls:
                        - id: SRG-001
                          title: First SRG
                          status: pending
                          rules: []
                """},
        )

        result = updater.update_requirement_rules("srg", "SRG-001", ["rule_a", "rule_b"])

        assert result.success
        assert result.requirements_updated == 1
        content = (tmp_path / "controls" / "srg" / "SRG-001.yml").read_text()
        assert "rule_a" in content
        assert "rule_b" in content
        assert "status: automated" in content

    def test_directory_requirement_missing(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_directory_control(
            tmp_path,
            "srg",
            """\
            ---
            id: srg
            title: SRG
            controls_dir: srg
            """,
            {},
        )

        result = updater.update_requirement_rules("srg", "SRG-MISSING", ["rule_a"])

        assert not result.success
        assert any("not found" in e for e in result.errors)


class TestPreservation:
    """Tests for Jinja2, comment, and formatting preservation."""

    def test_preserves_jinja2(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: '{{{ full_name }}}'
                  description: >-
                      This uses {{{ full_name }}} template
                  status: pending
                  rules: []
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["rule_a"])

        assert result.success
        content = (tmp_path / "controls" / "test.yml").read_text()
        assert "{{{ full_name }}}" in content

    def test_preserves_jinja2_in_other_blocks(
        self, updater: ControlUpdater, tmp_path: Path
    ) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: First
                  status: pending
                  rules: []
                - id: R2
                  title: '{{{ full_name }}}'
                  description: >-
                      Uses {{{ full_name }}} and {% if something %}yes{% endif %}
                  status: pending
                  rules: []
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["rule_a"])

        assert result.success
        content = (tmp_path / "controls" / "test.yml").read_text()
        assert "{{{ full_name }}}" in content
        assert "{% if something %}" in content

    def test_preserves_comments(self, updater: ControlUpdater, tmp_path: Path) -> None:
        original = """\
---
# This is a policy comment
id: test
title: Test
controls:
    # First requirement
    - id: R1
      title: First
      status: pending
      rules: []
    # Second requirement
    - id: R2
      title: Second
      status: pending
      rules: []
"""
        controls_dir = tmp_path / "controls"
        controls_dir.mkdir()
        (controls_dir / "test.yml").write_text(original)

        result = updater.update_requirement_rules("test", "R1", ["rule_a"])

        assert result.success
        content = (controls_dir / "test.yml").read_text()
        assert "# This is a policy comment" in content
        assert "# First requirement" in content
        assert "# Second requirement" in content


class TestErrorCases:
    """Tests for error handling."""

    def test_nonexistent_control(self, updater: ControlUpdater, tmp_path: Path) -> None:
        (tmp_path / "controls").mkdir()

        result = updater.update_requirement_rules("nonexistent", "R1", ["rule_a"])

        assert not result.success
        assert any("not found" in e for e in result.errors)

    def test_nonexistent_requirement_inline(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: First
                  rules: []
            """,
        )

        result = updater.update_requirement_rules("test", "R99", ["rule_a"])

        assert not result.success
        assert any("not found" in e.lower() for e in result.errors)

    def test_invalid_status(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: First
                  rules: []
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["rule_a"], "unknown")

        assert not result.success
        assert any("Invalid status" in e for e in result.errors)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_rules_list(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: First
                  rules:
                      - old_rule
            """,
        )

        result = updater.update_requirement_rules("test", "R1", [])

        assert result.success
        content = (tmp_path / "controls" / "test.yml").read_text()
        assert "rules: []" in content
        assert "old_rule" not in content

    def test_quoted_requirement_id(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: "R1"
                  title: First
                  rules: []
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["rule_a"])

        assert result.success
        content = (tmp_path / "controls" / "test.yml").read_text()
        assert "rule_a" in content

    def test_single_quoted_requirement_id(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: 'R1'
                  title: First
                  rules: []
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["rule_a"])

        assert result.success

    def test_status_justification_not_clobbered(
        self, updater: ControlUpdater, tmp_path: Path
    ) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: First
                  status: pending
                  status_justification: Needs review by security team
                  rules:
                      - old_rule
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["new_rule"], "automated")

        assert result.success
        content = (tmp_path / "controls" / "test.yml").read_text()
        assert "status: automated" in content
        assert "status_justification: Needs review by security team" in content
        assert "new_rule" in content
        assert "old_rule" not in content

    def test_result_model_fields(self, updater: ControlUpdater, tmp_path: Path) -> None:
        _write_inline_control(
            tmp_path,
            "test",
            """\
            ---
            id: test
            title: Test
            controls:
                - id: R1
                  title: First
                  rules: []
            """,
        )

        result = updater.update_requirement_rules("test", "R1", ["rule_a"])

        assert result.success is True
        assert result.requirements_updated == 1
        assert result.requirements_added == 0
        assert result.requirements_unchanged == 0
        assert result.errors == []
        assert result.file_path == tmp_path / "controls" / "test.yml"
