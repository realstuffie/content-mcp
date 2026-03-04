"""Tests for list_unmapped_requirements functionality."""

from unittest.mock import patch

from content_agent.models.control import (
    ControlFile,
    ControlRequirement,
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


class TestListUnmappedRequirements:
    """Test ControlDiscovery.list_unmapped_requirements()."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_returns_pending_by_default(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        reqs = [
            _make_requirement("R1", status="pending"),
            _make_requirement("R2", status="automated", rules=["rule_a"]),
            _make_requirement("R3", status="pending"),
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            results = discovery.list_unmapped_requirements("test")

        assert results is not None
        assert len(results) == 2
        assert {r.requirement_id for r in results} == {"R1", "R3"}

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_empty_rules_included(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        reqs = [
            _make_requirement("R1", status="automated", rules=["rule_a"]),
            _make_requirement("R2", status="automated", rules=[]),
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            results = discovery.list_unmapped_requirements("test")

        assert results is not None
        assert len(results) == 1
        assert results[0].requirement_id == "R2"

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_custom_status_filter(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        reqs = [
            _make_requirement("R1", status="pending"),
            _make_requirement("R2", status="manual"),
            _make_requirement("R3", status="automated", rules=["rule_a"]),
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            results = discovery.list_unmapped_requirements(
                "test", status_filter=["manual", "pending"]
            )

        assert results is not None
        assert len(results) == 2
        assert {r.requirement_id for r in results} == {"R1", "R2"}

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_nonexistent_control(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        with patch.object(discovery, "get_control_details", return_value=None):
            results = discovery.list_unmapped_requirements("nonexistent")

        assert results is None

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_all_mapped(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        reqs = [
            _make_requirement("R1", status="automated", rules=["rule_a"]),
            _make_requirement("R2", status="automated", rules=["rule_b"]),
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            results = discovery.list_unmapped_requirements("test")

        assert results is not None
        assert len(results) == 0

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_description_truncation(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        long_desc = "A" * 500
        reqs = [_make_requirement("R1", description=long_desc, status="pending")]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            results = discovery.list_unmapped_requirements("test")

        assert results is not None
        assert len(results) == 1
        assert len(results[0].description) == 300
