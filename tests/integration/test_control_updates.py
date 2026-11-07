"""Integration tests for update_requirement_rules on copies of real control files.

Each test copies control files into a temporary repository, updates a
requirement, and loads the result with ComplianceAsCode's own ControlsManager.
"""

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.conftest import requires_content_repo


def _copy_controls(real_repo: Path, tmp_path: Path, names: list[str]) -> Path:
    controls = tmp_path / "controls"
    controls.mkdir()
    for name in names:
        source = real_repo / "controls" / name
        if source.is_dir():
            shutil.copytree(source, controls / name)
        else:
            shutil.copy2(source, controls / name)
    return controls


def _cac_controls(real_repo: Path, controls: Path, policy_id: str, product: str) -> dict:
    """Load a policy the way the ComplianceAsCode build does."""
    import ssg.controls
    import ssg.products

    from content_agent.core.integration.product_variables import load_product_variables

    env = load_product_variables(ssg.products, real_repo, product)
    manager = ssg.controls.ControlsManager([str(controls)], env)
    manager.load()
    return manager.get_all_controls_dict(policy_id)


@pytest.fixture
def updater_for(real_content_repo):
    """Make a ControlUpdater that writes to a temporary repository."""
    from content_agent.core.scaffolding.control_updater import ControlUpdater

    def make(tmp_path: Path) -> ControlUpdater:
        updater = ControlUpdater()
        updater.content_repo = SimpleNamespace(path=tmp_path)
        return updater

    return make


@requires_content_repo
class TestControlUpdatesWithRealContent:
    def test_srg_requirement_file_stays_loadable(self, real_content_repo, updater_for, tmp_path):
        # srg_gpos requirement files use `-   id:`, which the updater used to break
        controls = _copy_controls(real_content_repo.path, tmp_path, ["srg_gpos.yml", "srg_gpos"])
        before = _cac_controls(real_content_repo.path, controls, "srg_gpos", "ubuntu2204")

        result = updater_for(tmp_path).update_requirement_rules(
            "srg_gpos", "SRG-OS-000001-GPOS-00001", ["sshd_disable_root_login"], "automated"
        )

        assert result.success, result.errors
        after = _cac_controls(real_content_repo.path, controls, "srg_gpos", "ubuntu2204")
        assert len(after) == len(before)
        updated = after["SRG-OS-000001-GPOS-00001"]
        assert updated.rules == ["sshd_disable_root_login"]
        assert updated.status == "automated"

    def test_parent_update_leaves_nested_requirements(
        self, real_content_repo, updater_for, tmp_path
    ):
        controls = _copy_controls(real_content_repo.path, tmp_path, ["pcidss_4.yml"])
        before = _cac_controls(real_content_repo.path, controls, "pcidss_4", "rhel9")
        children = [c for c in before if c.startswith("1.2.")]
        assert children

        result = updater_for(tmp_path).update_requirement_rules(
            "pcidss_4", "1.2", ["sweep_parent_rule"], "manual"
        )

        assert result.success, result.errors
        after = _cac_controls(real_content_repo.path, controls, "pcidss_4", "rhel9")
        assert len(after) == len(before)
        assert after["1.2"].rules == ["sweep_parent_rule"]
        assert after["1.2"].status == "manual"
        for child in children:
            assert after[child].rules == before[child].rules
            assert after[child].status == before[child].status

    def test_rules_with_jinja_conditionals_refused(self, real_content_repo, updater_for, tmp_path):
        controls = _copy_controls(real_content_repo.path, tmp_path, ["srg_gpos.yml", "srg_gpos"])
        requirement_file = controls / "srg_gpos" / "SRG-OS-000366-GPOS-00153.yml"
        original = requirement_file.read_text()
        assert "{{% if" in original

        result = updater_for(tmp_path).update_requirement_rules(
            "srg_gpos", "SRG-OS-000366-GPOS-00153", ["sweep_rule"], "automated"
        )

        assert not result.success
        assert "Jinja2 conditionals" in result.errors[0]
        assert requirement_file.read_text() == original
