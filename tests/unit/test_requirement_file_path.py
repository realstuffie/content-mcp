"""Tests for get_requirement_file_path functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from content_agent.models.control import RequirementFilePath


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f)


def _mock_product_ids(known_products: list[str]):
    """Stand in for product_ids(), which lists the products directory."""
    return MagicMock(return_value=sorted(known_products))


class TestRequirementFilePathModel:
    """Test RequirementFilePath Pydantic model."""

    def test_basic_creation(self):
        result = RequirementFilePath(
            control_id="anssi",
            requirement_id="R1",
            file_path=Path("/tmp/controls/anssi.yml"),
            format="inline",
            exists=True,
        )
        assert result.control_id == "anssi"
        assert result.format == "inline"
        assert result.exists is True

    def test_json_serialization(self):
        result = RequirementFilePath(
            control_id="test",
            requirement_id="R1",
            file_path=Path("/tmp/controls/test.yml"),
            format="directory",
            exists=False,
        )
        dumped = result.model_dump(mode="json")
        assert isinstance(dumped["file_path"], str)
        assert dumped["format"] == "directory"


class TestGetRequirementFilePath:
    """Test ControlDiscovery.get_requirement_file_path()."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_inline_format_found(self, mock_get_repo, tmp_path):
        mock_repo = MagicMock()
        mock_repo.path = tmp_path
        mock_get_repo.return_value = mock_repo

        controls_dir = tmp_path / "controls"
        _write_yaml(
            controls_dir / "anssi.yml",
            {
                "id": "anssi",
                "title": "ANSSI",
                "controls": [
                    {"id": "R1", "title": "First requirement", "description": "Desc"},
                    {"id": "R2", "title": "Second requirement", "description": "Desc"},
                ],
            },
        )

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            discovery = ControlDiscovery()
            result = discovery.get_requirement_file_path("anssi", "R1")

        assert result is not None
        assert result.format == "inline"
        assert result.exists is True
        assert result.file_path == (controls_dir / "anssi.yml").resolve()
        assert result.control_id == "anssi"
        assert result.requirement_id == "R1"

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_directory_format_found(self, mock_get_repo, tmp_path):
        mock_repo = MagicMock()
        mock_repo.path = tmp_path
        mock_get_repo.return_value = mock_repo

        controls_dir = tmp_path / "controls"
        _write_yaml(
            controls_dir / "srg_gpos.yml",
            {
                "id": "srg_gpos",
                "title": "SRG GPOS",
                "controls_dir": "srg_gpos",
            },
        )
        _write_yaml(
            controls_dir / "srg_gpos" / "SRG-OS-000001.yml",
            {"id": "SRG-OS-000001", "title": "First SRG", "description": "Desc"},
        )

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            discovery = ControlDiscovery()
            result = discovery.get_requirement_file_path("srg_gpos", "SRG-OS-000001")

        assert result is not None
        assert result.format == "directory"
        assert result.exists is True
        assert result.file_path == (controls_dir / "srg_gpos" / "SRG-OS-000001.yml").resolve()

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_directory_format_missing_file(self, mock_get_repo, tmp_path):
        mock_repo = MagicMock()
        mock_repo.path = tmp_path
        mock_get_repo.return_value = mock_repo

        controls_dir = tmp_path / "controls"
        _write_yaml(
            controls_dir / "srg_gpos.yml",
            {
                "id": "srg_gpos",
                "title": "SRG GPOS",
                "controls_dir": "srg_gpos",
            },
        )

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            discovery = ControlDiscovery()
            result = discovery.get_requirement_file_path("srg_gpos", "SRG-OS-999999")

        assert result is not None
        assert result.format == "directory"
        assert result.exists is False

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_nonexistent_control(self, mock_get_repo, tmp_path):
        mock_repo = MagicMock()
        mock_repo.path = tmp_path
        mock_get_repo.return_value = mock_repo

        (tmp_path / "controls").mkdir(parents=True)

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            discovery = ControlDiscovery()
            result = discovery.get_requirement_file_path("nonexistent", "R1")

        assert result is None

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_nonexistent_requirement_inline(self, mock_get_repo, tmp_path):
        mock_repo = MagicMock()
        mock_repo.path = tmp_path
        mock_get_repo.return_value = mock_repo

        controls_dir = tmp_path / "controls"
        _write_yaml(
            controls_dir / "anssi.yml",
            {
                "id": "anssi",
                "title": "ANSSI",
                "controls": [
                    {"id": "R1", "title": "First", "description": "Desc"},
                ],
            },
        )

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            discovery = ControlDiscovery()
            result = discovery.get_requirement_file_path("anssi", "NONEXISTENT")

        assert result is None

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_path_is_absolute(self, mock_get_repo, tmp_path):
        mock_repo = MagicMock()
        mock_repo.path = tmp_path
        mock_get_repo.return_value = mock_repo

        controls_dir = tmp_path / "controls"
        _write_yaml(
            controls_dir / "test.yml",
            {
                "id": "test",
                "title": "Test",
                "controls": [
                    {"id": "R1", "title": "First", "description": "Desc"},
                ],
            },
        )

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            discovery = ControlDiscovery()
            result = discovery.get_requirement_file_path("test", "R1")

        assert result is not None
        assert result.file_path.is_absolute()


class TestRequirementsInSharedFiles:
    """Requirements in files that hold several, or in the policy's own file."""

    def _lookup(self, tmp_path, control_id, requirement_id):
        from content_agent.core.discovery.controls import ControlDiscovery

        with (
            patch("content_agent.core.discovery.controls.get_content_repository") as get_repo,
            patch(
                "content_agent.core.discovery.controls.get_ssg_modules",
                side_effect=RuntimeError("SSG modules not initialized"),
            ),
            patch(
                "content_agent.core.discovery.controls.product_ids",
                _mock_product_ids([]),
            ),
        ):
            get_repo.return_value.path = tmp_path
            return ControlDiscovery().get_requirement_file_path(control_id, requirement_id)

    def test_family_file(self, tmp_path):
        # NIST 800-53 keeps a family per file: ac-2 is in ac.yml
        controls_dir = tmp_path / "controls"
        _write_yaml(
            controls_dir / "nist.yml", {"id": "nist", "title": "NIST", "controls_dir": "nist"}
        )
        (controls_dir / "nist").mkdir()
        (controls_dir / "nist" / "ac.yml").write_text(
            "controls:\n    - id: ac-1\n      title: First\n    - id: ac-2\n      title: Second\n"
        )
        (controls_dir / "nist" / "au.yml").write_text(
            "controls:\n    - id: au-2\n      title: Audit\n"
        )

        result = self._lookup(tmp_path, "nist", "ac-2")

        assert result is not None
        assert result.format == "directory"
        assert result.exists is True
        assert result.file_path == (controls_dir / "nist" / "ac.yml").resolve()

    def test_requirement_in_policy_file_of_directory_policy(self, tmp_path):
        # srg_gpos keeps its Variables requirement in srg_gpos.yml itself
        controls_dir = tmp_path / "controls"
        (controls_dir / "srg").mkdir(parents=True)
        (controls_dir / "srg.yml").write_text(
            "id: srg\ntitle: SRG\ncontrols_dir: srg\ncontrols:\n    - id: Variables\n"
            "      title: Variables\n"
        )
        (controls_dir / "srg" / "SRG-1.yml").write_text("controls:\n    - id: SRG-1\n")

        result = self._lookup(tmp_path, "srg", "Variables")

        assert result is not None
        assert result.format == "inline"
        assert result.file_path == (controls_dir / "srg.yml").resolve()

    def test_directory_named_after_policy_file(self, tmp_path):
        # cis_ocp sets no controls_dir; its requirements are in controls/cis_ocp/
        controls_dir = tmp_path / "controls"
        _write_yaml(controls_dir / "cis.yml", {"id": "cis", "title": "CIS"})
        (controls_dir / "cis").mkdir()
        (controls_dir / "cis" / "section-1.yml").write_text(
            "controls:\n    - id: '1'\n      controls:\n          - id: '1.1'\n"
        )

        result = self._lookup(tmp_path, "cis", "1.1")

        assert result is not None
        assert result.format == "directory"
        assert result.file_path == (controls_dir / "cis" / "section-1.yml").resolve()
