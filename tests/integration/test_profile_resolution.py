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


@requires_content_repo
class TestProfileFilterRulesWithRealContent:
    def test_openshift_platform_and_node_profiles_split_rules(self, real_content_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        discovery = RuleDiscovery()
        platform_rule = discovery.get_rule_product_availability("api_server_audit_log_maxsize")
        node_rule = discovery.get_rule_product_availability("file_owner_ovs_conf_db")

        assert platform_rule is not None and node_rule is not None
        # ocp4's CIS profiles select both rules through cis_ocp_200:all, and their
        # filter_rules keep platform rules in cis and node rules in cis-node
        assert "cis" in platform_rule.products_in_profiles["ocp4"]
        assert "cis-node" not in platform_rule.products_in_profiles["ocp4"]
        assert "cis-node" in node_rule.products_in_profiles["ocp4"]
        assert "cis" not in node_rule.products_in_profiles["ocp4"]

    def test_filter_matches_the_build_for_openshift_cis(self, real_content_repo):
        import ssg.build_cpe
        import ssg.build_yaml
        import ssg.products
        from ssg.entities.profile_base import rule_filter_from_def

        from content_agent.core.discovery.profile_resolution import ProfileRuleResolver
        from content_agent.core.discovery.profiles import ProfileDiscovery
        from content_agent.core.discovery.rules import RuleDiscovery
        from content_agent.core.integration.product_variables import load_product_variables

        repo = real_content_repo.path
        rules = RuleDiscovery()
        rules._build_rule_index()
        assert rules._rule_cache is not None
        env = load_product_variables(ssg.products, repo, "ocp4")
        cpes = ssg.build_cpe.ProductCPEs()
        cpes.load_product_cpes(env)
        cpes.load_content_cpes(env)

        def build_filter(product, rule_id, expression):
            rule = ssg.build_yaml.Rule.from_yaml(str(rules._rule_cache[rule_id]), env, cpes)
            return bool(rule_filter_from_def(expression)(rule))

        profiles = ProfileDiscovery()
        ours = ProfileRuleResolver(profiles, rule_filter=rules._profile_rule_filter())
        theirs = ProfileRuleResolver(profiles, rule_filter=build_filter)

        for profile_id in ("cis-2-0", "cis-node-2-0"):
            assert ours.resolve_profile("ocp4", profile_id) == theirs.resolve_profile(
                "ocp4", profile_id
            )


@requires_content_repo
class TestProductRuleSetsWithRealContent:
    def test_profiles_only_count_rules_their_product_loads(self, real_content_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        # ocp4 control files list Linux audit rules, but ocp4 reads its rules from
        # applications/, so the build drops them from ocp4's profiles
        availability = RuleDiscovery().get_rule_product_availability("audit_access_failed")

        assert availability is not None
        assert "ocp4" not in availability.products_in_profiles
        assert "rhel9" in availability.products_in_profiles
