"""Tests for per-product control discovery."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from content_agent.models.control import (
    ControlFile,
    ControlRequirement,
)


def _make_requirement(
    req_id: str,
    title: str = "Test",
    description: str = "Test description",
    rules: list[str] | None = None,
    status: str = "pending",
) -> ControlRequirement:
    return ControlRequirement(
        id=req_id,
        title=title,
        description=description,
        rules=rules or [],
        status=status,
    )


def _make_control_file(
    control_id: str,
    title: str = "Test Control",
    controls: list[ControlRequirement] | None = None,
) -> ControlFile:
    return ControlFile(
        id=control_id,
        title=title,
        controls=controls or [],
    )


def _write_control_yaml(path: Path, control_id: str, title: str, controls: list | None = None):
    """Write a minimal control YAML file."""
    data = {"id": control_id, "title": title, "controls": controls or []}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data))


def _mock_product_ids(known_products: list[str]):
    """Stand in for product_ids(), which lists the products directory."""
    return MagicMock(return_value=sorted(known_products))


class TestGetControlsDirs:
    """Test ControlDiscovery._get_controls_dirs()."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_global_dir_only(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            discovery = ControlDiscovery()
            dirs = discovery._get_controls_dirs(product=None)

        assert dirs == [tmp_path / "controls"]

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_product_specified_with_controls_dir(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()
        (tmp_path / "products" / "rhel9" / "controls").mkdir(parents=True)

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel9"]),
        ):
            discovery = ControlDiscovery()
            dirs = discovery._get_controls_dirs(product="rhel9")

        assert dirs == [
            tmp_path / "controls",
            tmp_path / "products" / "rhel9" / "controls",
        ]

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_product_specified_without_controls_dir(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()
        # Product exists but has no controls/ subdir
        (tmp_path / "products" / "fedora").mkdir(parents=True)

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["fedora"]),
        ):
            discovery = ControlDiscovery()
            dirs = discovery._get_controls_dirs(product="fedora")

        assert dirs == [tmp_path / "controls"]

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_invalid_product_raises_error(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel9"]),
        ):
            discovery = ControlDiscovery()
            with pytest.raises(ValueError, match="Unknown product 'nonexistent'"):
                discovery._get_controls_dirs(product="nonexistent")

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_no_product_discovers_all(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()
        (tmp_path / "products" / "rhel8" / "controls").mkdir(parents=True)
        (tmp_path / "products" / "rhel9" / "controls").mkdir(parents=True)

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel8", "rhel9"]),
        ):
            discovery = ControlDiscovery()
            dirs = discovery._get_controls_dirs(product=None)

        assert dirs == [
            tmp_path / "controls",
            tmp_path / "products" / "rhel8" / "controls",
            tmp_path / "products" / "rhel9" / "controls",
        ]


class TestListControlsOverride:
    """Test override semantics in list_controls."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_product_override_global(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path

        # Global control
        _write_control_yaml(
            tmp_path / "controls" / "cis_rhel9.yml", "cis_rhel9", "CIS RHEL9 Global"
        )
        # Product-specific override
        _write_control_yaml(
            tmp_path / "products" / "rhel9" / "controls" / "cis_rhel9.yml",
            "cis_rhel9",
            "CIS RHEL9 Product",
        )
        # Global-only control
        _write_control_yaml(tmp_path / "controls" / "anssi.yml", "anssi", "ANSSI")

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel9"]),
        ):
            discovery = ControlDiscovery()
            controls = discovery.list_controls(product="rhel9")

        # Both should appear, no duplicate
        assert sorted(controls) == ["anssi", "cis_rhel9"]

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_override_loads_product_file(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path

        _write_control_yaml(tmp_path / "controls" / "cis_rhel9.yml", "cis_rhel9", "CIS Global")
        _write_control_yaml(
            tmp_path / "products" / "rhel9" / "controls" / "cis_rhel9.yml",
            "cis_rhel9",
            "CIS Product",
        )

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel9"]),
        ):
            discovery = ControlDiscovery()
            details = discovery.get_control_details("cis_rhel9", product="rhel9")

        assert details is not None
        assert details.title == "CIS Product"


class TestGetControlDetailsSourceDir:
    """Test that source_dir is set on loaded ControlFile."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_source_dir_global(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        _write_control_yaml(tmp_path / "controls" / "anssi.yml", "anssi", "ANSSI")

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids([]),
        ):
            discovery = ControlDiscovery()
            details = discovery.get_control_details("anssi")

        assert details is not None
        assert details.source_dir == tmp_path / "controls"

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_source_dir_product(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()
        _write_control_yaml(
            tmp_path / "products" / "rhel9" / "controls" / "cis_rhel9.yml",
            "cis_rhel9",
            "CIS",
        )

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel9"]),
        ):
            discovery = ControlDiscovery()
            details = discovery.get_control_details("cis_rhel9", product="rhel9")

        assert details is not None
        assert details.source_dir == tmp_path / "products" / "rhel9" / "controls"


class TestRequirementFilePathProduct:
    """Test get_requirement_file_path with product parameter."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_inline_in_product_dir(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()

        ctrl_data = {
            "id": "custom",
            "title": "Custom",
            "controls": [{"id": "C1", "title": "Req 1", "description": "desc"}],
        }
        ctrl_path = tmp_path / "products" / "rhel9" / "controls" / "custom.yml"
        ctrl_path.parent.mkdir(parents=True)
        ctrl_path.write_text(yaml.dump(ctrl_data))

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel9"]),
        ):
            discovery = ControlDiscovery()
            result = discovery.get_requirement_file_path("custom", "C1", product="rhel9")

        assert result is not None
        assert result.format == "inline"
        assert "products/rhel9/controls/custom.yml" in str(result.file_path)

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_directory_based_in_product_dir(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()

        # Parent file with controls_dir
        ctrl_data = {"id": "cis", "title": "CIS", "controls_dir": "cis"}
        ctrl_path = tmp_path / "products" / "rhel9" / "controls" / "cis.yml"
        ctrl_path.parent.mkdir(parents=True)
        ctrl_path.write_text(yaml.dump(ctrl_data))

        # Requirement file in subdirectory
        req_dir = tmp_path / "products" / "rhel9" / "controls" / "cis"
        req_dir.mkdir()
        (req_dir / "1.1.1.yml").write_text(
            yaml.dump({"id": "1.1.1", "title": "Test", "description": "desc"})
        )

        from content_agent.core.discovery.controls import ControlDiscovery

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel9"]),
        ):
            discovery = ControlDiscovery()
            result = discovery.get_requirement_file_path("cis", "1.1.1", product="rhel9")

        assert result is not None
        assert result.format == "directory"
        assert result.exists is True
        assert "products/rhel9/controls/cis/1.1.1.yml" in str(result.file_path)


class TestUpdateRequirementRulesProduct:
    """Test ControlUpdater with product parameter."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    @patch("content_agent.core.scaffolding.control_updater.get_content_repository")
    def test_update_product_specific_inline(self, mock_updater_repo, mock_disc_repo, tmp_path):
        mock_updater_repo.return_value.path = tmp_path
        mock_disc_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()

        ctrl_content = textwrap.dedent("""\
            id: custom
            title: Custom
            controls:
                - id: C1
                  title: Req 1
                  description: desc
                  rules: []
                  status: pending
        """)
        ctrl_path = tmp_path / "products" / "rhel9" / "controls" / "custom.yml"
        ctrl_path.parent.mkdir(parents=True)
        ctrl_path.write_text(ctrl_content)

        from content_agent.core.scaffolding.control_updater import ControlUpdater

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel9"]),
        ):
            updater = ControlUpdater()
            result = updater.update_requirement_rules(
                control_id="custom",
                requirement_id="C1",
                rules=["rule_x"],
                status="automated",
                product="rhel9",
            )

        assert result.success is True
        updated = ctrl_path.read_text()
        assert "rule_x" in updated
        assert "automated" in updated


class TestGenerateControlStructureProduct:
    """Test ControlGenerator with product parameter."""

    @patch("content_agent.core.scaffolding.control_generator.get_content_repository")
    def test_generate_into_product_dir(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "products" / "rhel9" / "controls").mkdir(parents=True)

        from content_agent.core.scaffolding.control_generator import ControlGenerator
        from content_agent.models.control import ExtractedRequirement

        reqs = [
            ExtractedRequirement(
                text="Test requirement",
                section_id="sec1",
                section_title="Section 1",
                potential_id="REQ-1",
            )
        ]

        generator = ControlGenerator()
        result = generator.generate_control_structure(
            policy_id="my_policy",
            policy_title="My Policy",
            requirements=reqs,
            format="inline",
            product="rhel9",
        )

        assert result.success is True
        expected_parent = tmp_path / "products" / "rhel9" / "controls" / "my_policy.yml"
        assert expected_parent.exists()

    @patch("content_agent.core.scaffolding.control_generator.get_content_repository")
    def test_generate_without_product(self, mock_repo, tmp_path):
        mock_repo.return_value.path = tmp_path
        (tmp_path / "controls").mkdir()

        from content_agent.core.scaffolding.control_generator import ControlGenerator
        from content_agent.models.control import ExtractedRequirement

        reqs = [
            ExtractedRequirement(
                text="Test requirement",
                section_id="sec1",
                section_title="Section 1",
                potential_id="REQ-1",
            )
        ]

        generator = ControlGenerator()
        result = generator.generate_control_structure(
            policy_id="my_policy",
            policy_title="My Policy",
            requirements=reqs,
            format="inline",
        )

        assert result.success is True
        expected_parent = tmp_path / "controls" / "my_policy.yml"
        assert expected_parent.exists()


class TestSourceDirModelField:
    """Test ControlFile.source_dir field."""

    def test_source_dir_default_none(self):
        cf = ControlFile(id="test", title="Test")
        assert cf.source_dir is None

    def test_source_dir_set(self, tmp_path):
        cf = ControlFile(id="test", title="Test", source_dir=tmp_path / "controls")
        assert cf.source_dir == tmp_path / "controls"

    def test_source_dir_serialization(self, tmp_path):
        cf = ControlFile(id="test", title="Test", source_dir=tmp_path / "controls")
        dumped = cf.model_dump(mode="json")
        assert "source_dir" in dumped


class TestPoliciesWithoutAProduct:
    """Which control file is used when no product is given."""

    def _discovery(self, repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        with patch("content_agent.core.discovery.controls.get_content_repository") as get_repo:
            get_repo.return_value.path = repo
            discovery = ControlDiscovery()
        return discovery

    def _repo(self, tmp_path):
        req = [{"id": "R1", "title": "First", "rules": ["rule_a"]}]
        _write_control_yaml(tmp_path / "controls" / "shared.yml", "shared", "Global", req)
        _write_control_yaml(
            tmp_path / "products" / "rhel9" / "controls" / "shared.yml", "shared", "RHEL 9", req
        )
        _write_control_yaml(
            tmp_path / "products" / "rhel9" / "controls" / "stig_rhel9.yml",
            "stig_rhel9",
            "STIG",
            req,
        )
        for product in ("rhel8", "rhel9"):
            _write_control_yaml(
                tmp_path / "products" / product / "controls" / "nist.yml",
                "nist",
                f"NIST for {product}",
                [{"id": "ac-2", "title": "Account Management", "rules": [f"rule_{product}"]}],
            )
        return tmp_path

    def test_global_file_wins_without_product(self, tmp_path):
        discovery = self._discovery(self._repo(tmp_path))

        assert discovery.get_control_details("shared").title == "Global"
        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel8", "rhel9"]),
        ):
            assert discovery.get_control_details("shared", product="rhel9").title == "RHEL 9"

    def test_policy_of_one_product(self, tmp_path):
        discovery = self._discovery(self._repo(tmp_path))

        control = discovery.get_control_details("stig_rhel9")

        assert control is not None
        assert control.title == "STIG"

    def test_policy_of_several_products_needs_a_product(self, tmp_path):
        from content_agent.core.discovery.controls import AmbiguousControlError

        discovery = self._discovery(self._repo(tmp_path))

        with pytest.raises(AmbiguousControlError, match=r"defined per product \(rhel8, rhel9\)"):
            discovery.get_control_details("nist")
        assert discovery.controls_needing_product() == ["nist"]

    def test_rule_index_includes_each_product_version(self, tmp_path):
        discovery = self._discovery(self._repo(tmp_path))

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel8", "rhel9"]),
        ):
            index = discovery.get_control_rule_index(control_ids=["nist", "shared"])

        tagged = sorted((r.control_id, r.product, tuple(r.rules)) for r in index.requirements)
        assert tagged == [
            ("nist", "rhel8", ("rule_rhel8",)),
            ("nist", "rhel9", ("rule_rhel9",)),
            ("shared", None, ("rule_a",)),
        ]

    def test_similar_requirements_say_which_product(self, tmp_path):
        discovery = self._discovery(self._repo(tmp_path))

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel8", "rhel9"]),
        ):
            similar = discovery.find_similar_requirements("account management", min_similarity=0.5)

        assert sorted((s.control_id, s.product) for s in similar) == [
            ("nist", "rhel8"),
            ("nist", "rhel9"),
        ]

    def test_search_leaves_out_policies_of_several_products(self, tmp_path):
        discovery = self._discovery(self._repo(tmp_path))

        with patch(
            "content_agent.core.discovery.controls.product_ids",
            _mock_product_ids(["rhel8", "rhel9"]),
        ):
            found = discovery.search_controls("account management")
            found_for_rhel8 = discovery.search_controls("account management", product="rhel8")

        assert found == []
        assert [r.id for r in found_for_rhel8] == ["ac-2"]
