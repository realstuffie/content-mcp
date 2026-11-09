"""Tests for the search_rules product filter and the shared profile index."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

import content_agent.core.discovery.rules as rules_module


def _repo(tmp_path):
    for rule_id, data in {
        "rule_selected": {"title": "Selected", "severity": "high"},
        "rule_identified": {
            "title": "Identified",
            "severity": "low",
            "identifiers": {"cce@ubuntu2204": "CCE-1"},
        },
        "rule_other": {"title": "Other", "severity": "low"},
    }.items():
        rule_dir = tmp_path / "linux_os" / "guide" / rule_id
        rule_dir.mkdir(parents=True)
        (rule_dir / "rule.yml").write_text(yaml.dump(data))
    profiles = tmp_path / "products" / "ubuntu2204" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "cis.profile").write_text("selections:\n    - rule_selected\n")
    return tmp_path


def _discovery(repo_path):
    with patch("content_agent.core.discovery.rules.get_content_repository") as get_repo:
        get_repo.return_value.path = repo_path
        return rules_module.RuleDiscovery()


def _plain_yaml_modules():
    modules = MagicMock()
    modules.yaml.open_and_expand.side_effect = lambda path, subs: yaml.safe_load(
        Path(path).read_text()
    )
    return modules


def test_product_filter_includes_rules_selected_by_profiles(tmp_path):
    repo = _repo(tmp_path)
    discovery = _discovery(repo)
    discovery._profile_rule_index = {"rule_selected": [("ubuntu2204", "cis")]}

    with patch.object(rules_module, "get_ssg_modules", return_value=_plain_yaml_modules()):
        result = discovery.search_rules(product="ubuntu2204", limit=10)

    assert sorted(r.rule_id for r in result.items) == ["rule_identified", "rule_selected"]


def test_profile_index_is_shared_and_rebuilt_when_profiles_change(tmp_path):
    repo = _repo(tmp_path)
    rules_module._shared_profile_indexes.clear()
    builds = []

    def build(self):
        builds.append(1)
        self._profile_rule_index = {"rule_selected": [("ubuntu2204", "cis")]}

    with patch.object(rules_module.RuleDiscovery, "_build_profile_rule_index", build):
        first = _discovery(repo)._ensure_profile_rule_index()
        second = _discovery(repo)._ensure_profile_rule_index()
        assert len(builds) == 1
        assert first is second

        profile = repo / "products" / "ubuntu2204" / "profiles" / "cis.profile"
        stat = profile.stat()
        os.utime(profile, (stat.st_atime + 10, stat.st_mtime + 10))
        _discovery(repo)._ensure_profile_rule_index()
        assert len(builds) == 2

    rules_module._shared_profile_indexes.clear()


def _platform_index(builds):
    """Stand in for the index build: cis keeps the rules without the ocp4-node platform."""

    def build(self):
        builds.append(1)
        self._profile_rule_index = {}
        for rule_yml in sorted((self.content_repo.path / "linux_os").rglob("rule.yml")):
            if yaml.safe_load(rule_yml.read_text()).get("platform") != "ocp4-node":
                self._profile_rule_index[rule_yml.parent.name] = [("ubuntu2204", "cis")]

    return build


def test_profile_index_is_rebuilt_when_a_rule_changes(tmp_path):
    # The profiles stay the same, but filter_rules would now exclude the rule
    repo = _repo(tmp_path)
    rules_module._shared_profile_indexes.clear()
    builds: list[int] = []

    with patch.object(
        rules_module.RuleDiscovery, "_build_profile_rule_index", _platform_index(builds)
    ):
        assert "rule_other" in _discovery(repo)._ensure_profile_rule_index()

        rule_yml = repo / "linux_os" / "guide" / "rule_other" / "rule.yml"
        data = yaml.safe_load(rule_yml.read_text())
        rule_yml.write_text(yaml.dump({**data, "platform": "ocp4-node"}))

        assert "rule_other" not in _discovery(repo)._ensure_profile_rule_index()
        assert len(builds) == 2

    rules_module._shared_profile_indexes.clear()


def test_profile_index_is_rebuilt_when_product_files_change(tmp_path):
    repo = _repo(tmp_path)
    product_yml = repo / "products" / "ubuntu2204" / "product.yml"
    product_yml.write_text("product: ubuntu2204\n")
    properties = repo / "product_properties"
    properties.mkdir()
    (properties / "10-ids.yml").write_text("auid: 1000\n")
    rules_module._shared_profile_indexes.clear()
    builds: list[int] = []

    with patch.object(
        rules_module.RuleDiscovery, "_build_profile_rule_index", _platform_index(builds)
    ):
        _discovery(repo)._ensure_profile_rule_index()
        _discovery(repo)._ensure_profile_rule_index()
        assert len(builds) == 1

        product_yml.write_text("product: ubuntu2204\nfull_name: Ubuntu 22.04\n")
        _discovery(repo)._ensure_profile_rule_index()
        assert len(builds) == 2

        (properties / "10-ids.yml").write_text("auid: 500\nuid_min: 500\n")
        _discovery(repo)._ensure_profile_rule_index()
        assert len(builds) == 3

    rules_module._shared_profile_indexes.clear()
