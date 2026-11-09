## Changes

- [x] Reproduce a stale index after a rule change and after an older timestamp.
- [x] Record each input file's mtime, ctime and size, and list rule directories.
- [x] Watch rule files, product files and product_properties for the profile index.
- [x] Use the same check for the template usage map.
- [x] Return configured rule roots, including missing ones.
- [x] Test the timestamp collision, a ctime-only change, nested and empty groups,
      files inside rule directories, missing roots and moved rule directories.
- [x] Check that the state covers every rule.yml the index reads in real content.
- [x] Update the README and OpenSpec requirements using unslop.
- [x] Run the full suite, formatting, Ruff, mypy, and whitespace checks.
