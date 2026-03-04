## Context

The `get_template_schema` tool in the discovery layer returns a `TemplateSchema` with parameter names/types and example usage. The content repo contains a comprehensive reference file at `docs/templates/template_reference.md` with per-template sections (headed by `#### <template_name>`) that include detailed descriptions, parameter explanations with valid values, and supported languages. This documentation is not currently surfaced through the MCP tool.

Current flow:
```
MCP Client → get_template_schema handler → TemplateDiscovery.get_template_schema()
  → reads shared/templates/<name>/ dir → returns TemplateSchema
```

Target flow:
```
MCP Client → get_template_schema handler → TemplateDiscovery.get_template_schema()
  → reads shared/templates/<name>/ dir
  → reads docs/templates/template_reference.md, extracts section for <name>
  → returns TemplateSchema with documentation field populated
```

## Goals / Non-Goals

**Goals:**
- Return the reference documentation for a template as part of `get_template_schema` response.
- Parse `template_reference.md` to extract the section for a specific template by its `#### <name>` heading.
- Keep the documentation as raw markdown text — consumers (AI assistants) can interpret it directly.

**Non-Goals:**
- Structured parsing of documentation into sub-fields (parameter descriptions, language lists).
- Caching or indexing the reference file.
- Modifying the MCP tool handler or adding new tools.

## Decisions

### 1. Add `documentation` field to `TemplateSchema` model

**Choice**: Add an optional `documentation: str | None` field to the existing `TemplateSchema` Pydantic model.

**Rationale**: This is the simplest approach — no new models, no handler changes. The field serializes automatically via `model_dump(mode="json")`. AI consumers get the docs alongside parameters in a single call.

**Alternative considered**: New `TemplateDocumentation` model returned by a separate tool. Rejected — adds MCP tool surface area for something that naturally belongs with the schema.

### 2. Extract documentation by parsing markdown headings

**Choice**: Read `docs/templates/template_reference.md`, find the `#### <template_name>` heading, and extract all content until the next `####` heading.

**Rationale**: The reference file uses a consistent `#### <name>` format. Simple string/line parsing is sufficient — no markdown parsing library needed.

**Alternative considered**: Use a markdown parsing library. Rejected — adds a dependency for a simple heading-based extraction.

### 3. Populate documentation inside `get_template_schema()`

**Choice**: Add a private method `_get_template_documentation(template_name)` to `TemplateDiscovery` and call it from `get_template_schema()`.

**Rationale**: Fits the existing pattern — `get_template_schema` already calls private helpers like `_extract_description` and `_get_example_usage`. No async considerations since all file I/O in the discovery layer uses synchronous `Path` operations.

## Risks / Trade-offs

- **[Reference file missing]** → Return `None` for documentation. The field is optional, so this is a graceful degradation.
- **[Template not in reference file]** → Return `None`. Some templates may be undocumented.
- **[Reference file format changes]** → The `####` heading convention is well-established in the content project. If it changes, the parser returns `None` rather than breaking.
- **[Large documentation sections]** → Some templates have lengthy docs. This is acceptable — the AI consumer benefits from complete context and can summarize as needed.
