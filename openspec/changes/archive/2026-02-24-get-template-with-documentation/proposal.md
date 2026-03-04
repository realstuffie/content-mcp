## Why

The `get_template_schema` MCP tool returns parameter names and types but lacks the rich documentation available in `docs/templates/template_reference.md` in the content repo. That reference file contains detailed descriptions, parameter explanations, usage notes, and supported languages for every template. Without this context, AI assistants must guess how parameters work and what values are valid, leading to incorrect rule generation.

## What Changes

- Extend `get_template_schema` to parse the relevant section from `docs/templates/template_reference.md` and include it in the response.
- Add a `documentation` field to the `TemplateSchema` model to carry the extracted reference text.
- Add a method to `TemplateDiscovery` that reads and extracts per-template documentation from the reference file.

## Non-goals

- Modifying `list_templates` — it stays lightweight.
- Implementing template-based rule generation (Phase 3).
- Parsing or restructuring the reference markdown into structured sub-fields (parameters, languages, etc.) — the raw section text is sufficient context for AI consumers.

## Capabilities

### New Capabilities
- `template-documentation`: Extract and return per-template documentation from the content repo's `docs/templates/template_reference.md` alongside the existing parameter schema.

### Modified Capabilities

_(none)_

## Impact

- **Core logic** (`core/discovery/templates.py`): New method to parse `template_reference.md` and extract the section for a given template.
- **Models** (`models/profile.py`): Add optional `documentation` field to `TemplateSchema`.
- **MCP protocol** (`server/handlers/tools.py`): No handler changes needed — the enriched model is returned automatically.
- **No breaking changes**: `documentation` is an optional field added to the existing response.
- **No new dependencies**.
