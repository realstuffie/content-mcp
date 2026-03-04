## Why

`_find_section_by_requirement_id()` collects sibling sections after the matched heading until `_REQ_ID_PATTERN` detects the next requirement boundary. On CIS RHEL 9 markdown, headings contain HTML `<span>` tags and bold markers (`**`) before the dotted number (e.g., `<span id="page-601-0"></span>**5.3.3 Configure PAM Arguments**`). The current pattern requires start-of-string or whitespace before the number, so `**5.3.3` never matches, the loop never stops, and the tool returns the entire remainder of the document (~1.5 MB) instead of a single requirement section.

## What Changes

- Widen `_REQ_ID_PATTERN` in `src/content_agent/server/handlers/tools.py` to accept common markdown/HTML formatting characters (`*`, `>`, `)`, `]`, `#`) as valid prefix before a dotted requirement number.
- Add test cases covering CIS headings with `<span>` and `**` markers to `tests/unit/test_requirement_section_filter.py`.

## Non-goals

- Refactoring the overall flat-heading sibling collection algorithm.
- Handling requirement ID formats beyond those already supported (dotted numbers, R-codes).
- Addressing false-positive matches on version-like strings (e.g., `2.0.0`) — existing behavior, safe failure mode (stops collection early rather than late).

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `requirement-section-filter`: The boundary-detection pattern must match requirement IDs preceded by markdown bold markers and HTML tag residue, not only by whitespace or start-of-string.

## Impact

- **Core logic layer**: single regex change in `server/handlers/tools.py` (`_REQ_ID_PATTERN`).
- **Tests**: new unit tests in `tests/unit/test_requirement_section_filter.py`.
- No API, dependency, or configuration changes.
