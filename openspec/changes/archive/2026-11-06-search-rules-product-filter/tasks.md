## 1. Core Implementation

- [x] 1.1 Match the product filter against rules the product's profiles select
- [x] 1.2 Share the profile index between `RuleDiscovery` instances, keyed by content repository and invalidated by profile and control file changes

## 2. Tests

- [x] 2.1 Unit tests for the product filter and for sharing and rebuilding the index
- [x] 2.2 Integration test: an Ubuntu 22.04 search for `sshd` finds `sshd_disable_root_login`

## 3. Quality Checks

- [x] 3.1 Run `mypy src/`
- [x] 3.2 Run `ruff check src/ tests/` and `black --check src/ tests/`
- [x] 3.3 Run the full test suite
