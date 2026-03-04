## Why

When working with large policy documents (ANSSI, CIS Benchmarks, STIGs), the `parse_policy_document` tool returns the entire parsed document. AI assistants frequently need only a single requirement section (e.g., "R34" from ANSSI, "1.1.1.1" from CIS). Returning the full document wastes context window and forces downstream filtering. Adding a targeted extraction parameter lets assistants retrieve exactly the section they need in one call.

## What Changes

- Add an optional `requirement_id` parameter to the `parse_policy_document` MCP tool schema
- When `requirement_id` is provided, filter `ParsedDocument.sections` to return only the matching section (and its subsections)
- Add a helper function `_find_section_by_requirement_id` that uses word-boundary-aware regex matching to locate sections by ID in titles, with fallback to content search
- When no match is found, return empty sections with `requirement_not_found` in metadata
- When `requirement_id` is omitted, behavior is completely unchanged

## Non-goals

- Modifying the `ParsedDocument` model or adding new fields to it
- Supporting multi-requirement queries (returning multiple sections at once)
- Changing parser implementations — filtering happens after parsing
- Adding new MCP tools — this extends the existing `parse_policy_document` tool

## Capabilities

### New Capabilities

- `requirement-section-filter`: Word-boundary-aware section filtering for parsed policy documents, supporting requirement ID formats across frameworks (ANSSI R-codes, CIS dotted numbers, STIG IDs)

### Modified Capabilities

## Impact

- **MCP Protocol Layer**: `server/handlers/tools.py` — tool schema gains a new optional parameter; handler gains post-parse filtering logic
- **Core Logic**: No changes to parsers or models — filtering is applied to the existing `ParsedDocument` output
- **API surface**: Backward-compatible addition (optional parameter, no breaking changes)
