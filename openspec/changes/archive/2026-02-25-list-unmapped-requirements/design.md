## Context

The `map-controls` workflow iterates over unmapped requirements to suggest rule mappings. Currently it must call `get_control_details` (returns everything) and filter. This tool provides a focused query returning only the work queue.

The `IndexedRequirement` model already exists with the right shape: `control_id`, `requirement_id`, `title`, `description`, `rules`, `status`, `levels`.

## Goals / Non-Goals

**Goals:**
- Provide a lightweight MCP tool that returns only requirements needing mapping
- Support configurable status filtering with a sensible default (`["pending"]`)
- Catch requirements that have a status set but empty rules lists

**Non-Goals:**
- Full-text search within requirements (use `search_control_requirements` for that)
- Creating new data models (reuse `IndexedRequirement`)
- Pagination (control files are small enough to return all matches)

## Decisions

### 1. Reuse IndexedRequirement model

`IndexedRequirement` already has the exact fields needed (control_id, requirement_id, title, description, rules, status, levels). No new model avoids duplication. Description truncated to 300 chars consistent with `get_control_rule_index`.

### 2. Filter logic: status OR empty rules

A requirement is "unmapped" if either:
- Its status matches the filter (default: `["pending"]`), OR
- Its rules list is empty (regardless of status)

This catches edge cases where a requirement has been marked with a status (e.g., "automated") but no rules were actually mapped.

### 3. Synchronous, in discovery layer

Follows the same pattern as `get_control_stats`, `get_requirement_file_path`, and other discovery functions. Synchronous, returns `None` for not-found control.

### 4. Return None vs empty list

Returns `None` when control file doesn't exist (consistent with other discovery functions). Returns empty list `[]` when control exists but all requirements are mapped.

## Risks / Trade-offs

- **Loads full control file**: Same as other discovery functions — parses the full YAML to filter. Acceptable for current scale (<1MB files).

## Architecture Fit

```
MCP Tool (list_unmapped_requirements)
  → server/handlers/tools.py (handler)
    → core/discovery/controls.py (business logic)
      → models/control.py (IndexedRequirement — existing)
        → filesystem (controls/*.yml)
```

New MCP tool definition added to `TOOLS` list. No changes to resources or prompts.
