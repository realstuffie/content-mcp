"""Tests for recording the state of the files a cached result depends on."""

import os
import time
from pathlib import Path

from content_agent.core.discovery.content_state import take_content_state
from content_agent.core.discovery.rule_paths import configured_rule_roots

PRODUCT_FILES = ("products/*/product.yml",)
SECONDS = 1_000_000_000


def _product(repo: Path, name: str, benchmark_root: str, extra: list[str] | None = None) -> Path:
    product_dir = repo / "products" / name
    product_dir.mkdir(parents=True, exist_ok=True)
    text = f"product: {name}\nbenchmark_root: {benchmark_root}\n"
    if extra:
        text += "additional_content_directories:\n" + "".join(f"  - {d}\n" for d in extra)
    product_yml = product_dir / "product.yml"
    product_yml.write_text(text)
    return product_yml


def _rule(directory: Path, text: str = "title: A rule\n") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    rule_yml = directory / "rule.yml"
    rule_yml.write_text(text)
    return rule_yml


def _state(repo: Path):
    return take_content_state(repo, PRODUCT_FILES, configured_rule_roots(repo))


def _change_ctime_only(path: Path, text: str) -> None:
    """Rewrite a file with same-size text and put its mtime back, as `cp -p` would."""
    before = path.stat()
    assert len(text) == before.st_size
    path.write_text(text)
    # ctime comes from a clock that can tick slower than these calls
    for _ in range(200):
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        if path.stat().st_ctime_ns != before.st_ctime_ns:
            return
        time.sleep(0.005)
    raise AssertionError("ctime did not change")


def _repo(tmp_path: Path) -> Path:
    _product(tmp_path, "rhel9", "../../linux_os/guide")
    _rule(tmp_path / "linux_os" / "guide" / "group_a" / "rule_one")
    return tmp_path


def test_unchanged_files_are_current(tmp_path):
    repo = _repo(tmp_path)
    state = _state(repo)

    (repo / "linux_os" / "guide" / "group_a" / "rule_one" / "rule.yml").read_text()

    assert state.is_current()


def test_each_file_is_compared_not_only_the_newest(tmp_path):
    repo = _repo(tmp_path)
    profiles = repo / "products" / "rhel9" / "profiles"
    profiles.mkdir()
    older, newer = profiles / "a.profile", profiles / "b.profile"
    older.write_text("selections: []\n")
    newer.write_text("selections: []\n")
    os.utime(older, ns=(100 * SECONDS, 100 * SECONDS))
    os.utime(newer, ns=(200 * SECONDS, 200 * SECONDS))
    state = take_content_state(repo, ("products/*/profiles/*.profile",))

    # The newest time is still 200
    os.utime(older, ns=(150 * SECONDS, 150 * SECONDS))

    assert not state.is_current()


def test_same_mtime_and_size_with_a_new_ctime(tmp_path):
    repo = _repo(tmp_path)
    rule_yml = repo / "linux_os" / "guide" / "group_a" / "rule_one" / "rule.yml"
    state = _state(repo)

    _change_ctime_only(rule_yml, "title: B rule\n")

    assert not state.is_current()


def test_rule_in_a_new_nested_group(tmp_path):
    repo = _repo(tmp_path)
    state = _state(repo)

    _rule(repo / "linux_os" / "guide" / "group_a" / "new_group" / "deeper" / "rule_two")

    assert not state.is_current()


def test_rule_in_an_existing_empty_directory(tmp_path):
    repo = _repo(tmp_path)
    empty = repo / "linux_os" / "guide" / "group_b" / "empty"
    empty.mkdir(parents=True)
    state = _state(repo)

    _rule(empty / "rule_two")

    assert not state.is_current()


def test_removed_rule(tmp_path):
    repo = _repo(tmp_path)
    second = _rule(repo / "linux_os" / "guide" / "group_a" / "rule_two")
    state = _state(repo)

    second.unlink()

    assert not state.is_current()


def test_files_inside_a_rule_directory_are_ignored(tmp_path):
    # Adding a test scenario or an OVAL file doesn't change the rule set
    repo = _repo(tmp_path)
    rule_dir = repo / "linux_os" / "guide" / "group_a" / "rule_one"
    state = _state(repo)

    (rule_dir / "tests").mkdir()
    (rule_dir / "tests" / "correct.pass.sh").write_text("#!/bin/bash\n")
    (rule_dir / "oval").mkdir()

    assert state.is_current()


def test_root_created_after_the_state_was_taken(tmp_path):
    repo = _repo(tmp_path)
    _product(repo, "rhel9", "../../linux_os/guide", extra=["extra_rules"])
    state = _state(repo)
    assert repo / "extra_rules" in state.rule_roots

    _rule(repo / "extra_rules" / "rule_two")

    assert not state.is_current()


def test_new_benchmark_root_refreshes_the_watched_rules(tmp_path):
    repo = _repo(tmp_path)
    other_rule = _rule(repo / "other" / "guide" / "rule_two")
    state = _state(repo)
    assert state.rule_roots == (repo / "linux_os" / "guide",)

    _product(repo, "rhel9", "../../other/guide")

    assert not state.is_current()
    refreshed = _state(repo)
    assert refreshed.rule_roots == (repo / "other" / "guide",)
    other_rule.write_text("title: A changed rule\n")
    assert not refreshed.is_current()


def test_added_content_directory_refreshes_the_watched_rules(tmp_path):
    repo = _repo(tmp_path)
    extra_rule = _rule(repo / "extra_rules" / "rule_two")
    state = _state(repo)

    _product(repo, "rhel9", "../../linux_os/guide", extra=["extra_rules"])

    assert not state.is_current()
    refreshed = _state(repo)
    assert repo / "extra_rules" in refreshed.rule_roots
    extra_rule.write_text("title: A changed rule\n")
    assert not refreshed.is_current()
