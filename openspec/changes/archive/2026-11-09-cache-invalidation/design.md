## Compare each file

A state is a sorted tuple of entries, one per file or directory, compared as a
whole. A file's entry holds its path, `st_mtime_ns`, `st_ctime_ns` and size, so
any change to one file changes the state, whatever the other files' times.

ctime catches copies that keep the old mtime, such as `cp -p`, `rsync -t` and
tar extraction. On Linux the kernel sets ctime on every write and on `utime`,
and programs can't set it. A change that keeps mtime, ctime and size would
still be missed. Hashing would catch it, but would read every input file on
each call, so this stays a metadata check.

## List rule directories instead of trusting their timestamps

A new rule or group shows up as a new directory. Watching directory mtimes
would need the snapshot to record every directory, and directory timestamps
come from a clock that can tick slower than file operations. A rule created in
the same tick as the snapshot could keep the directory's old time.

The check lists the rule directories again instead, from each root named in a
`product.yml` down to each rule directory, and compares the names. It records
every directory on the way, including empty ones and groups without a
`group.yml`, so a rule in a new nested group or an existing empty directory
changes the state. It doesn't go inside a rule directory: the build never looks
for rules there (`DirectoryLoader._collect_items_to_load` adds a rule directory
to the rule files and does not recurse), and skipping them means adding a test
scenario or an OVAL file doesn't trigger a rebuild.

A root that doesn't exist is recorded as missing, so creating it later changes
the state.

## Refresh the watched directories with product.yml

The rule roots come from `product.yml` files, and those files are part of the
state. A changed `benchmark_root` or added `additional_content_directories`
makes the state stale. The rebuild takes a new state, which works out the roots
again from the changed files.

## Cost

Measured on content `f09d243`, 2566 rules, warm file cache:

| Check | Before | After |
|---|---|---|
| Profile index reuse | 3 ms | 19 ms |
| Template usage reuse | 70 ms (globbed every `rule.yml`) | 15 ms |

The rule tree walk uses strings and `os.stat` rather than `Path`. With `Path`,
it took 33 ms.
