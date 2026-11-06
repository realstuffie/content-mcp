## 1. Core Implementation

- [x] 1.1 Load product variables from `product.yml` and `product_properties` in `RuleDiscovery._product_substitutions`
- [x] 1.2 Expand with `product=""` when no product is given
- [x] 1.3 Without a product, retry failed rules with a literal `{{{ full_name }}}`, then with each product's variables

## 2. Tests

- [x] 2.1 Unit tests for product variables, an unknown product, and the fallback order without a product
- [x] 2.2 Integration tests for rules that failed to load before, with and without a product

## 3. Quality Checks

- [x] 3.1 Run `mypy src/`
- [x] 3.2 Run `ruff check src/ tests/` and `black --check src/ tests/`
- [x] 3.3 Run the full test suite
