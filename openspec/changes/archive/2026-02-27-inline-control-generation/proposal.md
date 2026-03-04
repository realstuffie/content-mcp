## Why

The `generate_control_files` MCP tool always produces a directory-based split format (parent file + directory of individual requirement files). ComplianceAsCode supports both this format and a monolithic inline format where all requirements live in a single YAML file. For small policies, the inline format is simpler to read, review, and manage. Users should be able to choose which format to generate.

## What Changes

- Add a required `format` parameter (`"inline"` or `"directory"`) to `generate_control_files`, forcing the caller to explicitly choose the output format
- Implement inline generation: a single file with all requirements embedded in a `controls:` list, no subdirectory, no `controls_dir` field
- **BREAKING**: Remove the deprecated `nested_by_section` parameter from the MCP tool schema and generator
- Delete dead code: `_group_by_section()` and `_clean_section_id()` methods that were left behind when `nested_by_section` was deprecated
- Delete orphaned tests for the removed methods

## Non-goals

- Changing the validator, updater, reviewer, or discovery layers — they already handle both formats
- Changing the `ControlGenerationResult` model — `requirement_files=[]` with `total_requirements=N` is sufficient for inline
- Adding a default value or auto-selection heuristic for the format parameter

## Capabilities

### New Capabilities
- `inline-control-generation`: Output format selection for control file generation, including the inline (monolithic) generation path

### Modified Capabilities

## Impact

- **Core logic** (`core/scaffolding/control_generator.py`): New inline generation path, removal of dead code and deprecated parameter
- **MCP protocol** (`server/handlers/tools.py`): Tool schema change — new required `format` parameter, removed `nested_by_section`
- **Tests** (`tests/unit/test_control_generator.py`): Deleted orphaned tests, new tests for inline format
- **Breaking**: Any caller relying on `nested_by_section` (already a no-op) or not passing `format` will get a validation error
