## Context

`docs/api_reference.md` was written during early development and covers the original Discovery and Scaffolding tool categories. Since then, two major feature sets were added — Build Artifacts (4 tools) and Control Files (8 tools) — and `get_rule_details` gained three new parameters for build artifact integration. The documentation was never updated to reflect these additions.

The source of truth is `src/content_agent/server/handlers/tools.py`, which defines the `TOOLS` list (tool schemas) and `handle_tool_call` (implementation with return value structure).

## Goals / Non-Goals

**Goals:**
- Document all 19 MCP tools in `docs/api_reference.md` with parameters, types, defaults, and return descriptions matching the existing format.
- Update the `get_rule_details` entry with its `include_rendered`, `product`, and `rendered_detail` parameters.
- Add Data Models section entries for any new return types referenced by new tool documentation (e.g., rendered rule, datastream info, control details).

**Non-Goals:**
- Rewriting or restructuring existing documented sections.
- Adding usage guides or tutorials beyond the existing example style.
- Documenting internal implementation details or async behavior.
- Changes to code, tool definitions, or MCP resource/prompt definitions.

## Decisions

**1. Follow the existing document structure and format exactly.**
The current doc uses `### Category` headings for tool groups and `#### tool_name` entries with Parameters/Returns/Example subsections. New tool categories will follow this same pattern. This avoids a jarring style mismatch and keeps the doc consistent.

Alternative considered: Restructuring into a table-based format. Rejected because it would change existing sections unnecessarily.

**2. Add two new category sections after Scaffolding Tools.**
- `### Build Artifact Tools` (4 tools) — placed after Scaffolding Tools since build artifacts represent a later stage in the workflow (build → inspect).
- `### Control File Tools` (8 tools) — placed last since it represents the newest and most complex feature set.

This ordering follows the natural workflow: discover → scaffold → build → control files.

**3. Derive parameter documentation from the `TOOLS` schema definitions.**
Each tool's `inputSchema` in `tools.py` is the authoritative source for parameter names, types, required status, defaults, enum values, and descriptions. The `handle_tool_call` function provides return value structure context.

**4. Add examples selectively.**
Include JSON examples for tools with non-obvious return structures. Skip verbose examples for tools whose returns are straightforward (e.g., simple lists or validation results similar to existing documented patterns).

## Risks / Trade-offs

- **[Drift]** Documentation may fall out of sync again when new tools are added. → No automated solution in this change; mitigated by noting the source of truth at the top of the doc.
- **[Incomplete models]** Some return types come from Pydantic models not yet documented in the Data Models section. → Add key model definitions; skip deeply nested sub-models to keep the doc manageable.
