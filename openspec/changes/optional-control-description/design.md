## Context

The `ControlRequirement` Pydantic model (`models/control.py:10`) requires `description: str` as a mandatory field. Upstream ComplianceAsCode control files (especially product-specific CIS benchmarks like `products/rhel9/controls/cis_rhel9.yml`) don't include `description` on their control entries — they use `title` and optionally `notes`. This causes a Pydantic validation error when any tool tries to parse these files through `get_control_details`, which is called by `get_control_stats`, `list_unmapped_requirements`, `get_control_rule_index`, `search_control_requirements`, and others.

The `IndexedRequirement` model (line 306) also has a required `description: str` field that gets populated from `ControlRequirement.description`.

Five locations in `core/discovery/controls.py` reference `req.description`:
- Line 255: text search comparison
- Line 319: truncation for indexing
- Line 536: tokenization for similarity search
- Line 546: populating `IndexedRequirement`
- Line 640: truncation for unmapped listing

## Goals / Non-Goals

**Goals:**
- Make `ControlRequirement.description` optional so upstream control files parse successfully.
- Make `IndexedRequirement.description` optional to match.
- Ensure all downstream `.description` accesses handle `None` safely.

**Non-Goals:**
- Auto-populating `description` from `notes` or `title` as a fallback.
- Changing the YAML parsing logic or control file format.
- Modifying MCP tool definitions or responses.

## Decisions

**Make `description` optional with `None` default** rather than defaulting to empty string.

`None` explicitly signals "not provided" vs. an empty description. The existing code at lines 319 and 640 already handles the `None` case (`req.description[:300] if req.description else ""`), confirming this pattern is expected. Line 255 and 536 need minor guards added.

This fits the models layer only — no changes needed in the MCP handler layer or integration layer.

## Risks / Trade-offs

- [Risk] Code that constructs `ControlRequirement` in tests or scaffolding may rely on `description` being present → Tests will still pass since they explicitly provide `description`; scaffolding generates it from parsed documents where `description` is always extracted.
- [Risk] `IndexedRequirement.description` becoming optional could affect MCP tool response schemas → The field will contain `""` for requirements without descriptions (using `or ""` at the population site), so MCP responses remain unchanged.
