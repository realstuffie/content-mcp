"""Where ComplianceAsCode keeps rules."""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Used when no product.yml names a benchmark root, as in minimal test repositories
DEFAULT_RULE_DIRS = ("linux_os", "applications")

_BENCHMARK_ROOT = re.compile(r"^benchmark_root:\s*['\"]?(?P<path>[^'\"#\s]+)", re.MULTILINE)


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
