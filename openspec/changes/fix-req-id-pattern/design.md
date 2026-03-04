## Context

`_find_section_by_requirement_id()` in `server/handlers/tools.py` uses `_REQ_ID_PATTERN` as a boundary detector when collecting sibling sections for flat-heading CIS documents. After finding the matched requirement heading, it iterates over subsequent siblings and stops when the pattern detects the next requirement's dotted number. The pattern currently requires start-of-string or whitespace before the number (`(?:^|\s)`), but CIS RHEL 9 markdown headings embed HTML `<span>` tags and bold markers before the number, so the boundary is never detected and the entire document remainder is returned.

This is a single-regex fix in the core logic layer. No MCP tool/resource/prompt definitions change. No async considerations apply — the pattern is used synchronously within a list iteration.

## Goals / Non-Goals

**Goals:**
- `_REQ_ID_PATTERN` matches requirement IDs preceded by markdown formatting characters (`*`, `>`, `)`, `]`, `#`) in addition to whitespace and start-of-string.
- Sibling collection correctly stops at the next requirement boundary in CIS documents with formatted headings.

**Non-Goals:**
- Restructuring the sibling-collection algorithm.
- Supporting new requirement ID formats beyond dotted numbers and R-codes.
- Eliminating false positives on version-like strings (existing safe behavior).

## Decisions

**Extend the prefix character class instead of rewriting the pattern.**

The current pattern `(?:^|\s)(\d+(?:\.\d+){2,}|R\d+)\b` uses an alternation for prefix. The fix changes this to a character class `(?:^|[\s*>)\]#])` which is a minimal, readable change that covers observed CIS formatting. Alternative considered: a lookbehind assertion (`(?<=\*\*)`) — rejected because it would be format-specific and fragile against future markdown variations. The character class approach is more permissive and handles multiple formatting patterns at once.

## Risks / Trade-offs

**[Slightly more permissive matching]** → The wider character class could match dotted numbers after `*`, `>`, etc. in prose. Mitigation: the pattern is only used as a boundary detector in the sibling loop — a false positive stops collection early (returns less content), which is a safe failure mode compared to the current bug (returns too much content).
