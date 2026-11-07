"""Hidden profiles contribute benchmark rules without becoming scan profiles."""

import json
import os
from datetime import timedelta
from pathlib import Path

import pytest
import yaml
from mcp.shared.memory import create_connected_server_and_client_session

from content_agent.core.discovery.products import ProductDiscovery
from content_agent.core.discovery.profiles import ProfileDiscovery
from content_agent.core.discovery.rules import RuleDiscovery
from content_agent.core.integration import get_ssg_modules
from content_agent.server.mcp_server import ContentAgentServer


@pytest.fixture
def profiles_repo(initialized_content_repo):
    root = initialized_content_repo.path
    profiles = root / "products" / "rhel9" / "profiles"
    definitions = {
        "default": "hidden: true\nselections:\n  - hidden_only_rule\n",
        "internal": "hidden: true\nselections:\n  - base_rule\n",
        "cis": "extends: internal\nselections:\n  - selected_rule\n",
        "standard": "selections:\n  - selected_rule\n",
    }
    for name, selections in definitions.items():
        (profiles / f"{name}.profile").write_text(
            f"title: {name}\ndescription: Test profile\n{selections}"
        )
    for name in ("hidden_only_rule", "base_rule", "selected_rule"):
        rule = root / "linux_os" / "guide" / name / "rule.yml"
        rule.parent.mkdir(parents=True)
        rule.write_text(f"title: {name}\ndescription: Test rule\nseverity: medium\n")
    get_ssg_modules().yaml.open_and_expand.side_effect = lambda path, substitutions: yaml.safe_load(
        Path(path).read_text()
    )
    return root


def test_lists_only_selectable_profiles(profiles_repo):
    profiles = ProfileDiscovery().list_profiles("rhel9").items
    assert [p.profile_id for p in profiles] == ["cis", "standard"]
    assert all(not p.hidden for p in profiles)


def test_hidden_profiles_can_be_listed_explicitly(profiles_repo):
    profiles = ProfileDiscovery().list_profiles("rhel9", include_hidden=True).items
    assert {p.profile_id: p.hidden for p in profiles} == {
        "cis": False,
        "default": True,
        "internal": True,
        "standard": False,
    }


def test_product_profiles_exclude_hidden_entries(profiles_repo):
    details = ProductDiscovery().get_product_details("rhel9")
    assert details is not None
    assert details.profiles == ["cis", "standard"]


def test_hidden_details_remain_available(profiles_repo):
    details = ProfileDiscovery().get_profile_details("default", "rhel9")
    assert details is not None
    assert details.hidden
    assert details.selections == ["hidden_only_rule"]


def test_default_name_does_not_imply_hidden(profiles_repo):
    default = profiles_repo / "products" / "rhel9" / "profiles" / "default.profile"
    default.write_text("title: default\ndescription: Visible\nselections: []\n")
    assert "default" in [p.profile_id for p in ProfileDiscovery().list_profiles("rhel9").items]


def test_hidden_rules_remain_searchable_without_hidden_memberships(profiles_repo):
    discovery = RuleDiscovery()
    availability = discovery.get_rule_product_availability("hidden_only_rule")
    assert availability is not None
    assert availability.products_in_profiles == {}
    found = discovery.search_rules(query="hidden_only_rule", product="rhel9")
    assert [r.rule_id for r in found.items] == ["hidden_only_rule"]
    inherited = discovery.get_rule_product_availability("base_rule")
    assert inherited is not None
    assert inherited.products_in_profiles == {"rhel9": ["cis"]}


def test_shared_index_preserves_hidden_rule_search(profiles_repo):
    first = RuleDiscovery()
    first_index = first._ensure_profile_rule_index()
    second = RuleDiscovery()
    assert second._ensure_profile_rule_index() is first_index
    assert "hidden_only_rule" in second._rules_selected_by_product("rhel9")
    assert "hidden_only_rule" not in first_index


def test_hidden_flag_change_rebuilds_index(profiles_repo):
    first = RuleDiscovery()
    old_index = first._ensure_profile_rule_index()
    default = profiles_repo / "products" / "rhel9" / "profiles" / "default.profile"
    default.write_text(default.read_text().replace("hidden: true\n", ""))
    newest = max(p.stat().st_mtime_ns for p in profiles_repo.rglob("*.profile"))
    stat = default.stat()
    os.utime(default, ns=(stat.st_atime_ns, newest + 1_000_000_000))
    second = RuleDiscovery()
    assert second._ensure_profile_rule_index() is not old_index
    availability = second.get_rule_product_availability("hidden_only_rule")
    assert availability is not None
    assert availability.products_in_profiles == {"rhel9": ["default"]}


@pytest.mark.parametrize(
    "value, hidden",
    [
        ("true", True),
        ("false", True),
        ('"false"', True),
        ("yes", True),
        ("null", False),
        ("''", False),
        ("0", False),
        ("1", True),
    ],
)
def test_hidden_value_matches_build_truthiness(initialized_content_repo, value, hidden):
    # SSG preserves YAML boolean scalars as strings, including the word false.
    assert ProfileDiscovery()._parse_profile(f"hidden: {value}\n")["hidden"] is hidden


@pytest.mark.asyncio
async def test_profile_visibility_through_mcp(profiles_repo):
    server = ContentAgentServer()
    async with create_connected_server_and_client_session(
        server.server, read_timeout_seconds=timedelta(seconds=5)
    ) as client:
        visible = await client.call_tool("list_profiles", {"product": "rhel9"})
        assert not visible.isError
        assert len(json.loads(visible.content[0].text)) == 2
        all_profiles = await client.call_tool(
            "list_profiles", {"product": "rhel9", "include_hidden": True}
        )
        assert not all_profiles.isError
        assert len(json.loads(all_profiles.content[0].text)) == 4
        resource = await client.read_resource("cac://profiles")
        assert len(json.loads(resource.contents[0].text)) == 2
        hidden = await client.read_resource("cac://profiles/rhel9/default")
        assert json.loads(hidden.contents[0].text)["hidden"] is True
