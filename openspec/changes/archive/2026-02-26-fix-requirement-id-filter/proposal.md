## Why

`parse_policy_document` returns empty `content` and no `subsections` when filtering by `requirement_id` on CIS benchmark documents that use flat level-1 headings for everything (requirement title, Profile Applicability, Description, Rationale, Audit, Remediation). The sibling body sections are never collected because all headings are at the same level, making the feature unusable for CIS benchmarks — the most common policy format.

## What Changes

- Modify `_find_section_by_requirement_id()` in the MCP tools handler to collect following sibling sections that belong to the matched requirement (stopping at the next requirement ID heading)
- Add a heuristic pattern to distinguish requirement-ID headings from body-part headings (e.g., "Description", "Rationale")

## Non-goals

- Changing the markdown parser's heading-level logic — the flat-heading structure is a document quirk, not a parser bug
- Supporting new document formats or parsers
- Modifying full-document parsing behavior (only the requirement_id filter path changes)

## Capabilities

### New Capabilities

- `flat-heading-sibling-collection`: When a requirement is matched by title in a flat-heading document, collect following sibling sections (up to the next requirement ID) into the matched section's content

### Modified Capabilities

- `requirement-section-filter`: The filtered response for CIS-style flat-heading documents must now include the body content (Description, Rationale, Audit, Remediation) that follows the matched requirement heading

## Impact

- **Affected code**: `src/content_agent/server/handlers/tools.py` — `_find_section_by_requirement_id()` function (core logic layer, MCP tool handler)
- **APIs**: No schema changes; same `parse_policy_document` tool interface, same `ParsedDocument` response model
- **Dependencies**: None — uses only `re` stdlib
- **Risk**: Low — change is isolated to the requirement_id filter path; full-document parsing is untouched
