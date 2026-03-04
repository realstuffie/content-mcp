## Context

The `parse_policy_document` MCP tool parses policy documents (PDF, Markdown, HTML, text) and returns a `ParsedDocument` with a flat or nested list of `DocumentSection` objects. Currently it always returns the entire parsed document.

AI assistants working with compliance frameworks (ANSSI, CIS, STIG) frequently need a single requirement section. They must currently parse the full document and then manually search through the response — wasting context window and adding complexity to the assistant workflow.

The filtering logic lives entirely in the MCP handler layer (`server/handlers/tools.py`). No changes are needed to the core parsing layer or Pydantic models since we filter the already-parsed `ParsedDocument` output.

## Goals / Non-Goals

**Goals:**
- Allow targeted extraction of a single requirement section by ID from any parsed policy document
- Support requirement ID formats across major frameworks: ANSSI R-codes, CIS dotted numbers, STIG IDs
- Use word-boundary-aware matching to prevent partial matches (e.g., "R3" must not match "R34")
- Maintain full backward compatibility — omitting `requirement_id` preserves current behavior

**Non-Goals:**
- Multi-requirement queries (returning several sections at once)
- Modifying `ParsedDocument` or `DocumentSection` models
- Adding filtering to parser implementations — filtering is post-parse only
- Fuzzy or semantic matching of requirement IDs

## Decisions

### 1. Filter in the handler, not in parsers

**Decision**: Apply section filtering after `parser.parse(source)` returns, within the `parse_policy_document` handler in `tools.py`.

**Rationale**: Parsers are document-format-specific (PDF, MD, HTML, text) and shouldn't know about requirement IDs. Filtering the parsed output keeps parsers focused on structural extraction and avoids duplicating filter logic across four parser implementations.

**Alternative considered**: Adding a `requirement_id` parameter to each parser's `parse()` method. Rejected because it couples parsers to compliance domain concepts and requires changes in four places.

### 2. Word-boundary regex matching with content fallback

**Decision**: Use a custom word-boundary regex pattern (`(?<![.\w])` + escaped ID + `(?![.\w])`) that handles dotted IDs (like CIS "1.1.1.1"). Search section titles first, then fall back to section content.

**Rationale**: Standard `\b` word boundaries don't handle dots correctly — "1.1.1" would match inside "1.1.1.1". The custom pattern treats dots as part of the word, preventing partial matches on dotted identifiers. Title-first search works for most frameworks (ANSSI, CIS use headings), while content fallback handles STIG documents that embed IDs in body text.

**Alternative considered**: Simple substring matching. Rejected because "R3" would match "R30", "R31", etc.

### 3. Module-level helper function

**Decision**: Add `_find_section_by_requirement_id` as a private module-level function in `tools.py`, above the handler.

**Rationale**: The function is small (recursive section search) and only used by this one handler. A separate module would be over-engineering for a single function. The underscore prefix signals it's internal.

### 4. Empty sections with metadata on no match

**Decision**: When `requirement_id` doesn't match any section, return the same `ParsedDocument` structure with `sections=[]` and `metadata["requirement_not_found"] = requirement_id`.

**Rationale**: Returning a consistent response structure (rather than an error) lets callers handle the no-match case without exception handling. The metadata field provides actionable feedback about what was searched for.

## Risks / Trade-offs

- **[Risk] Regex pattern may not cover all ID formats** → The pattern handles ANSSI R-codes, CIS dotted numbers, and STIG hyphenated IDs. If new frameworks use unusual delimiters, the pattern may need updating. Mitigation: the pattern is isolated in one function, easy to extend.
- **[Trade-off] Title-first, content-fallback search order** → If a section title contains an unrelated ID that happens to match, it will be returned instead of the correct content match. This is acceptable because policy documents use structured, unique requirement IDs in headings.
- **[Trade-off] Full document is still parsed before filtering** → Parsing the entire document and then discarding sections is not optimal for performance. However, parse results could be cached in the future, and the filtering itself is negligible cost compared to parsing.
