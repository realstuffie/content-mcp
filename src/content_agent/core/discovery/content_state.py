"""Tell when the content files behind a kept result have changed.

Results that are slow to make, like the profile index, are kept between tool
calls with the state of the files they were made from. Before reusing one, the
caller takes the state again and compares the two.

A file's entry holds its st_mtime_ns, st_ctime_ns and size. Entries are
compared one by one, so a change counts even when the file's new time is older
than another file's. ctime also changes when a copy keeps the old mtime, as
`cp -p`, `rsync -t` and tar do.

Timestamps come from a clock that can tick every few milliseconds, so a file
rewritten with the same size within one tick of the last check can keep all
three values. Files changed in the last few seconds therefore also get a hash
of their contents, and keep it in later checks. Where ctime is a creation time
rather than a change time, as on Windows, every file gets a hash.

Each check lists the rule trees again, down to each rule directory but not
inside it, because the build never looks for rules inside a rule directory.
Comparing the names finds a new or removed rule or group at any depth without
relying on directory timestamps. Listing the 2566 rules in the content
repository takes about 10 ms.
"""

import hashlib
import os
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

# Files changed this recently are hashed. This covers clocks that tick every few
# milliseconds, FAT's 2-second mtime steps, and a file server's clock running
# a little behind this one.
RECENT_NS = 5_000_000_000

# On Windows, st_ctime is the creation time, so it doesn't change on a rewrite
CTIME_IS_CHANGE_TIME = os.name != "nt"


class Entry(NamedTuple):
    """One file or directory a kept result depends on."""

    path: str
    kind: str  # "file", "dir" or "missing"
    mtime_ns: int = 0
    ctime_ns: int = 0
    size: int = 0
    digest: str = ""


def file_entry(path: Path | str) -> Entry:
    """Return a file's state without a hash, or a "missing" entry if it can't be read."""
    try:
        stat = os.stat(path)
    except OSError:
        return Entry(str(path), "missing")
    return Entry(str(path), "file", stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)


def rule_tree_entries(root: Path) -> list[Entry]:
    """Return the directories under a rule root and the state of each rule.yml.

    This lists every directory that could hold a rule, including empty ones and
    groups without a group.yml. A directory with a rule.yml is a rule, and like
    the build, this doesn't go into its subdirectories (tests, oval, bash). A
    root that doesn't exist is recorded as missing, so creating it changes the
    state.
    """
    # Plain strings and os calls, which make this about three times faster than Path
    entries: list[Entry] = []
    pending = [str(root)]
    while pending:
        directory = pending.pop()
        rule_file = file_entry(os.path.join(directory, "rule.yml"))
        if rule_file.kind == "file":
            entries.append(rule_file)
            continue
        try:
            with os.scandir(directory) as listing:
                children = [item.path for item in listing if item.is_dir(follow_symlinks=False)]
        except OSError:
            entries.append(Entry(directory, "missing"))
            continue
        entries.append(Entry(directory, "dir"))
        pending.extend(children)
    return entries


def _digest(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return "unreadable"


def _with_digest(entry: Entry, since_ns: int, hash_paths: frozenset[str]) -> Entry:
    if entry.kind != "file":
        return entry
    recent = max(entry.mtime_ns, entry.ctime_ns) >= since_ns
    if recent or entry.path in hash_paths or not CTIME_IS_CHANGE_TIME:
        return entry._replace(digest=_digest(entry.path))
    return entry


@dataclass(frozen=True)
class ContentState:
    """The state of the files a kept result was made from.

    `patterns` are globs relative to the repository, such as
    "products/*/product.yml". `rule_roots` are the rule directories, which
    callers derive from product.yml files. Include "products/*/product.yml" in
    `patterns` when they do: a product.yml change then makes the state stale,
    and the caller works out the roots again for the new state.
    """

    repo_path: Path
    patterns: tuple[str, ...]
    rule_roots: tuple[Path, ...]
    entries: tuple[Entry, ...]

    def is_current(self) -> bool:
        """Return True if no recorded file or rule tree has changed."""
        hashed = frozenset(entry.path for entry in self.entries if entry.digest)
        try:
            current = take_content_state(self.repo_path, self.patterns, self.rule_roots, hashed)
        except OSError:
            return False
        return current.entries == self.entries


def take_content_state(
    repo_path: Path,
    patterns: Sequence[str],
    rule_roots: Iterable[Path] = (),
    hash_paths: frozenset[str] = frozenset(),
) -> ContentState:
    """Record the files matching `patterns` and the rule trees under `rule_roots`.

    Files changed in the last RECENT_NS, and the files in `hash_paths`, also get
    a hash of their contents.
    """
    since_ns = time.time_ns() - RECENT_NS
    roots = tuple(dict.fromkeys(rule_roots))
    entries: set[Entry] = set()
    for pattern in patterns:
        entries.update(file_entry(path) for path in repo_path.glob(pattern))
    for root in roots:
        entries.update(rule_tree_entries(root))
    hashed = {_with_digest(entry, since_ns, hash_paths) for entry in entries}
    return ContentState(repo_path, tuple(patterns), roots, tuple(sorted(hashed)))
