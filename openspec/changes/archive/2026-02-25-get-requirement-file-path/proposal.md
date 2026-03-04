## Why

The `map-controls` workflow needs to edit the correct file when updating a requirement's rule mappings, but control files use two different storage formats (inline monolithic YAML vs. directory-based individual files). Currently the caller must detect the format and resolve paths manually. A dedicated tool eliminates this duplication and provides a single reliable entry point.

## What Changes

- Add `get_requirement_file_path` MCP tool that resolves the filesystem path for a specific requirement in a control file
- Handles both inline (`controls/<id>.yml` with all requirements) and directory-based (`controls_dir` field pointing to individual requirement files) formats
- Returns path, format type, and existence status so callers can decide whether to create or edit

## Non-goals

- Editing or writing requirement files (this is read-only discovery)
- Parsing requirement content — only resolving the file location
- Supporting any format beyond the two established ComplianceAsCode patterns

## Capabilities

### New Capabilities

- `requirement-file-path`: Resolve filesystem path for a control requirement, detecting inline vs. directory-based format

### Modified Capabilities

## Impact

- **Core logic layer**: New function in `core/discovery/controls.py`
- **Models layer**: New `RequirementFilePath` Pydantic model in `models/control.py`
- **MCP protocol layer**: New tool definition and handler in `server/handlers/tools.py`
- **No dependency changes**: Uses only stdlib (`pathlib`, `yaml`) and existing Pydantic
