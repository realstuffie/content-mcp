"""Tests for control requirements without a title."""

from content_agent.models.control import ControlFile, ControlRequirement


class TestOptionalRequirementTitle:
    def test_requirement_without_title(self):
        req = ControlRequirement(id="needed_rules", rules=["rule_a"])
        assert req.title == ""
        assert req.rules == ["rule_a"]

    def test_control_file_with_untitled_requirement_parses(self):
        control = ControlFile(
            id="stig_example",
            title="Example STIG",
            controls=[
                {"id": "needed_rules", "levels": ["high"], "rules": ["rule_a"]},
                {"id": "SV-1", "title": "Titled requirement", "rules": ["rule_b"]},
            ],
        )
        assert [c.id for c in control.controls] == ["needed_rules", "SV-1"]
        assert control.controls[0].title == ""
