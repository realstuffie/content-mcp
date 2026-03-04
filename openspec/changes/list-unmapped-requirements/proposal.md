## Why

The `map-controls` workflow needs to iterate over unmapped requirements, but currently must call `get_control_details` (which returns full content for all requirements) and filter client-side. This wastes tokens and adds complexity at the call site. A focused tool that returns only the work queue is more efficient.

## What Changes

- Add `list_unmapped_requirements` MCP tool that returns requirements needing rule mappings, filtered by status
- Defaults to `pending` status filter, but supports custom filters (e.g., `["pending", "manual", "partial"]`)
- Also includes requirements with empty rules lists regardless of status (catches items marked as a status but not actually mapped)
- Reuses existing `IndexedRequirement` model — no new data models needed

## Non-goals

- Modifying requirements or control files (this is read-only discovery)
- Replacing `get_control_details` — this is a complementary focused query
- Adding new data models (reuses `IndexedRequirement`)

## Capabilities

### New Capabilities

- `unmapped-requirements`: List requirements in a control file that need rule mapping work, filtered by status

### Modified Capabilities

## Impact

- **Core logic layer**: New method in `core/discovery/controls.py` (ControlDiscovery class)
- **MCP protocol layer**: New tool definition and handler in `server/handlers/tools.py`
- **No model changes**: Reuses existing `IndexedRequirement` from `models/control.py`
- **No dependency changes**: Uses only existing internal APIs
