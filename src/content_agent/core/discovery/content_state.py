"""Tell when the content files behind a cached result have changed.

The profile index and the template usage map each read thousands of files, so
the server keeps them between tool calls with the state of the files they were
built from. Before reusing one, it takes the state again and compares the two.

A file's entry holds its st_mtime_ns, st_ctime_ns and size. Entries are
compared one by one, so a change counts even when the file's new time is older
than another file's. ctime also changes when a copy keeps the old mtime, as
`cp -p`, `rsync -t` and tar do. This compares metadata, not contents.

Each check lists the rule trees again, down to each rule directory but not
inside it, because the build never looks for rules inside a rule directory.
Comparing the names finds a new or removed rule or group at any depth without
relying on directory timestamps, which can stay the same for changes within
one clock tick. Listing the 2566 rules in the content repository takes about
10 ms.
"""

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple


class Entry(NamedTuple):
    """One file or directory a cached result depends on."""

    path: str
    kind: str  # "file", "dir" or "missing"
    mtime_ns: int = 0
    ctime_ns: int = 0
    size: int = 0


def file_entry(path: Path) -> Entry:
    """Return a file's state, or a "missing" entry if it can't be read."""
    try:
        stat = path.stat()
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
        rule_file = os.path.join(directory, "rule.yml")
        try:
            stat = os.stat(rule_file)
        except OSError:
            pass
        else:
            entries.append(
                Entry(rule_file, "file", stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
            )
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


@dataclass(frozen=True)
class ContentState:
    """The state of the files a cached result was built from.

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
        try:
            current = take_content_state(self.repo_path, self.patterns, self.rule_roots)
        except OSError:
            return False
        return current.entries == self.entries


def take_content_state(
    repo_path: Path, patterns: Sequence[str], rule_roots: Iterable[Path] = ()
) -> ContentState:
    """Record the files matching `patterns` and the rule trees under `rule_roots`."""
    roots = tuple(dict.fromkeys(rule_roots))
    entries: set[Entry] = set()
    for pattern in patterns:
        entries.update(file_entry(path) for path in repo_path.glob(pattern))
    for root in roots:
        entries.update(rule_tree_entries(root))
    return ContentState(repo_path, tuple(patterns), roots, tuple(sorted(entries)))
