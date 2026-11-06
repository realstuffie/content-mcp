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

        control = ControlDiscovery().get_control_details("nist_800_53")

        assert control is not None
        assert control.parse_errors == []
        ids = {req.id for req in flatten_requirements(control.controls)}
        assert {"ac-2", "au-2"} <= ids
