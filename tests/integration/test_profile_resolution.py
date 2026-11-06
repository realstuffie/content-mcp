"""Integration tests for profile resolution against a real content repository."""

from tests.conftest import requires_content_repo


@requires_content_repo
class TestProfileResolutionWithRealContent:
    def test_rule_selected_through_control_file(self, real_content_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        availability = RuleDiscovery().get_rule_product_availability(
            "accounts_umask_interactive_users"
        )

        assert availability is not None
        # rhel9's STIG profile selects this rule only through stig_rhel9:all
        assert "stig" in availability.products_in_profiles.get("rhel9", [])

    def test_control_references_are_not_indexed_as_rules(self, real_content_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        discovery = RuleDiscovery()
        discovery._build_profile_rule_index()

        assert discovery._profile_rule_index is not None
        assert not [key for key in discovery._profile_rule_index if ":" in key]


@requires_content_repo
class TestSearchRulesProductFilterWithRealContent:
    def test_ubuntu_rules_found_through_profiles(self, real_content_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        result = RuleDiscovery().search_rules(query="sshd", product="ubuntu2204", limit=500)

        # Ubuntu rules rarely have identifiers for the product, so before profile
        # selections counted, this search returned nothing.
        assert "sshd_disable_root_login" in {r.rule_id for r in result.items}
