"""Tests for expanding rules with product variables and the fallbacks without a product."""

from unittest.mock import MagicMock, patch

import pytest


class FakeProduct(dict):
    """Stands in for ssg.products.Product, which is a dict with property loading."""

    def __init__(self, data, properties):
        super().__init__(data)
        self.properties = properties
        self.properties_dirs = []

    def read_properties_from_directory(self, path):
        self.properties_dirs.append(path)
        self.update(self.properties)


@pytest.fixture
def content_repo(tmp_path):
    for product in ("aaa", "ubuntu2204"):
        (tmp_path / "products" / product).mkdir(parents=True)
        (tmp_path / "products" / product / "product.yml").write_text(f"product: {product}\n")
    (tmp_path / "product_properties").mkdir()
    return tmp_path


def _discovery(repo_path):
    with patch("content_agent.core.discovery.rules.get_content_repository") as get_repo:
        get_repo.return_value.path = repo_path
        from content_agent.core.discovery.rules import RuleDiscovery

        return RuleDiscovery()


def _ssg_modules(products, expand):
    modules = MagicMock()
    modules.products.load_product_yaml.side_effect = lambda path: products[path.split("/")[-2]]
    modules.yaml.open_and_expand.side_effect = expand
    return modules


def test_product_expansion_uses_product_yaml_and_properties(content_repo, tmp_path):
    rule_file = tmp_path / "rule.yml"
    rule_file.write_text("title: test\n")
    product = FakeProduct({"product": "ubuntu2204", "full_name": "Ubuntu 22.04"}, {"auid": 1000})
    calls = []

    def expand(path, substitutions):
        calls.append(dict(substitutions))
        return {"title": substitutions["full_name"]}

    discovery = _discovery(content_repo)
    with patch(
        "content_agent.core.discovery.rules.get_ssg_modules",
        return_value=_ssg_modules({"ubuntu2204": product}, expand),
    ):
        result = discovery._load_rule_yaml(rule_file, product="ubuntu2204")
        discovery._load_rule_yaml(rule_file, product="ubuntu2204")

    assert result == {"title": "Ubuntu 22.04"}
    assert calls[0] == {"product": "ubuntu2204", "full_name": "Ubuntu 22.04", "auid": 1000}
    assert product.properties_dirs == [str(content_repo / "product_properties")]


def test_unknown_product_falls_back_to_product_name_only(content_repo, tmp_path):
    rule_file = tmp_path / "rule.yml"
    rule_file.write_text("title: test\n")
    calls = []

    def expand(path, substitutions):
        calls.append(dict(substitutions))
        return {"title": "expanded"}

    discovery = _discovery(content_repo)
    modules = _ssg_modules({}, expand)
    modules.products.load_product_yaml.side_effect = FileNotFoundError("no product.yml")
    with patch("content_agent.core.discovery.rules.get_ssg_modules", return_value=modules):
        discovery._load_rule_yaml(rule_file, product="missing")

    assert calls == [{"product": "missing"}]


def test_without_product_tries_placeholder_then_products(content_repo, tmp_path):
    rule_file = tmp_path / "rule.yml"
    rule_file.write_text("{{% if 'ubuntu' in product %}}\ntitle: test\n{{% endif %}}\n")
    products = {
        "aaa": FakeProduct({"product": "aaa"}, {}),
        "ubuntu2204": FakeProduct({"product": "ubuntu2204", "auid": 1000}, {}),
    }
    calls = []

    def expand(path, substitutions):
        calls.append(dict(substitutions))
        if "auid" not in substitutions:
            raise RuntimeError("'auid' is undefined")
        return {"title": "expanded"}

    discovery = _discovery(content_repo)
    with patch(
        "content_agent.core.discovery.rules.get_ssg_modules",
        return_value=_ssg_modules(products, expand),
    ):
        result = discovery._load_rule_yaml(rule_file)

    assert result == {"title": "expanded"}
    assert [c.get("product") for c in calls] == ["", "", "aaa", "ubuntu2204"]
    assert calls[1] == {"product": "", "full_name": "{{{ full_name }}}"}


def test_without_product_plain_yaml_wins_over_product_fallbacks(content_repo, tmp_path):
    rule_file = tmp_path / "rule.yml"
    rule_file.write_text("title: '{{{ full_name }}} rule'\n")
    calls = []

    def expand(path, substitutions):
        calls.append(dict(substitutions))
        raise RuntimeError("expansion failed")

    discovery = _discovery(content_repo)
    with patch(
        "content_agent.core.discovery.rules.get_ssg_modules",
        return_value=_ssg_modules({}, expand),
    ):
        result = discovery._load_rule_yaml(rule_file)

    assert result == {"title": "{{{ full_name }}} rule"}
    assert calls == [{"product": ""}]


def test_without_ssg_modules_falls_back_to_plain_yaml(content_repo, tmp_path):
    rule_file = tmp_path / "rule.yml"
    rule_file.write_text("title: plain\n")

    discovery = _discovery(content_repo)
    with patch(
        "content_agent.core.discovery.rules.get_ssg_modules",
        side_effect=RuntimeError("SSG modules not initialized"),
    ):
        assert discovery._load_rule_yaml(rule_file) == {"title": "plain"}
        assert discovery._load_rule_yaml(rule_file, product="ubuntu2204") == {"title": "plain"}
