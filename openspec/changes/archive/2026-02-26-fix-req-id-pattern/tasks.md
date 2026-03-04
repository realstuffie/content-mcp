## 1. Fix the Pattern

- [x] 1.1 Update `_REQ_ID_PATTERN` in `src/content_agent/server/handlers/tools.py` (line 637) to use the character class `(?:^|[\s*>)\]#])` instead of `(?:^|\s)`

## 2. Add Tests

- [x] 2.1 Add `test_req_id_pattern_matches_through_bold_markers` to `tests/unit/test_requirement_section_filter.py` — verify `_REQ_ID_PATTERN` matches IDs preceded by `**`, `*`, and existing formats (start-of-string, whitespace, R-codes)
- [x] 2.2 Add `test_flat_heading_cis_with_span_and_bold_markers` to `tests/unit/test_requirement_section_filter.py` — verify `_find_section_by_requirement_id` stops collection at the next requirement when headings contain `<span>` and `**` markers

## 3. Verify

- [x] 3.1 Run `pytest tests/unit/test_requirement_section_filter.py -v` — all tests pass
- [x] 3.2 Run `black --check src/ tests/ && ruff check src/ tests/` — no lint or formatting errors
- [x] 3.3 Run `mypy src/` — no new type errors
