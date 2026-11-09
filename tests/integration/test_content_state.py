"""Integration tests for the files cached results are checked against."""

import os
from pathlib import Path

from tests.conftest import requires_content_repo


def _norm(path: Path | str) -> Path:
    return Path(os.path.normpath(path))


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
        ):
            assert _norm(expected) in watched
        assert any(path.parent.name == "product_properties" for path in watched)
