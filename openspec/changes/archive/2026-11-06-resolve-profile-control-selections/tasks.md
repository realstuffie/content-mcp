## 1. Core Implementation

- [x] 1.1 Add `ProfileRuleResolver` in `src/content_agent/core/discovery/profile_resolution.py`
- [x] 1.2 Build `_profile_rule_index` in `src/content_agent/core/discovery/rules.py` from resolved profile rules
- [x] 1.3 Fix `_parse_profile` in `src/content_agent/core/discovery/profiles.py` for indented comments, Jinja lines, quotes and inline comments

## 2. Tests

- [x] 2.1 Unit tests for `policy:all`, `policy:all:level` with inheritance and default levels, and single requirements with nested and referenced requirements
- [x] 2.2 Unit tests for unselections, variables, refinements, `extends` and `extends` loops
- [x] 2.3 Unit tests for profile selection parsing
- [x] 2.4 Integration test: `accounts_umask_interactive_users` is selected by the rhel9 STIG profile

## 3. Quality Checks

- [x] 3.1 Run `mypy src/`
- [x] 3.2 Run `ruff check src/ tests/` and `black --check src/ tests/`
- [x] 3.3 Run the full test suite
