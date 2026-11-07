"""Tests for rule product availability functionality."""

import json
from unittest.mock import MagicMock, patch

from content_agent.models.rule import RuleDetails, RuleProductAvailability


class TestRuleProductAvailabilityModel:
    """Test RuleProductAvailability Pydantic model."""

    def test_basic_creation(self):
        avail = RuleProductAvailability(
            rule_id="sshd_disable_root_login",
            products_with_identifiers=["rhel8", "rhel9"],
            products_in_profiles={"rhel8": ["cis", "stig"], "rhel9": ["cis"]},
            platforms=["machine"],
            template={"name": "sshd_lineinfile", "vars": {}},
            has_build_artifacts={"rhel8": True, "rhel9": False},
        )
        assert avail.rule_id == "sshd_disable_root_login"
        assert len(avail.products_with_identifiers) == 2
        assert avail.products_in_profiles["rhel8"] == ["cis", "stig"]

    def test_defaults(self):
        avail = RuleProductAvailability(rule_id="test_rule")
        assert avail.products_with_identifiers == []
        assert avail.products_in_profiles == {}
        assert avail.platforms == []
        assert avail.template is None
        assert avail.has_build_artifacts == {}


class TestGetRuleProductAvailability:
    """Test RuleDiscovery.get_rule_product_availability()."""

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_rule_not_found(self, mock_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        discovery = RuleDiscovery()

        with patch.object(discovery, "get_rule_details", return_value=None):
            result = discovery.get_rule_product_availability("nonexistent")

        assert result is None

    def test_build_flags_require_rule_json_in_checked_products(self, initialized_content_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        root = initialized_content_repo.path
        for product in ("rhel8", "rhel9"):
            (root / "build" / product / "rules").mkdir(parents=True)
        oval = root / "build" / "rhel8" / "checks" / "oval"
        oval.mkdir(parents=True)
        (oval / "test_rule.xml").write_text("<def-group/>")
        remediation = root / "build" / "rhel8" / "fixes_from_templates" / "bash"
        remediation.mkdir(parents=True)
        (remediation / "test_rule.sh").write_text("#!/bin/bash\ntrue\n")
        (root / "build" / "rhel9" / "rules" / "test_rule.json").write_text(
            json.dumps({"title": "Test rule"})
        )
        discovery = RuleDiscovery()
        discovery._profile_rule_index = {}
        rule = RuleDetails(
            rule_id="test_rule",
            title="Test rule",
            description="Test",
            severity="medium",
            products=["rhel8", "rhel9", "rhel10"],
            file_path="test/rule.yml",
            rule_dir="test",
        )
        with patch.object(discovery, "get_rule_details", return_value=rule):
            availability = discovery.get_rule_product_availability("test_rule")

        assert availability is not None
        assert availability.has_build_artifacts == {"rhel8": False, "rhel9": True}

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_basic_availability(self, mock_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        discovery = RuleDiscovery()

        mock_rule = RuleDetails(
            rule_id="sshd_disable_root_login",
            title="Disable Root Login via SSH",
            description="Test",
            severity="high",
            products=["rhel8", "rhel9"],
            platforms=["machine"],
            template={"name": "sshd_lineinfile"},
            file_path="test/rule.yml",
            rule_dir="test",
        )

        with patch.object(discovery, "get_rule_details", return_value=mock_rule):
            # Mock profile scanning
            discovery._profile_rule_index = {
                "sshd_disable_root_login": [("rhel8", "cis"), ("rhel8", "stig"), ("rhel9", "cis")]
            }
            # Mock build artifacts (imported inside the method)
            with (
                patch(
                    "content_agent.core.discovery.build_artifacts.list_built_products",
                    return_value=["rhel8"],
                ),
                patch(
                    "content_agent.core.discovery.build_artifacts.get_rendered_rule",
                    return_value=MagicMock(),
                ),
            ):
                result = discovery.get_rule_product_availability("sshd_disable_root_login")

        assert result is not None
        assert result.rule_id == "sshd_disable_root_login"
        assert "rhel8" in result.products_with_identifiers
        assert "rhel9" in result.products_with_identifiers
        assert result.products_in_profiles["rhel8"] == ["cis", "stig"]
        assert result.products_in_profiles["rhel9"] == ["cis"]
        assert result.platforms == ["machine"]
        assert result.template == {"name": "sshd_lineinfile"}

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_control_references_not_matched(self, mock_repo):
        """Control references like 'anssi:all:minimal' should not match as rule IDs."""
        from content_agent.core.discovery.rules import RuleDiscovery
        from content_agent.models.profile import ProfileDetails, ProfileSummary

        discovery = RuleDiscovery()
        discovery._profile_rule_index = None  # Force rebuild

        mock_profile_summary = ProfileSummary(
            profile_id="test_profile",
            title="Test",
            description="Test profile",
            product="rhel9",
            rule_count=2,
        )

        mock_profile_details = ProfileDetails(
            profile_id="test_profile",
            title="Test",
            description="Test profile",
            product="rhel9",
            selections=["anssi:all:minimal", "real_rule_id", "!unselect_this"],
            variables={},
            file_path="test.profile",
            rule_count=2,
        )

        with patch(
            "content_agent.core.discovery.profiles.ProfileDiscovery"
        ) as MockProfileDiscovery:
            mock_pd = MockProfileDiscovery.return_value
            from content_agent.models.common import DiscoveryResult

            mock_pd.list_profiles.return_value = DiscoveryResult(items=[mock_profile_summary])
            mock_pd.get_profile_details.return_value = mock_profile_details

            discovery._build_profile_rule_index()

        # Control reference should NOT be in the index
        assert "anssi:all:minimal" not in discovery._profile_rule_index
        # Direct rule ID should be in the index
        assert "real_rule_id" in discovery._profile_rule_index
        # Unselection should NOT be in the index
        assert "!unselect_this" not in discovery._profile_rule_index

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_cache_reuse(self, mock_repo):
        """Second call should reuse cached index."""
        from content_agent.core.discovery.rules import RuleDiscovery

        discovery = RuleDiscovery()

        # Pre-populate cache
        discovery._profile_rule_index = {"test_rule": [("rhel9", "cis")]}

        mock_rule = RuleDetails(
            rule_id="test_rule",
            title="Test",
            description="Test",
            severity="medium",
            products=["rhel9"],
            platforms=[],
            file_path="test/rule.yml",
            rule_dir="test",
        )

        with patch.object(discovery, "get_rule_details", return_value=mock_rule):
            with patch(
                "content_agent.core.discovery.build_artifacts.list_built_products",
                return_value=[],
            ):
                # First call
                result1 = discovery.get_rule_product_availability("test_rule")
                # Second call should use same cache
                result2 = discovery.get_rule_product_availability("test_rule")

        assert result1 is not None
        assert result2 is not None
        assert result1.products_in_profiles == result2.products_in_profiles
