"""Tests for expanding content files from current files with ssg.jinja's environment."""

import types
from pathlib import Path
from unittest.mock import patch

import pytest

import content_agent.core.discovery.jinja_expansion as jinja_expansion


class _Environment:
    def __init__(self) -> None:
        self.cache: dict | None = {}


def _fake_jinja(old_style: bool = False) -> types.ModuleType:
    """A stand-in for ssg.jinja, which makes its environment on first use."""
    jinja = types.ModuleType("ssg.jinja")

    def _get_jinja_environment(substitutions):
        if old_style:
            if _get_jinja_environment.env is None:
                _get_jinja_environment.env = _Environment()
            return _get_jinja_environment.env
        if jinja._jinja_env is None:
            jinja._jinja_env = _Environment()
        return jinja._jinja_env

    if old_style:
        _get_jinja_environment.env = None
    else:
        jinja._jinja_env = None
    jinja._get_jinja_environment = _get_jinja_environment
    return jinja


def _fake_yaml(jinja):
    ssg_yaml = types.SimpleNamespace()

    def open_and_expand(path, substitutions):
        environment = jinja._get_jinja_environment(substitutions)
        return {"path": path, "environment": environment}

    ssg_yaml.open_and_expand = open_and_expand
    return ssg_yaml


@pytest.fixture
def repo(tmp_path):
    macros = tmp_path / "shared" / "macros"
    macros.mkdir(parents=True)
    (macros / "10-general.jinja").write_text("{{% macro a() %}}a{{% endmacro %}}\n")
    (tmp_path / "products" / "rhel9").mkdir(parents=True)
    (tmp_path / "products" / "rhel9" / "product.yml").write_text("product: rhel9\n")
    jinja_expansion._environment_made_from = None
    with patch.object(jinja_expansion, "get_content_repository") as get_repo:
        get_repo.return_value.path = tmp_path
        yield tmp_path
    jinja_expansion._environment_made_from = None


def _expand(jinja, path: Path):
    with patch.object(jinja_expansion, "_ssg_jinja", return_value=jinja):
        return jinja_expansion.expand_yaml(_fake_yaml(jinja), path, {"product": "rhel9"})


def _environment(jinja):
    return jinja_expansion._environment(jinja)


def test_template_cache_is_turned_off(repo):
    jinja = _fake_jinja()

    _expand(jinja, repo / "rule.yml")

    assert _environment(jinja).cache is None


def test_environment_is_kept_while_its_inputs_are_unchanged(repo):
    jinja = _fake_jinja()

    first = _expand(jinja, repo / "rule.yml")["environment"]
    second = _expand(jinja, repo / "rule.yml")["environment"]

    assert first is second


@pytest.mark.parametrize(
    "change",
    [
        "shared/macros/10-general.jinja",
        "products/rhel9/product.yml",
        "product_properties/10-ids.yml",
    ],
)
def test_environment_is_made_again_when_an_input_changes(repo, change):
    jinja = _fake_jinja()
    first = _expand(jinja, repo / "rule.yml")["environment"]

    changed = repo / change
    changed.parent.mkdir(parents=True, exist_ok=True)
    changed.write_text("changed: true\n# a longer file than before\n")
    second = _expand(jinja, repo / "rule.yml")["environment"]

    assert second is not first


def test_environment_made_elsewhere_is_replaced(repo):
    # Its inputs' state is unknown, so it can't be trusted
    jinja = _fake_jinja()
    outside = jinja._get_jinja_environment({})

    made = _expand(jinja, repo / "rule.yml")["environment"]
    again = _expand(jinja, repo / "rule.yml")["environment"]

    assert made is not outside
    assert again is made


def test_older_ssg_jinja_keeps_the_environment_on_a_function(repo):
    jinja = _fake_jinja(old_style=True)
    first = _expand(jinja, repo / "rule.yml")["environment"]
    assert first.cache is None

    (repo / "shared" / "macros" / "20-new.jinja").write_text("{{% macro b() %}}b{{% endmacro %}}\n")
    second = _expand(jinja, repo / "rule.yml")["environment"]

    assert second is not first
    assert jinja._get_jinja_environment.env is second


def test_without_ssg_jinja_the_file_is_still_expanded(repo):
    ssg_yaml = types.SimpleNamespace(open_and_expand=lambda path, subs: {"path": path})

    with patch.object(jinja_expansion, "_ssg_jinja", return_value=None):
        result = jinja_expansion.expand_yaml(ssg_yaml, repo / "rule.yml", {})

    assert result == {"path": str(repo / "rule.yml")}
