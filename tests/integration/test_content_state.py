"""Integration tests for the files cached results are checked against."""

import os
from pathlib import Path
from unittest.mock import patch

from tests.conftest import requires_content_repo

HOST_RULE = "title: API rule\nplatform: '{{{ product }}}-host'\n"
NODE_RULE = "title: API rule\nplatform: '{{{ product }}}-node'\n"


def _norm(path: Path | str) -> Path:
    return Path(os.path.normpath(path))


def _rewrite_keeping_mtime(path: Path, text: str) -> None:
    """Rewrite a file with same-size text and put its mtime back, as `cp -p` would."""
    before = path.stat()
    assert len(text) == before.st_size
    path.write_text(text)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))


@requires_content_repo
class TestContentStateWithRealContent:
    def test_profile_index_state_covers_every_rule_the_index_reads(self, real_content_repo):
        from content_agent.core.discovery.rule_paths import product_rule_directories, rule_files
        from content_agent.core.discovery.rules import _profile_index_state

        repo = real_content_repo.path
        state = _profile_index_state(repo)
        assert state is not None

        read = {_norm(path) for path in rule_files(repo)}
        for product_yml in (repo / "products").glob("*/product.yml"):
            for directory in product_rule_directories(repo, product_yml.parent.name) or []:
                read |= {_norm(path) for path in directory.rglob("rule.yml")}
        watched = {
            _norm(entry.path)
            for entry in state.entries
            if entry.kind == "file" and entry.path.endswith(f"{os.sep}rule.yml")
        }

        assert len(read) > 2000
        assert read == watched
        assert state.is_current()

    def test_profile_index_state_watches_products_profiles_and_controls(self, real_content_repo):
        from content_agent.core.discovery.rules import _profile_index_state

        repo = real_content_repo.path
        state = _profile_index_state(repo)
        assert state is not None
        watched = {_norm(entry.path) for entry in state.entries}

        for expected in (
            repo / "products" / "ubuntu2204" / "product.yml",
            repo / "products" / "ubuntu2204" / "profiles" / "cis_level1_server.profile",
            repo / "controls" / "cis_ubuntu2204.yml",
            repo / "controls" / "srg_gpos" / "SRG-OS-000001-GPOS-00001.yml",
            repo / "products" / "rhel9" / "controls" / "nist_800_53" / "ac.yml",
            repo / "shared" / "macros" / "01-general.jinja",
        ):
            assert _norm(expected) in watched
        assert any(path.parent.name == "product_properties" for path in watched)

    def test_rule_rewritten_with_its_old_mtime_expands_to_its_new_contents(
        self, real_content_repo, tmp_path
    ):
        from content_agent.core.discovery.rules import RuleDiscovery

        rule_yml = tmp_path / "api_rule" / "rule.yml"
        rule_yml.parent.mkdir()
        rule_yml.write_text(HOST_RULE)
        first = RuleDiscovery()._load_rule_yaml(rule_yml, "ocp4")["platform"]

        _rewrite_keeping_mtime(rule_yml, NODE_RULE)
        second = RuleDiscovery()._load_rule_yaml(rule_yml, "ocp4")["platform"]

        assert (first, second) == ("ocp4-host", "ocp4-node")

    def test_index_rebuild_expands_a_rule_rewritten_with_its_old_mtime(
        self, real_content_repo, tmp_path
    ):
        import content_agent.core.discovery.rules as rules_module

        rule_yml = tmp_path / "linux_os" / "guide" / "api_rule" / "rule.yml"
        rule_yml.parent.mkdir(parents=True)
        rule_yml.write_text(HOST_RULE)
        platforms = []

        def build(self):
            platforms.append(self._load_rule_yaml(rule_yml, "ocp4")["platform"])
            self._profile_rule_index = {}

        rules_module._shared_profile_indexes.clear()
        with (
            patch.object(rules_module.RuleDiscovery, "_build_profile_rule_index", build),
            patch.object(rules_module, "get_content_repository") as get_repo,
        ):
            get_repo.return_value.path = tmp_path
            rules_module.RuleDiscovery()._ensure_profile_rule_index()
            _rewrite_keeping_mtime(rule_yml, NODE_RULE)
            rules_module.RuleDiscovery()._ensure_profile_rule_index()
        rules_module._shared_profile_indexes.clear()

        assert platforms == ["ocp4-host", "ocp4-node"]
