"""Tests for loading requirement files from a control file's subdirectory."""

from unittest.mock import MagicMock, patch

import yaml

CONTROL_FILE = {"id": "pol", "title": "Policy", "controls_dir": "pol"}


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else yaml.dump(data))


def _discovery(repo_path):
    with patch("content_agent.core.discovery.controls.get_content_repository") as get_repo:
        get_repo.return_value.path = repo_path
        from content_agent.core.discovery.controls import ControlDiscovery

        return ControlDiscovery()


def _no_ssg():
    return patch(
        "content_agent.core.discovery.controls.get_ssg_modules",
        side_effect=RuntimeError("SSG modules not initialized"),
    )


def test_controls_wrapper_with_several_requirements(tmp_path):
    controls_dir = tmp_path / "controls"
    _write(controls_dir / "pol.yml", CONTROL_FILE)
    _write(
        controls_dir / "pol" / "ac.yml",
        {
            "controls": [
                {"id": "ac-1", "title": "First", "rules": ["rule_a"]},
                {"id": "ac-2", "title": "Second", "rules": ["rule_b"]},
            ]
        },
    )
    _write(controls_dir / "pol" / "single.yml", {"id": "single", "title": "Single"})

    with _no_ssg():
        control = _discovery(tmp_path).parse_control_file(controls_dir / "pol.yml")

    assert control is not None
    assert sorted(c.id for c in control.controls) == ["ac-1", "ac-2", "single"]
    assert control.parse_errors == []


def test_requirement_files_are_expanded_without_product(tmp_path):
    controls_dir = tmp_path / "controls"
    _write(controls_dir / "pol.yml", CONTROL_FILE)
    _write(
        controls_dir / "pol" / "SRG-1.yml",
        "controls:\n    -   id: SRG-1\n        title: {{{ full_name }}} must do it.\n",
    )
    calls = []

    def expand(path, substitutions):
        calls.append(dict(substitutions))
        return {"controls": [{"id": "SRG-1", "title": "The operating system must do it."}]}

    modules = MagicMock()
    modules.yaml.open_and_expand.side_effect = expand
    with patch("content_agent.core.discovery.controls.get_ssg_modules", return_value=modules):
        control = _discovery(tmp_path).parse_control_file(controls_dir / "pol.yml")

    assert control is not None
    assert control.controls[0].title == "The operating system must do it."
    assert calls == [{"product": "", "families": [], "full_name": "The operating system"}]


def test_requirement_files_are_expanded_with_product_variables(tmp_path):
    controls_dir = tmp_path / "controls"
    _write(controls_dir / "pol.yml", CONTROL_FILE)
    _write(controls_dir / "pol" / "SRG-1.yml", "controls:\n    -   id: SRG-1\n")
    (tmp_path / "products" / "ubuntu2204").mkdir(parents=True)
    calls = []

    def expand(path, substitutions):
        calls.append(dict(substitutions))
        return {"controls": [{"id": "SRG-1", "title": f"{substitutions['full_name']} must"}]}

    modules = MagicMock()
    modules.yaml.open_and_expand.side_effect = expand
    modules.products.load_product_yaml.return_value = {
        "product": "ubuntu2204",
        "full_name": "Ubuntu 22.04",
    }
    with patch("content_agent.core.discovery.controls.get_ssg_modules", return_value=modules):
        control = _discovery(tmp_path).parse_control_file(
            controls_dir / "pol.yml", product="ubuntu2204"
        )

    assert control is not None
    assert control.controls[0].title == "Ubuntu 22.04 must"
    assert calls == [{"product": "ubuntu2204", "full_name": "Ubuntu 22.04"}]
