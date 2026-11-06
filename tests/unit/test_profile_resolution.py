"""Tests for resolving profile selections, including control references."""

from content_agent.core.discovery.profile_resolution import ProfileRuleResolver
from content_agent.models.control import ControlFile
from content_agent.models.profile import ProfileDetails

POLICY = ControlFile(
    id="pol",
    title="Policy",
    levels=[
        {"id": "l1"},
        {"id": "l2", "inherits_from": ["l1"]},
        {"id": "l3", "inherits_from": ["l2"]},
    ],
    controls=[
        {"id": "R1", "title": "Level 1", "levels": ["l1"], "rules": ["rule_l1"]},
        {"id": "R2", "title": "Level 2", "levels": ["l2"], "rules": ["rule_l2", "var_x=1"]},
        {"id": "R3", "title": "Level 3", "levels": ["l3"], "rules": ["rule_l3", "!rule_l1"]},
        {"id": "R4", "title": "No level, so it belongs to l1", "rules": ["rule_default"]},
        {
            "id": "R5",
            "title": "Parent",
            "levels": ["l3"],
            "rules": ["rule_parent"],
            "controls": [
                {"id": "R5.1", "title": "Child", "levels": ["l3"], "rules": ["rule_child"]},
                "other:all:base",
            ],
        },
    ],
)

OTHER = ControlFile(
    id="other",
    title="Other policy",
    levels=[{"id": "base"}],
    controls=[{"id": "O1", "title": "Referenced", "levels": ["base"], "rules": ["rule_other"]}],
)


class FakeControls:
    def __init__(self, policies):
        self.policies = policies
        self.calls = 0

    def get_control_details(self, control_id, product=None):
        self.calls += 1
        return self.policies.get(control_id)


class FakeProfiles:
    def __init__(self, profiles):
        self.profiles = profiles

    def get_profile_details(self, profile_id, product):
        selections, extends = self.profiles.get(profile_id, (None, None))
        if selections is None:
            return None
        return ProfileDetails(
            profile_id=profile_id,
            title=profile_id,
            description="",
            product=product,
            extends=extends,
            selections=selections,
            file_path=f"{profile_id}.profile",
            rule_count=len(selections),
        )


def _resolve(profiles, profile_id="p"):
    controls = FakeControls({"pol": POLICY, "other": OTHER})
    resolver = ProfileRuleResolver(FakeProfiles(profiles), controls)
    return resolver.resolve_profile("prod", profile_id), controls


class TestControlSelections:
    def test_all_selects_every_requirement_with_references(self):
        rules, _ = _resolve({"p": (["pol:all"], None)})
        assert rules == {
            "rule_l1",
            "rule_l2",
            "rule_l3",
            "rule_default",
            "rule_parent",
            "rule_child",
            "rule_other",
        }

    def test_level_includes_inherited_levels_and_default_level(self):
        rules, _ = _resolve({"p": (["pol:all:l2"], None)})
        assert rules == {"rule_l1", "rule_l2", "rule_default"}

    def test_lowest_level_only(self):
        rules, _ = _resolve({"p": (["pol:all:l1"], None)})
        assert rules == {"rule_l1", "rule_default"}

    def test_single_requirement_includes_children_and_references(self):
        rules, _ = _resolve({"p": (["pol:R5"], None)})
        assert rules == {"rule_parent", "rule_child", "rule_other"}

    def test_unknown_policy_or_requirement_selects_nothing(self):
        rules, _ = _resolve({"p": (["missing:all", "pol:R99", "direct_rule"], None)})
        assert rules == {"direct_rule"}

    def test_control_level_unselections_and_variables_are_ignored(self):
        # The build merges only selected rules from controls, so "!rule_l1" in R3
        # doesn't remove rule_l1 and "var_x=1" isn't a rule.
        rules, _ = _resolve({"p": (["pol:all:l3"], None)})
        assert "rule_l1" in rules
        assert "var_x=1" not in rules

    def test_control_files_are_loaded_once_per_product(self):
        _, controls = _resolve({"p": (["pol:all", "pol:all:l1", "pol:R1"], None)})
        assert controls.calls == 2  # pol, plus other through the R5 reference


class TestProfileSelections:
    def test_unselection_removes_rules_from_controls(self):
        rules, _ = _resolve({"p": (["pol:all:l1", "!rule_default"], None)})
        assert rules == {"rule_l1"}

    def test_variables_and_refinements_select_nothing(self):
        rules, _ = _resolve({"p": (["var_a=1", "rule_a.severity=high", "rule_a"], None)})
        assert rules == {"rule_a"}

    def test_extends_adds_parent_rules_and_child_can_unselect(self):
        profiles = {
            "parent": (["parent_rule", "shared_rule"], None),
            "p": (["child_rule", "!shared_rule"], "parent"),
        }
        rules, _ = _resolve(profiles)
        assert rules == {"parent_rule", "child_rule"}

    def test_extends_loop_is_ignored(self):
        profiles = {"a": (["rule_a"], "b"), "b": (["rule_b"], "a")}
        rules, _ = _resolve(profiles, "a")
        assert rules == {"rule_a", "rule_b"}

    def test_missing_profile(self):
        rules, _ = _resolve({}, "nope")
        assert rules == set()
