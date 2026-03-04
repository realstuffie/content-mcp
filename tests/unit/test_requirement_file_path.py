"""Tests for get_requirement_file_path functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from content_agent.models.control import RequirementFilePath


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f)


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

        discovery = ControlDiscovery()
        result = discovery.get_requirement_file_path("test", "R1")

        assert result is not None
        assert result.file_path.is_absolute()
