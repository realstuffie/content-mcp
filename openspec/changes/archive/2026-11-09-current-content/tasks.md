## Changes

- [x] Reproduce a stale expansion after a rewrite that keeps mtime and size.
- [x] Expand rules and control files through expand_yaml().
- [x] Turn off the ssg.jinja template cache and drop the environment when its inputs change.
- [x] Hash recently changed files, and every file where ctime is a creation time.
- [x] Watch shared/macros for the profile index.
- [x] Remove the product list and template usage caches.
- [x] Check product names against product directories in control discovery.
- [x] Test with real expansion, a fake ssg.jinja, frozen file stats and both ssg.jinja layouts.
- [x] Update the README, architecture notes and OpenSpec requirements using unslop.
- [x] Run the full suite, formatting, Ruff, mypy, and whitespace checks.
