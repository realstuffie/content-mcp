## 1. Core Implementation

- [ ] 1.1 Replace `_find_section_by_requirement_id()` in `src/content_agent/server/handlers/tools.py` (lines 637-664) with the sibling-collecting version that uses `req_id_pattern` to detect requirement ID headings and concatenates following body sections into the matched section's content

## 2. Tests

- [ ] 2.1 Add unit test: CIS flat-heading document returns body content (Description, Rationale, Audit, Remediation) when filtering by dotted requirement ID like `5.3.2.5`
- [ ] 2.2 Add unit test: sibling collection stops at the next requirement ID heading (e.g., `5.3.3.1` content not included)
- [ ] 2.3 Add unit test: ANSSI R-code format (`R1`, `R34`) is recognized as a requirement ID boundary
- [ ] 2.4 Add unit test: body headings like "Description" and "Rationale" are not mistaken for requirement IDs
- [ ] 2.5 Add unit test: original section object is not mutated when sibling content is collected
- [ ] 2.6 Add unit test: well-structured documents with proper heading hierarchy still work correctly (no regression)

## 3. Quality Checks

- [ ] 3.1 Run `mypy src/` and fix any type errors in the modified function
- [ ] 3.2 Run `ruff check src/ tests/` and `black --check src/ tests/` to ensure lint and format compliance
- [ ] 3.3 Run full test suite (`pytest`) to verify no regressions
