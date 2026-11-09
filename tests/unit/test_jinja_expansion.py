"""Tests for expanding content files from current files with ssg.jinja's environment."""

import types
from pathlib import Path
from unittest.mock import patch

import pytest

import content_agent.core.discovery.jinja_expansion as jinja_expansion


class _Environment:
    def __init__(self, variables: dict) -> None:
        self.cache: dict | None = {}
        self.variables = dict(variables)


def _fake_jinja(old_style: bool = False) -> types.ModuleType:
    """A stand-in for ssg.jinja, which makes its environment on first use."""
    jinja = types.ModuleType("ssg.jinja")

    def _get_jinja_environment(substitutions):
        if old_style:
            if _get_jinja_environment.env is None:
                _get_jinja_environment.env = _Environment(substitutions)
            return _get_jinja_environment.env
        if jinja._jinja_env is None:
            jinja._jinja_env = _Environment(substitutions)
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
    jinja_expansion._environments.clear()
    jinja_expansion._inputs = None
    with patch.object(jinja_expansion, "get_content_repository") as get_repo:
        get_repo.return_value.path = tmp_path
        yield tmp_path
    jinja_expansion._environments.clear()
    jinja_expansion._inputs = None


def _expand(jinja, path: Path, product: str = "rhel9"):
    with patch.object(jinja_expansion, "_ssg_jinja", return_value=jinja):
        return jinja_expansion.expand_yaml(_fake_yaml(jinja), path, {"product": product})


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
    # Its variables and inputs are unknown, so it can't be trusted
    jinja = _fake_jinja()
    outside = jinja._get_jinja_environment({"product": "rhel9"})

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


def test_stand_in_yaml_module_is_called_directly(repo):
    # Tests pass mocks for ssg.yaml, which must see the caller's variables
    seen = []
    ssg_yaml = types.SimpleNamespace(open_and_expand=lambda path, subs: seen.append(subs))

    jinja_expansion.expand_yaml(ssg_yaml, repo / "rule.yml", {"product": "rhel9"})

    assert seen == [{"product": "rhel9"}]
    assert not jinja_expansion._environments


def test_each_product_gets_its_own_environment(repo):
    jinja = _fake_jinja()

    rhel = _expand(jinja, repo / "rule.yml", "rhel9")["environment"]
    ubuntu = _expand(jinja, repo / "rule.yml", "ubuntu2204")["environment"]
    rhel_again = _expand(jinja, repo / "rule.yml", "rhel9")["environment"]

    assert ubuntu is not rhel
    assert rhel_again is rhel
    assert (rhel.variables["product"], ubuntu.variables["product"]) == ("rhel9", "ubuntu2204")


def test_environments_use_a_bytecode_cache(repo):
    jinja = _fake_jinja()

    variables = _expand(jinja, repo / "rule.yml")["environment"].variables

    assert variables["jinja2_cache_enabled"] == "true"
    assert Path(variables["jinja2_cache_dir"]).is_dir()


def test_caller_variables_are_left_unchanged(repo):
    jinja = _fake_jinja()
    substitutions = {"product": "rhel9"}

    with patch.object(jinja_expansion, "_ssg_jinja", return_value=jinja):
        jinja_expansion.expand_yaml(_fake_yaml(jinja), repo / "rule.yml", substitutions)

    assert substitutions == {"product": "rhel9"}


def test_least_recently_used_environment_is_dropped(repo, monkeypatch):
    monkeypatch.setattr(jinja_expansion, "MAX_ENVIRONMENTS", 2)
    jinja = _fake_jinja()
    rhel = _expand(jinja, repo / "rule.yml", "rhel9")["environment"]
    _expand(jinja, repo / "rule.yml", "ubuntu2204")
    _expand(jinja, repo / "rule.yml", "rhel9")

    _expand(jinja, repo / "rule.yml", "sle15")

    assert _expand(jinja, repo / "rule.yml", "rhel9")["environment"] is rhel
    assert len(jinja_expansion._environments) == 2


def test_input_change_drops_every_environment(repo):
    jinja = _fake_jinja()
    rhel = _expand(jinja, repo / "rule.yml", "rhel9")["environment"]
    ubuntu = _expand(jinja, repo / "rule.yml", "ubuntu2204")["environment"]

    (repo / "shared" / "macros" / "10-general.jinja").write_text(
        "{{% macro a() %}}b{{% endmacro %}}\n"
    )

    assert _expand(jinja, repo / "rule.yml", "rhel9")["environment"] is not rhel
    assert _expand(jinja, repo / "rule.yml", "ubuntu2204")["environment"] is not ubuntu
