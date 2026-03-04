## 1. Core Implementation

- [x] 1.1 Add `_load_rule_yaml` helper method to `RuleDiscovery` in `src/content_agent/core/discovery/rules.py` that uses `ssg.yaml.open_and_expand()` with product-aware substitutions and fallback to raw `yaml.load()`
- [x] 1.2 Update `get_rule_details()` to use `_load_rule_yaml` instead of direct `yaml.load()`
- [x] 1.3 Update `_load_search_result()` to accept `product` parameter and use `_load_rule_yaml`
- [x] 1.4 Update all `_load_search_result()` call sites in `search_rules()` to pass `product` parameter

## 2. Tests

- [x] 2.1 Add test that a rule with Jinja2 control structures is discoverable via `get_rule_details` (without product)
- [x] 2.2 Add test that a rule with Jinja2 control structures returns product-specific content when `product` is provided
- [x] 2.3 Add test that `search_rules` includes rules with Jinja2 control structures
- [x] 2.4 Run full test suite and verify no regressions

## 3. Quality Checks

- [x] 3.1 Run `black` and `ruff` to verify formatting and lint compliance
- [x] 3.2 Run `mypy src/` to verify type checking passes
