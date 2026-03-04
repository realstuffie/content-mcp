## 1. Models Layer

- [x] 1.1 Create `src/content_agent/models/common.py` with `DiscoveryResult[T]` generic dataclass (`items: list[T]`, `errors: list[str]`)
- [x] 1.2 Add `parse_errors: list[str] = Field(default_factory=list)` to `ControlFile` model in `src/content_agent/models/control.py`
- [x] 1.3 Export `DiscoveryResult` from `src/content_agent/models/__init__.py`

## 2. Discovery Layer — Detail Methods

- [x] 2.1 `products.py`: Remove `except Exception` from `get_product_details()` and `_load_product_summary()` — keep only not-found checks returning `None`
- [x] 2.2 `profiles.py`: Remove `except Exception` from `get_profile_details()` and `_load_profile_summary()` — keep only not-found checks returning `None`
- [x] 2.3 `rules.py`: Remove `except Exception` from `get_rule_details()` and `_load_search_result()` — keep only not-found checks returning `None`
- [x] 2.4 `rules.py`: Add `logger.warning()` to `_load_rule_yaml()` fallback from SSG expansion to direct YAML loading
- [x] 2.5 `controls.py`: Remove `except Exception` from `_parse_requirement_file()` — let errors propagate
- [x] 2.6 `build_artifacts.py`: Remove `except Exception` from `get_rendered_rule()` rule JSON reading (keep per-component catches for OVAL/remediations)
- [x] 2.7 `templates.py`: Replace `except Exception: pass` blocks in `_extract_description()` and `_get_example_usage()` with `logger.warning()`

## 3. Discovery Layer — List Methods

- [x] 3.1 `products.py`: Change `list_products()` to return `DiscoveryResult[ProductSummary]`, accumulate per-item errors
- [x] 3.2 `profiles.py`: Change `list_profiles()` to return `DiscoveryResult[ProfileSummary]`, accumulate per-item errors
- [x] 3.3 `rules.py`: Change `search_rules()` to return `DiscoveryResult[RuleSearchResult]`, accumulate per-item errors
- [x] 3.4 `controls.py`: Update `parse_control_file()` to accumulate per-requirement errors into `ControlFile.parse_errors` instead of silently skipping

## 4. Public API and Exports

- [x] 4.1 Update module-level functions in `products.py`, `profiles.py`, `rules.py` to return `DiscoveryResult`
- [x] 4.2 Update `src/content_agent/core/discovery/__init__.py` imports

## 5. Handler Layer

- [x] 5.1 Update `list_products` handler in `tools.py` to unpack `DiscoveryResult` and include error warnings in response text
- [x] 5.2 Update `search_rules` handler to unpack `DiscoveryResult` and include error warnings
- [x] 5.3 Update `list_profiles` handler to unpack `DiscoveryResult` and include error warnings
- [x] 5.4 Update `get_control_details` handler to surface `parse_errors` from `ControlFile` in response text
- [x] 5.5 Update internal callers of list methods (e.g., `_get_controls_dirs` calls `list_products()`) to use `.items`

## 6. Tests

- [x] 6.1 Add unit tests for `DiscoveryResult` dataclass
- [x] 6.2 Add unit tests verifying detail methods raise on parse errors (not return `None`)
- [x] 6.3 Add unit tests verifying list methods accumulate errors in `DiscoveryResult.errors`
- [x] 6.4 Add unit tests verifying `ControlFile.parse_errors` is populated for failed requirements
- [x] 6.5 Run full test suite and fix any regressions from changed return types

## 7. Lint and Type Checking

- [x] 7.1 Run `black src/ tests/` and fix formatting
- [x] 7.2 Run `ruff check --fix src/ tests/` and fix lint issues
- [x] 7.3 Run `mypy src/` and fix type errors from changed signatures (no new errors introduced)
