"""Tests for nested requirements and control references in control files."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from content_agent.models.control import ControlFile, ControlRequirement, flatten_requirements

NESTED_POLICY = {
    "id": "nested",
    "title": "Nested policy",
    "controls": [
        {
            "id": "1",
            "title": "Section one",
            "rules": ["rule_top"],
            "controls": [
                {
                    "id": "1.1",
                    "title": "Child requirement",
                    "rules": ["rule_child"],
                    "controls": [
                        {
                            "id": "1.1.1",
                            "title": "Grandchild requirement",
                            "rules": ["rule_grandchild"],
                        },
                    ],
                },
                "other_policy:all:level_2",
            ],
        },
        {"id": "2", "title": "Section two"},
    ],
}


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f)


def _mock_product_ids(known_products: list[str]):
    """Stand in for product_ids(), which lists the products directory."""
    return MagicMock(return_value=sorted(known_products))


def _discovery_for(tmp_path: Path, mock_get_repo: MagicMock):
    mock_repo = MagicMock()
    mock_repo.path = tmp_path
    mock_get_repo.return_value = mock_repo
    _write_yaml(tmp_path / "controls" / "nested.yml", NESTED_POLICY)

    from content_agent.core.discovery.controls import ControlDiscovery

    return ControlDiscovery()


class TestNestedModel:
    def test_nested_requirements_are_kept(self):
        control = ControlFile(**NESTED_POLICY)
        section = control.controls[0]
        assert [c.id for c in section.controls] == ["1.1"]
        assert section.controls[0].controls[0].id == "1.1.1"

    def test_string_entries_become_references(self):
        control = ControlFile(**NESTED_POLICY)
        section = control.controls[0]
        assert section.referenced_controls == ["other_policy:all:level_2"]
        assert all(isinstance(c, ControlRequirement) for c in section.controls)

    def test_flatten_lists_every_depth_parents_first(self):
        control = ControlFile(**NESTED_POLICY)
        assert [r.id for r in flatten_requirements(control.controls)] == [
            "1",
            "1.1",
            "1.1.1",
            "2",
        ]


class TestNestedDiscovery:
    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_stats_count_nested_requirements(self, mock_get_repo, tmp_path):
        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            stats = _discovery_for(tmp_path, mock_get_repo).get_control_stats("nested")

        assert stats is not None
        assert stats.total == 4
        assert stats.mapped == 3
        assert stats.unmapped == 1

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_rule_index_includes_nested_rules(self, mock_get_repo, tmp_path):
        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            index = _discovery_for(tmp_path, mock_get_repo).get_control_rule_index(
                control_ids=["nested"]
            )

        rules = {rule for req in index.requirements for rule in req.rules}
        assert rules == {"rule_top", "rule_child", "rule_grandchild"}

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_search_finds_nested_requirement(self, mock_get_repo, tmp_path):
        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            results = _discovery_for(tmp_path, mock_get_repo).search_controls(
                "grandchild", control_id="nested"
            )

        assert [r.id for r in results] == ["1.1.1"]

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_file_path_found_for_nested_requirement(self, mock_get_repo, tmp_path):
        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            result = _discovery_for(tmp_path, mock_get_repo).get_requirement_file_path(
                "nested", "1.1.1"
            )

        assert result is not None
        assert result.format == "inline"
        assert result.file_path == (tmp_path / "controls" / "nested.yml").resolve()
