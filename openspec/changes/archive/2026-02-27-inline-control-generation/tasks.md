## 1. Dead Code Cleanup

- [x] 1.1 Remove `nested_by_section` parameter from `ControlGenerator.generate_control_structure()` and its docstring
- [x] 1.2 Delete `_group_by_section()` and `_clean_section_id()` methods from `ControlGenerator`
- [x] 1.3 Delete `test_group_by_section` and `test_clean_section_id` tests from `tests/unit/test_control_generator.py`
- [x] 1.4 Remove `nested_by_section` from the MCP tool schema in `server/handlers/tools.py` and its usage in the handler

## 2. Core Implementation

- [x] 2.1 Extract `_build_control_item()` private method from `generate_requirement_file()` to build the control item dict without writing to file
- [x] 2.2 Add `format: Literal["inline", "directory"]` parameter to `generate_control_structure()`
- [x] 2.3 Implement `_generate_inline_file()` private method that writes a single YAML file with metadata and all requirements in a `controls` list
- [x] 2.4 Add format branching in `generate_control_structure()`: call existing directory logic for `"directory"`, call `_generate_inline_file()` for `"inline"`

## 3. MCP Tool Schema

- [x] 3.1 Add `format` property (`"inline"` or `"directory"`) to `generate_control_files` tool schema and add it to `required` list
- [x] 3.2 Update the handler to pass `format` through to `generate_control_structure()`

## 4. Tests

- [x] 4.1 Add test for inline generation: single file created, no subdirectory, `controls` list present, no `controls_dir` field
- [x] 4.2 Add test for inline result shape: `requirement_files` is empty, `total_requirements` matches input count
- [x] 4.3 Add test for inline conflict detection: error when file already exists
- [x] 4.4 Add test for directory format still works as before (regression)
- [x] 4.5 Run linting (`black --check`, `ruff check`, `mypy`) and fix any issues

## 5. Documentation

- [x] 5.1 Update `docs/api_reference.md` to reflect the new `format` parameter and removal of `nested_by_section`
- [x] 5.2 Update the "Available Tools" list in `README.md` if `generate_control_files` description changed
