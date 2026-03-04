## Why

The `map-controls` skill needs to write selected rules back to control files after an author makes a mapping decision. Currently this relies on `Read` + `Edit` tool calls, requiring the LLM to understand YAML structure and make surgical edits — error-prone, especially for inline control files where multiple requirements share one file and Jinja2 templating must be preserved.

## What Changes

- Add a new `update_requirement_rules` MCP tool that deterministically updates the `rules` list and `status` for a single requirement in a control file
- Support both inline (monolithic YAML) and directory-based (`controls_dir`) control file formats
- Use text-based editing (not `yaml.dump`) to preserve Jinja2 templating (`{{{ ... }}}`), comments, and formatting
- Wire the tool into the MCP handler layer with proper validation and error reporting
- Return `ControlUpdateResult` (model already exists at `models/control.py:368`)

## Non-goals

- Batch updates across multiple requirements in a single call (caller can loop)
- Creating new requirements — this tool only updates existing ones
- Modifying fields other than `rules` and `status`
- Changing the `ControlUpdateResult` model structure

## Capabilities

### New Capabilities
- `requirement-rules-update`: MCP tool to update rules and status for a specific requirement in a control file, with format-aware text-based editing

### Modified Capabilities

## Impact

- **Core logic layer** (`core/scaffolding/`): New `control_updater.py` module
- **MCP protocol layer** (`server/handlers/tools.py`): New tool definition and handler
- **Models**: No changes — uses existing `ControlUpdateResult`
- **Dependencies**: No new dependencies — uses stdlib `re`, `yaml`, and `pathlib`
