## Context

The `parse_policy_document` MCP tool supports filtering by `requirement_id`, handled by `_find_section_by_requirement_id()` in `src/content_agent/server/handlers/tools.py:637-664`. This function searches parsed `DocumentSection` trees for a matching title or content.

CIS benchmark markdown files use level-1 headings (`#`) for both the requirement title and its body parts (Profile Applicability, Description, Rationale, Audit, Remediation). The markdown parser produces a flat list of sibling sections at the same level. When the filter matches the requirement title, it returns only that single section — which has empty content because the next heading immediately follows.

This sits in the MCP tool handler layer, not the core parsing layer. The parser correctly represents the document structure; the issue is that the filter function doesn't account for flat-heading documents.

## Goals / Non-Goals

**Goals:**
- Return complete requirement content (body parts) when filtering by `requirement_id` on flat-heading documents
- Preserve existing behavior for well-structured documents with proper heading hierarchy
- Keep the fix isolated to the filter function — no parser changes

**Non-Goals:**
- Fixing the markdown parser to produce hierarchical sections from flat headings
- Handling new document formats or parser types
- Changing the `DocumentSection` Pydantic model or MCP tool schema

## Decisions

### Decision 1: Collect following siblings in the filter function, not the parser

**Choice**: Modify `_find_section_by_requirement_id()` to collect sibling sections after a match, stopping at the next requirement ID heading.

**Rationale**: The parser correctly represents what's in the document. Changing the parser would risk regressions across all document types. The filter function is the right place because it already knows the user is looking for a specific requirement and can apply domain knowledge about what constitutes "body" vs "next requirement".

**Alternative considered**: Modify `_parse_sections()` in `markdown_parser.py` to detect and re-parent flat headings. Rejected because it would require heuristics about heading content that could misfire on other document formats.

### Decision 2: Use regex pattern to distinguish requirement IDs from body headings

**Choice**: A regex pattern `r"(?:^|\s)(\d+(?:\.\d+){2,}|R\d+)\b"` identifies headings that start new requirements (dotted numeric like `1.2.3` or ANSSI-style `R1`). Any heading that doesn't match this pattern is treated as a body part of the current requirement.

**Rationale**: Requirement IDs follow predictable conventions across CIS (dotted numbers) and ANSSI (R-codes). Body headings like "Description", "Rationale", "Audit" never match these patterns. This heuristic covers the two main policy formats used by the project.

**Alternative considered**: Maintain a list of known body-part heading names. Rejected because it's brittle and locale-dependent.

### Decision 3: Concatenate sibling content into matched section rather than adding subsections

**Choice**: Build a new `DocumentSection` with combined `content` from the matched section plus its body siblings (formatted as `## {title}\n\n{content}`).

**Rationale**: Adding subsections would change the shape of the response for flat-heading documents compared to hierarchical ones. Concatenating into content provides a consistent, self-contained result regardless of document structure. The `##` prefix gives visual structure within the content block.

## Risks / Trade-offs

- **[False positive on body heading]** A heading like "R1 remediation notes" could be misidentified as a new requirement → Mitigation: The regex requires word boundaries and the pattern is conservative. In practice, body headings in CIS/ANSSI docs don't contain requirement IDs.
- **[New document format with different ID patterns]** Future policy formats may use IDs not matching `\d+(\.\d+){2,}|R\d+` → Mitigation: The pattern can be extended. The fallback behavior (returning just the matched section) is no worse than current behavior.
- **[Performance]** Iterating siblings is O(n) over sections → Mitigation: Policy documents have at most ~1000 sections; this is negligible compared to parsing cost.

No async considerations — `_find_section_by_requirement_id()` is a synchronous helper. No MCP tool/resource/prompt definition changes needed.
