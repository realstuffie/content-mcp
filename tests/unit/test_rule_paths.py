"""Tests for finding the directories the content build reads rules from."""

from pathlib import Path
from unittest.mock import patch

from content_agent.core.discovery.rule_paths import rule_directories, rule_files


def _product(repo: Path, name: str, benchmark_root: str | None) -> None:
    product_dir = repo / "products" / name
    product_dir.mkdir(parents=True, exist_ok=True)
    line = f'benchmark_root: "{benchmark_root}"\n' if benchmark_root else ""
    (product_dir / "product.yml").write_text(f"product: {name}\n{line}")


def _rule(root: Path, rule_id: str) -> None:
    rule_dir = root / "group" / rule_id
    rule_dir.mkdir(parents=True)
    (rule_dir / "rule.yml").write_text(f"documentation_complete: true\ntitle: {rule_id}\n")


def test_roots_come_from_product_files(tmp_path):
    for name in ("linux_os/guide", "applications", "products/firefox/guide"):
        (tmp_path / name).mkdir(parents=True)
    _product(tmp_path, "rhel9", "../../linux_os/guide")
    _product(tmp_path, "ubuntu2204", "../../linux_os/guide")
    _product(tmp_path, "ocp4", "../../applications")
    _product(tmp_path, "firefox", "./guide")
    _product(tmp_path, "example", None)

    roots = rule_directories(tmp_path)

    assert [root.relative_to(tmp_path).as_posix() for root in roots] == [
        "applications",
        "linux_os/guide",
        "products/firefox/guide",
    ]


def test_nested_roots_are_kept_once(tmp_path):
    (tmp_path / "linux_os" / "guide").mkdir(parents=True)
    _product(tmp_path, "wide", "../../linux_os")
    _product(tmp_path, "narrow", "../../linux_os/guide")
    _rule(tmp_path / "linux_os" / "guide", "rule_a")

    assert rule_directories(tmp_path) == [tmp_path / "linux_os"]
    assert len(rule_files(tmp_path)) == 1


def test_roots_outside_the_repository_are_ignored(tmp_path):
    repo = tmp_path / "content"
    (repo / "linux_os" / "guide").mkdir(parents=True)
    (tmp_path / "elsewhere").mkdir()
    _product(repo, "rhel9", "../../linux_os/guide")
    _product(repo, "odd", "../../../elsewhere")

    assert rule_directories(repo) == [repo / "linux_os" / "guide"]


def test_defaults_without_benchmark_roots(tmp_path):
    (tmp_path / "linux_os").mkdir()
    (tmp_path / "applications").mkdir()
    _product(tmp_path, "rhel9", None)

    assert rule_directories(tmp_path) == [tmp_path / "applications", tmp_path / "linux_os"]


def test_rule_discovery_finds_product_rules(tmp_path):
    import content_agent.core.discovery.rules as rules_module

    (tmp_path / "linux_os" / "guide").mkdir(parents=True)
    _product(tmp_path, "rhel9", "../../linux_os/guide")
    _product(tmp_path, "firefox", "./guide")
    _rule(tmp_path / "linux_os" / "guide", "sshd_disable_root_login")
    _rule(tmp_path / "products" / "firefox" / "guide", "firefox_policy-disable_telemetry")

    with patch("content_agent.core.discovery.rules.get_content_repository") as get_repo:
        get_repo.return_value.path = tmp_path
        discovery = rules_module.RuleDiscovery()
    discovery._build_rule_index()

    assert discovery._rule_cache is not None
    assert set(discovery._rule_cache) == {
        "sshd_disable_root_login",
        "firefox_policy-disable_telemetry",
    }


class TestProductRules:
    """The rules the build loads for one product."""

    def _repo(self, tmp_path):
        from pathlib import Path

        for name in ("linux_os/guide", "applications", "shared/extra"):
            (tmp_path / name).mkdir(parents=True)
        _product(tmp_path, "rhel9", "../../linux_os/guide")
        _product(tmp_path, "ocp4", "../../applications")
        _rule(tmp_path / "linux_os" / "guide", "audit_rule")
        _rule(tmp_path / "applications", "api_server_rule")
        draft = tmp_path / "linux_os" / "guide" / "group" / "draft_rule"
        draft.mkdir(parents=True)
        (draft / "rule.yml").write_text("documentation_complete: false\ntitle: Draft\n")
        return Path(tmp_path)

    def test_rules_under_the_product_benchmark_root(self, tmp_path):
        from content_agent.core.discovery.rule_paths import product_rule_ids

        repo = self._repo(tmp_path)

        assert product_rule_ids(repo, "rhel9") == {"audit_rule"}
        assert product_rule_ids(repo, "ocp4") == {"api_server_rule"}

    def test_additional_content_directories(self, tmp_path):
        from content_agent.core.discovery.rule_paths import product_rule_ids

        repo = self._repo(tmp_path)
        _rule(repo / "shared" / "extra", "extra_rule")
        (repo / "products" / "rhel9" / "product.yml").write_text(
            'product: rhel9\nbenchmark_root: "../../linux_os/guide"\n'
            "additional_content_directories:\n  - shared/extra\n"
        )

        assert product_rule_ids(repo, "rhel9") == {"audit_rule", "extra_rule"}

    def test_unknown_without_benchmark_root(self, tmp_path):
        from content_agent.core.discovery.rule_paths import product_rule_ids

        repo = self._repo(tmp_path)
        _product(repo, "example", None)

        assert product_rule_ids(repo, "example") is None
        assert product_rule_ids(repo, "missing") is None

    def test_directories_read_once_across_products(self, tmp_path):
        from content_agent.core.discovery.rule_paths import product_rule_ids

        repo = self._repo(tmp_path)
        _product(repo, "rhel8", "../../linux_os/guide")
        cache: dict = {}

        product_rule_ids(repo, "rhel9", cache)
        _rule(repo / "linux_os" / "guide", "added_later")

        # The second product reuses what the first one read
        assert product_rule_ids(repo, "rhel8", cache) == {"audit_rule"}
