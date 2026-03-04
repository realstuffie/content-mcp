## 1. Data Models

- [x] 1.1 Add `IndexedRequirement`, `ControlRuleIndex`, and `SimilarRequirement` models to `src/content_agent/models/control.py`
- [x] 1.2 Add `RuleProductAvailability` model to `src/content_agent/models/rule.py`

## 2. Control Rule Index

- [x] 2.1 Verify `parse_control_file()` handles the `controls_dir` pattern (subdirectory of individual control YAML files); fix if missing
- [x] 2.2 Implement recursive control flattening helper in `ControlDiscovery` to handle nested `controls` lists
- [x] 2.3 Implement `get_control_rule_index()` method on `ControlDiscovery` with `include_unmapped` and `control_ids` params
- [x] 2.4 Add module-level `get_control_rule_index()` convenience function in `controls.py`
- [x] 2.5 Add `get_control_rule_index` tool definition and handler in `tools.py`

## 3. Similar Requirements

- [x] 3.1 Add `_STOPWORDS`, `_tokenize()`, and `_jaccard_similarity()` to `ControlDiscovery`
- [x] 3.2 Implement `find_similar_requirements()` method on `ControlDiscovery`
- [x] 3.3 Add module-level `find_similar_requirements()` convenience function in `controls.py`
- [x] 3.4 Add `find_similar_requirements` tool definition and handler in `tools.py`

## 4. Rule Product Availability

- [x] 4.1 Implement profile→rule reverse index builder with instance-level caching on `RuleDiscovery`
- [x] 4.2 Implement `get_rule_product_availability()` method on `RuleDiscovery`
- [x] 4.3 Add module-level `get_rule_product_availability()` convenience function in `rules.py`
- [x] 4.4 Add `get_rule_product_availability` tool definition and handler in `tools.py`

## 5. Enhance suggest_rule_mappings

- [x] 5.1 Add `cross_reference` and `target_product` optional params to `suggest_rule_mappings` tool schema in `tools.py`
- [x] 5.2 Modify `RuleMapper.suggest_rules()` and `suggest_rules_for_text()` to accept and use `cross_reference` and `target_product` params
- [x] 5.3 When `cross_reference=true`, call `find_similar_requirements()` and append cross-framework evidence section to the AI prompt
- [x] 5.4 When `target_product` is set, prioritize rules with identifiers for that product in `_build_rules_context()`
- [x] 5.5 Update handler in `tools.py` to pass new params through to `RuleMapper`

## 6. Tests

- [x] 6.1 Create `tests/unit/test_control_rule_index.py` — test index building, unmapped filtering, control_ids filtering, nested flattening, unique rule counting
- [x] 6.2 Create `tests/unit/test_similar_requirements.py` — test tokenization, Jaccard similarity, find_similar_requirements with mock data, edge cases
- [x] 6.3 Create `tests/unit/test_rule_product_availability.py` — test identifier extraction, profile scanning, control reference exclusion, cache reuse
- [x] 6.4 Add integration tests for new tool handlers in `tests/integration/test_tools.py`

## 7. Verification

- [x] 7.1 Run `mypy src/content_agent/` and fix any type errors
- [x] 7.2 Run `ruff check src/ tests/` and `black --check src/ tests/` and fix any issues
- [x] 7.3 Run full test suite `pytest tests/` and verify all tests pass
