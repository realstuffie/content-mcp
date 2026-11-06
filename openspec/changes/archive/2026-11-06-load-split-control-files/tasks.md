## 1. Core Implementation

- [x] 1.1 Read the `controls` list of requirement files
- [x] 1.2 Expand requirement files with Jinja2, with product variables or generic values
- [x] 1.3 Share product variable loading between rules and controls

## 2. Tests

- [x] 2.1 Unit tests for the `controls` list and Jinja2 expansion with and without a product
- [x] 2.2 Integration tests for `srg_gpos` and `nist_800_53`

## 3. Quality Checks

- [x] 3.1 Run `mypy src/`
- [x] 3.2 Run `ruff check src/ tests/` and `black --check src/ tests/`
- [x] 3.3 Run the full test suite
