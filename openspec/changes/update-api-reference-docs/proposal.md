## Why

The MCP tools API reference (`docs/api_reference.md`) only documents 11 of the 19 tools the server actually exposes. The entire Build Artifacts and Control File tool categories are missing, and `get_rule_details` is documented without its newer parameters. This makes the API reference unreliable for users and AI assistants consuming the MCP server.

## What Changes

- Add **Build Artifact Tools** section documenting 4 tools: `list_built_products`, `get_rendered_rule`, `get_datastream_info`, `search_rendered_content`.
- Add **Control File Tools** section documenting 8 tools: `parse_policy_document`, `generate_control_files`, `suggest_rule_mappings`, `validate_control_file`, `review_control_generation`, `list_controls`, `get_control_details`, `search_control_requirements`.
- Update `get_rule_details` entry to document the `include_rendered`, `product`, and `rendered_detail` parameters added for build artifact integration.
- Add any missing data model definitions referenced by the new tool entries.

## Non-goals

- Changing tool implementations or behavior — this is documentation only.
- Restructuring or rewriting existing documented sections.
- Adding usage tutorials or guides beyond what the current format provides.
- Documenting MCP resources or prompts (those sections are already adequate).

## Capabilities

### New Capabilities

- `api-reference-completeness`: Ensure `docs/api_reference.md` documents every tool defined in `src/content_agent/server/handlers/tools.py`, with accurate parameters, types, and examples.

### Modified Capabilities

_(none — no existing spec-level requirements are changing)_

## Impact

- **Affected file**: `docs/api_reference.md` (MCP protocol layer documentation).
- **No code changes** — purely a documentation update.
- **Source of truth**: `src/content_agent/server/handlers/tools.py` (`TOOLS` list and `handle_tool_call` function).
