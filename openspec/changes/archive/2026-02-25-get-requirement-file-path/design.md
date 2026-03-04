## Context

Control files in ComplianceAsCode use two storage patterns:

1. **Inline**: All requirements live in `controls/<control_id>.yml` under the `controls:` key (e.g., `anssi.yml`, `hipaa.yml`)
2. **Directory-based**: Parent YAML has a `controls_dir` field, individual requirements are stored in `controls/<controls_dir>/<requirement_id>.yml` (e.g., `srg_gpos.yml` → `controls/srg_gpos/SRG-OS-000001-GPOS-00001.yml`)

Callers (like the `map-controls` workflow) need to know which file to edit for a given requirement. Currently this requires format-detection logic at the call site.

## Goals / Non-Goals

**Goals:**
- Provide a single MCP tool that resolves a requirement's file path regardless of storage format
- Return enough metadata (format type, existence) for callers to decide next steps
- Fit cleanly into the existing discovery layer (read-only, no side effects)

**Non-Goals:**
- Writing or modifying requirement files
- Full YAML parsing of requirement content (only enough to detect format and verify existence)
- Caching or performance optimization (control files are small, accessed infrequently)

## Decisions

### 1. Synchronous implementation

The function reads small YAML files from the local filesystem. There is no I/O that benefits from async. Following the pattern of other discovery functions (e.g., `get_control_details`, `get_control_stats`), this will be a synchronous function. The MCP handler calls it directly — consistent with existing tool handlers in `tools.py`.

### 2. Place in `core/discovery/controls.py`

This is a read-only query about control files, so it belongs in the discovery layer alongside `get_control_details`, `list_controls`, and `get_control_stats`. Adding a new file would be over-engineering for a single function.

### 3. Minimal YAML parsing

For inline format, we need to scan the `controls:` list to verify the requirement exists. We parse the full YAML but only inspect `id` fields — we don't need to load requirement content. For directory format, we just check `controls_dir` and whether the target file exists on disk.

### 4. Return `None` for not-found cases

Consistent with `get_control_details()` and `get_rule_details()` which return `None` when the entity doesn't exist. The MCP handler converts this to a descriptive error message.

## Risks / Trade-offs

- **YAML parsing overhead for inline format**: We load the full YAML to scan for requirement IDs. For large control files this could be slow, but in practice control files are <1MB. → No mitigation needed; acceptable for current scale.
- **Directory-based format returns `exists=False` for missing files**: The requirement might be valid but not yet created. → This is intentional — callers need to know whether to create or edit.

## Architecture Fit

```
MCP Tool (get_requirement_file_path)
  → server/handlers/tools.py (handler)
    → core/discovery/controls.py (business logic)
      → models/control.py (RequirementFilePath model)
        → filesystem (controls/*.yml)
```

New MCP tool definition added to `TOOLS` list in `tools.py`. No changes to resources or prompts.
