## Why

When the `map-controls` skill needs to summarize control file state, it calls `get_control_details` and then counts requirements by status. LLMs are unreliable at counting, leading to incorrect summaries. A dedicated tool that returns pre-computed counts eliminates this class of errors.

## What Changes

- Add a new `get_control_stats` MCP tool that returns deterministic requirement counts for a control file
- Counts are broken down by status (`automated`, `pending`, `manual`, etc.), plus `mapped`/`unmapped` tallies
- Returns a compact summary instead of transferring full requirement data

## Non-goals

- Modifying the existing `get_control_details` tool
- Adding filtering or aggregation across multiple control files
- Changing the control file format or storage

## Capabilities

### New Capabilities

- `control-stats`: Read-only MCP tool that computes and returns requirement statistics (total, by-status, mapped, unmapped) for a given control file

### Modified Capabilities

_None — this is a new read-only tool with no changes to existing capabilities._

## Impact

- **Core logic layer** (`core/discovery/controls.py`): New `get_control_stats` method on `ControlDiscovery` and module-level convenience function
- **Models layer** (`models/control.py`): New `ControlStats` Pydantic model
- **MCP protocol layer** (`server/handlers/tools.py`): New tool definition and handler
- **Documentation** (`docs/api_reference.md`): New tool entry and `ControlStats` data model
- **Dependencies**: None — uses only existing internal APIs
