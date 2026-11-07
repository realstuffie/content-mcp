"""Integration tests for control files that keep requirements in a subdirectory."""

from tests.conftest import requires_content_repo


@requires_content_repo
class TestRequirementFilesWithRealContent:
    def test_srg_gpos_requirements_load(self, real_content_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        control = ControlDiscovery().get_control_details("srg_gpos")

        assert control is not None
        assert control.parse_errors == []
        assert len(control.controls) > 200
        assert not [c for c in control.controls if "{{{" in c.title]

    def test_nist_800_53_family_files_load(self, real_content_repo):
        from content_agent.core.discovery.controls import ControlDiscovery
        from content_agent.models.control import flatten_requirements

        # nist_800_53 is defined per product
        control = ControlDiscovery().get_control_details("nist_800_53", product="rhel9")

        assert control is not None
        assert control.parse_errors == []
        ids = {req.id for req in flatten_requirements(control.controls)}
        assert {"ac-2", "au-2"} <= ids


@requires_content_repo
class TestImplicitRequirementDirectories:
    """Policies whose requirements live in controls/<id>/ without a controls_dir key."""

    def test_requirement_counts_match_the_build(self, real_content_repo):
        import ssg.controls
        import ssg.products

        from content_agent.core.discovery.controls import ControlDiscovery
        from content_agent.core.integration.product_variables import load_product_variables
        from content_agent.models.control import flatten_requirements

        repo = real_content_repo.path
        for policy, product in [("cis_ocp", "ocp4"), ("srg_ctr", "rhel9"), ("base_sle16", "sle16")]:
            env = load_product_variables(ssg.products, repo, product)
            manager = ssg.controls.ControlsManager(
                [str(repo / "controls"), str(repo / "products" / product / "controls")], env
            )
            manager.load()
            control = ControlDiscovery().get_control_details(policy, product)

            assert control is not None, policy
            expected = len(manager.get_all_controls(policy))
            assert len(flatten_requirements(control.controls)) == expected, policy

    def test_ocp4_cis_profile_selects_its_rules(self, real_content_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        availability = RuleDiscovery().get_rule_product_availability("api_server_audit_log_maxsize")

        assert availability is not None
        # ocp4's CIS profiles select rules only through cis_ocp_200:all and similar
        assert "cis" in availability.products_in_profiles.get("ocp4", [])


@requires_content_repo
class TestRequirementFileLookup:
    def test_nist_requirement_in_family_file(self, real_content_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        result = ControlDiscovery().get_requirement_file_path(
            "nist_800_53", "ac-2.1", product="rhel9"
        )

        assert result is not None
        assert result.exists is True
        assert result.file_path.name == "ac.yml"


@requires_content_repo
class TestPoliciesWithoutAProduct:
    def test_nist_needs_a_product(self, real_content_repo):
        import pytest

        from content_agent.core.discovery.controls import AmbiguousControlError, ControlDiscovery

        with pytest.raises(AmbiguousControlError, match="rhel8"):
            ControlDiscovery().get_control_details("nist_800_53")

    def test_rule_index_has_every_nist_version(self, real_content_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        index = ControlDiscovery().get_control_rule_index(control_ids=["nist_800_53"])

        assert {r.product for r in index.requirements} == {"fedora", "rhel8", "rhel9", "rhel10"}
