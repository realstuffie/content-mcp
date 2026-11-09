"""Where ComplianceAsCode keeps rules."""

import logging
import os
import re
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Used when no product.yml names a benchmark root, as in minimal test repositories
DEFAULT_RULE_DIRS = ("linux_os", "applications")

_BENCHMARK_ROOT = re.compile(r"^benchmark_root:\s*['\"]?(?P<path>[^'\"#\s]+)", re.MULTILINE)
# The build skips a rule whose documentation_complete is exactly "false"
_DOCUMENTATION_INCOMPLETE = re.compile(
    r"^documentation_complete:[ \t]*['\"]?false['\"]?[ \t]*(?:#.*)?$", re.MULTILINE
)


def rule_directories(repo_path: Path) -> list[Path]:
    """Return the directories the content build reads rules from.

    Each product's product.yml names its benchmark root, relative to the
    product directory. Most products share linux_os/guide, the OpenShift and
    EKS products use applications, and Firefox keeps its rules in
    products/firefox/guide. Roots inside other roots are dropped, so no rule is
    found twice.

    Paths are normalized but not resolved, so they stay relative to
    ``repo_path`` the way callers expect.
    """
    repo = Path(os.path.normpath(repo_path))
    roots: set[Path] = set()
    for product_yml in sorted((repo / "products").glob("*/product.yml")):
        try:
            match = _BENCHMARK_ROOT.search(product_yml.read_text())
        except OSError as e:
            logger.debug(f"Could not read {product_yml}: {e}")
            continue
        if not match:
            continue
        root = Path(os.path.normpath(product_yml.parent / match["path"]))
        if root.is_dir() and root.is_relative_to(repo):
            roots.add(root)

    if not roots:
        roots = {repo / name for name in DEFAULT_RULE_DIRS if (repo / name).is_dir()}

    kept: list[Path] = []
    for root in sorted(roots, key=lambda path: len(path.parts)):
        if not any(root.is_relative_to(parent) for parent in kept):
            kept.append(root)
    return sorted(kept)


def rule_files(repo_path: Path) -> list[Path]:
    """Return every rule.yml the content build would read."""
    files: list[Path] = []
    for root in rule_directories(repo_path):
        files.extend(root.rglob("rule.yml"))
    return files


def product_rule_directories(repo_path: Path, product: str) -> list[Path] | None:
    """Return the directories the build reads a product's rules from.

    Like the build, this is the product's benchmark_root, relative to its
    directory, plus any additional_content_directories, relative to the
    repository. Returns None when the product names no benchmark root.
    """
    repo = Path(os.path.normpath(repo_path))
    product_yml = repo / "products" / product / "product.yml"
    try:
        data = yaml.safe_load(product_yml.read_text())
    except (OSError, yaml.YAMLError) as e:
        logger.debug(f"Could not read {product_yml}: {e}")
        return None
    if not isinstance(data, dict) or not data.get("benchmark_root"):
        return None
    directories = [Path(os.path.normpath(product_yml.parent / str(data["benchmark_root"])))]
    for extra in data.get("additional_content_directories") or []:
        directories.append(Path(os.path.normpath(repo / str(extra))))
    return [directory for directory in directories if directory.is_dir()]


def configured_rule_roots(repo_path: Path) -> list[Path]:
    """Return every rule directory product.yml files name, whether it exists or not.

    These are the benchmark roots and additional_content_directories of all
    products, inside the repository, without roots nested in other roots. This
    is what a cache of rule data has to watch: a named directory that doesn't
    exist yet may be created later. Without any named root, it is the default
    directories, as in rule_directories().
    """
    repo = Path(os.path.normpath(repo_path))
    roots: set[Path] = set()
    for product_yml in sorted((repo / "products").glob("*/product.yml")):
        try:
            data = yaml.safe_load(product_yml.read_text())
        except (OSError, yaml.YAMLError) as e:
            logger.debug(f"Could not read {product_yml}: {e}")
            continue
        if not isinstance(data, dict):
            continue
        named = []
        if data.get("benchmark_root"):
            named.append(product_yml.parent / str(data["benchmark_root"]))
        named.extend(
            repo / str(extra) for extra in data.get("additional_content_directories") or []
        )
        for path in named:
            root = Path(os.path.normpath(path))
            if root.is_relative_to(repo):
                roots.add(root)

    if not roots:
        roots = {repo / name for name in DEFAULT_RULE_DIRS}

    kept: list[Path] = []
    for root in sorted(roots, key=lambda path: len(path.parts)):
        if not any(root.is_relative_to(parent) for parent in kept):
            kept.append(root)
    return sorted(kept)


def product_rule_ids(
    repo_path: Path, product: str, directory_cache: dict[Path, set[str]] | None = None
) -> set[str] | None:
    """Return the IDs of the rules the build loads for a product, or None if unknown.

    Rules marked `documentation_complete: false` are left out, as in a normal
    (not Debug) build. Most products share a directory, so pass the same
    `directory_cache` for several products to read each directory once.
    """
    directories = product_rule_directories(repo_path, product)
    if directories is None:
        return None
    cache = directory_cache if directory_cache is not None else {}
    rule_ids: set[str] = set()
    for directory in directories:
        if directory not in cache:
            cache[directory] = _complete_rule_ids(directory)
        rule_ids |= cache[directory]
    return rule_ids


def _complete_rule_ids(directory: Path) -> set[str]:
    rule_ids: set[str] = set()
    for rule_file in directory.rglob("rule.yml"):
        try:
            if _DOCUMENTATION_INCOMPLETE.search(rule_file.read_text()):
                continue
        except OSError:
            continue
        rule_ids.add(rule_file.parent.name)
    return rule_ids
