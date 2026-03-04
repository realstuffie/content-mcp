## 1. Tool Schema

- [ ] 1.1 Add `requirement_id` optional string parameter to `parse_policy_document` tool schema in `server/handlers/tools.py` (~line 307)

## 2. Core Implementation

- [ ] 2.1 Add `_find_section_by_requirement_id` helper function in `server/handlers/tools.py` with word-boundary regex matching and title-first/content-fallback search
- [ ] 2.2 Add filtering logic to `parse_policy_document` handler (~line 810) to filter sections when `requirement_id` is provided, and set `requirement_not_found` metadata when no match

## 3. Tests

- [ ] 3.1 Add unit tests for `_find_section_by_requirement_id`: title match, content fallback match, no-match, partial-match prevention (R3 vs R34, 1.1.1 vs 1.1.1.1), case-insensitive matching
- [ ] 3.2 Add unit tests for handler filtering: requirement_id provided with match, requirement_id with no match (empty sections + metadata), requirement_id omitted (unchanged behavior)

## 4. Quality

- [ ] 4.1 Run linting (`black --check`, `ruff check`) and fix any issues
- [ ] 4.2 Run type checking (`mypy src/`) and fix any type errors
- [ ] 4.3 Run full test suite (`pytest`) and verify all tests pass

## 5. Documentation

- [ ] 5.1 Update `docs/api_reference.md` with the new `requirement_id` parameter for `parse_policy_document`
- [ ] 5.2 Update the "Available Tools" list in `README.md` to reflect the new parameter
