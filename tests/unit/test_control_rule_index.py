"""Tests for control rule index functionality."""

from unittest.mock import patch

from content_agent.models.control import (
    ControlFile,
    ControlRequirement,
    ControlRuleIndex,
    IndexedRequirement,
)


def _make_requirement(
    req_id: str,
    title: str = "Test",
    description: str = "Test description",
    rules: list[str] | None = None,
    status: str = "pending",
) -> ControlRequirement:
    return ControlRequirement(
        id=req_id,
        title=title,
        description=description,
        rules=rules or [],
        status=status,
    )


def _make_control_file(
    control_id: str,
    title: str = "Test Control",
    controls: list[ControlRequirement] | None = None,
) -> ControlFile:
    return ControlFile(
        id=control_id,
        title=title,
        controls=controls or [],
    )


class TestIndexedRequirementModel:
    """Test IndexedRequirement Pydantic model."""

    def test_basic_creation(self):
        req = IndexedRequirement(
            control_id="anssi",
            requirement_id="R1",
            title="Test Requirement",
            description="A test requirement",
            rules=["rule_a", "rule_b"],
        )
        assert req.control_id == "anssi"
        assert req.requirement_id == "R1"
        assert req.status == "pending"
        assert len(req.rules) == 2

    def test_defaults(self):
        req = IndexedRequirement(
            control_id="test",
            requirement_id="T1",
            title="Test",
            description="Test",
        )
        assert req.rules == []
        assert req.status == "pending"
        assert req.levels == []


class TestControlRuleIndexModel:
    """Test ControlRuleIndex Pydantic model."""

    def test_basic_creation(self):
        index = ControlRuleIndex(
            total_controls=2,
            total_requirements=10,
            total_mapped_rules=5,
        )
        assert index.total_controls == 2
        assert index.total_requirements == 10
        assert index.total_mapped_rules == 5
        assert index.requirements == []


class TestGetControlRuleIndex:
    """Test ControlDiscovery.get_control_rule_index()."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_index_all_controls(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req1 = _make_requirement("R1", rules=["rule_a"])
        req2 = _make_requirement("R2", rules=["rule_b", "rule_c"])
        req3 = _make_requirement("R3")  # unmapped

        cf1 = _make_control_file("anssi", controls=[req1, req2])
        cf2 = _make_control_file("cis", controls=[req3])

        with patch.object(discovery, "list_controls", return_value=["anssi", "cis"]):
            with patch.object(
                discovery,
                "get_control_details",
                side_effect=lambda cid: {"anssi": cf1, "cis": cf2}.get(cid),
            ):
                index = discovery.get_control_rule_index()

        assert index.total_controls == 2
        assert index.total_requirements == 3
        assert index.total_mapped_rules == 3  # rule_a, rule_b, rule_c

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_exclude_unmapped(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req1 = _make_requirement("R1", rules=["rule_a"])
        req2 = _make_requirement("R2")  # unmapped

        cf = _make_control_file("test", controls=[req1, req2])

        with patch.object(discovery, "list_controls", return_value=["test"]):
            with patch.object(discovery, "get_control_details", return_value=cf):
                index = discovery.get_control_rule_index(include_unmapped=False)

        assert index.total_requirements == 1
        assert index.requirements[0].requirement_id == "R1"

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_filter_by_control_ids(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req1 = _make_requirement("R1", rules=["rule_a"])
        cf1 = _make_control_file("anssi", controls=[req1])

        with patch.object(
            discovery,
            "get_control_details",
            side_effect=lambda cid: cf1 if cid == "anssi" else None,
        ):
            index = discovery.get_control_rule_index(control_ids=["anssi"])

        assert index.total_controls == 1
        assert index.total_requirements == 1

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_nonexistent_control_ids(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        with patch.object(discovery, "get_control_details", return_value=None):
            index = discovery.get_control_rule_index(control_ids=["nonexistent"])

        assert index.total_controls == 0
        assert index.total_requirements == 0
        assert index.requirements == []

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_unique_rule_counting(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        # Same rule_a appears in both frameworks
        req1 = _make_requirement("R1", rules=["rule_a", "rule_b"])
        req2 = _make_requirement("R2", rules=["rule_a", "rule_c"])

        cf1 = _make_control_file("anssi", controls=[req1])
        cf2 = _make_control_file("cis", controls=[req2])

        with patch.object(discovery, "list_controls", return_value=["anssi", "cis"]):
            with patch.object(
                discovery,
                "get_control_details",
                side_effect=lambda cid: {"anssi": cf1, "cis": cf2}.get(cid),
            ):
                index = discovery.get_control_rule_index()

        assert index.total_mapped_rules == 3  # rule_a, rule_b, rule_c (deduplicated)

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_description_truncation(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        long_desc = "x" * 500
        req = _make_requirement("R1", description=long_desc)
        cf = _make_control_file("test", controls=[req])

        with patch.object(discovery, "list_controls", return_value=["test"]):
            with patch.object(discovery, "get_control_details", return_value=cf):
                index = discovery.get_control_rule_index()

        assert len(index.requirements[0].description) == 300
