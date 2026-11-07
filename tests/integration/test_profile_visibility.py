"""Compare profile visibility with ComplianceAsCode's profile loader."""

import pytest

from content_agent.core.discovery.products import ProductDiscovery
from content_agent.core.discovery.profiles import ProfileDiscovery
from content_agent.core.discovery.rules import RuleDiscovery
from tests.conftest import requires_content_repo


@requires_content_repo
@pytest.mark.parametrize("value", ["true", "false", '"false"', "yes", "null", "''", "0", "1"])
def test_hidden_flag_matches_ssg_profile(real_content_repo, tmp_path, value):
    from ssg.entities.profile_base import Profile

    path = tmp_path / "test.profile"
    content = (
        f"title: Test\ndescription: Test profile\nhidden: {value}\nselections:\n  - test_rule\n"
    )
    path.write_text(content)
    built = Profile.from_yaml(str(path))
    parsed = ProfileDiscovery()._parse_profile(content)
    assert parsed["hidden"] is bool(built.hidden)


@requires_content_repo
def test_ubuntu_default_is_hidden_but_rules_still_searchable(real_content_repo):
    profiles = ProfileDiscovery()
    visible = profiles.list_profiles("ubuntu2404").items
    all_profiles = profiles.list_profiles("ubuntu2404", include_hidden=True).items
    assert len(visible) == 5
    assert len(all_profiles) == 6
    assert "default" not in [p.profile_id for p in visible]
    assert [p.profile_id for p in all_profiles if p.hidden] == ["default"]
    details = ProductDiscovery().get_product_details("ubuntu2404")
    assert details is not None
    assert details.profiles == [p.profile_id for p in visible]
    rules = RuleDiscovery()
    available = rules.get_rule_product_availability("sshd_set_idle_timeout")
    assert available is not None
    assert all("default" not in names for names in available.products_in_profiles.values())
    # Hidden defaults keep otherwise unselected rules in the XCCDF benchmark.
    found = rules.search_rules(product="ubuntu2204", limit=10000)
    assert len(found.items) == 639
    assert not found.errors
