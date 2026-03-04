"""Tests for get_control_stats functionality."""

from unittest.mock import patch

from content_agent.models.control import (
    ControlFile,
    ControlRequirement,
    ControlStats,
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


class TestControlStatsModel:
    """Test ControlStats Pydantic model."""

    def test_basic_creation(self):
        stats = ControlStats(
            control_id="test",
            title="Test Control",
            total=5,
            by_status={"automated": 3, "pending": 2},
            mapped=3,
            unmapped=2,
        )
        assert stats.control_id == "test"
        assert stats.total == 5
        assert stats.by_status == {"automated": 3, "pending": 2}
        assert stats.mapped == 3
        assert stats.unmapped == 2

    def test_empty_stats(self):
        stats = ControlStats(
            control_id="empty",
            title="Empty",
            total=0,
            by_status={},
            mapped=0,
            unmapped=0,
        )
        assert stats.total == 0
        assert stats.by_status == {}


class TestGetControlStats:
    """Test ControlDiscovery.get_control_stats()."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_basic_stats(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req1 = _make_requirement("R1", rules=["rule_a"], status="automated")
        req2 = _make_requirement("R2", status="pending")
        req3 = _make_requirement("R3", rules=["rule_b"], status="automated")

        cf = _make_control_file("test", title="Test Policy", controls=[req1, req2, req3])

        with patch.object(discovery, "get_control_details", return_value=cf):
            stats = discovery.get_control_stats("test")

        assert stats is not None
        assert stats.control_id == "test"
        assert stats.title == "Test Policy"
        assert stats.total == 3
        assert stats.by_status == {"automated": 2, "pending": 1}
        assert stats.mapped == 2
        assert stats.unmapped == 1

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_nonexistent_control(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        with patch.object(discovery, "get_control_details", return_value=None):
            stats = discovery.get_control_stats("nonexistent")

        assert stats is None

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_empty_control(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        cf = _make_control_file("empty", controls=[])

        with patch.object(discovery, "get_control_details", return_value=cf):
            stats = discovery.get_control_stats("empty")

        assert stats is not None
        assert stats.total == 0
        assert stats.mapped == 0
        assert stats.unmapped == 0
        assert stats.by_status == {}

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_all_mapped(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        reqs = [
            _make_requirement("R1", rules=["rule_a"], status="automated"),
            _make_requirement("R2", rules=["rule_b"], status="automated"),
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            stats = discovery.get_control_stats("test")

        assert stats is not None
        assert stats.mapped == stats.total
        assert stats.unmapped == 0

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_all_unmapped(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        reqs = [
            _make_requirement("R1", status="pending"),
            _make_requirement("R2", status="pending"),
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            stats = discovery.get_control_stats("test")

        assert stats is not None
        assert stats.unmapped == stats.total
        assert stats.mapped == 0

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_mapped_unmapped_invariant(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        reqs = [
            _make_requirement("R1", rules=["rule_a"], status="automated"),
            _make_requirement("R2", status="pending"),
            _make_requirement("R3", rules=["rule_c"], status="manual"),
            _make_requirement("R4", status="pending"),
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            stats = discovery.get_control_stats("test")

        assert stats is not None
        assert stats.mapped + stats.unmapped == stats.total

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_all_model_statuses(self, mock_repo):
        """Test counting across all statuses accepted by ControlRequirement model."""
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        # These are the statuses currently accepted by ControlRequirement's Literal type.
        # The upstream control.json schema defines 10 canonical statuses; the model
        # constrains to this subset.
        model_statuses = [
            "automated",
            "partially_automated",
            "manual",
            "not_applicable",
            "pending",
        ]

        reqs = [
            _make_requirement(f"R{i}", status=status) for i, status in enumerate(model_statuses, 1)
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            stats = discovery.get_control_stats("test")

        assert stats is not None
        assert stats.total == 5
        assert len(stats.by_status) == 5
        for status in model_statuses:
            assert stats.by_status[status] == 1

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_mixed_statuses_with_duplicates(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        reqs = [
            _make_requirement("R1", status="automated"),
            _make_requirement("R2", status="automated"),
            _make_requirement("R3", status="manual"),
            _make_requirement("R4", status="not_applicable"),
            _make_requirement("R5", status="automated"),
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "get_control_details", return_value=cf):
            stats = discovery.get_control_stats("test")

        assert stats is not None
        assert stats.by_status == {"automated": 3, "manual": 1, "not_applicable": 1}
        assert stats.total == 5
        assert sum(stats.by_status.values()) == stats.total
