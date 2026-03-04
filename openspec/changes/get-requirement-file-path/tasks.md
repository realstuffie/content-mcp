## 1. Model

- [ ] 1.1 Add `RequirementFilePath` Pydantic model to `src/content_agent/models/control.py` with fields: `control_id` (str), `requirement_id` (str), `file_path` (Path), `format` (Literal["inline", "directory"]), `exists` (bool)
- [ ] 1.2 Export `RequirementFilePath` from `src/content_agent/models/__init__.py`

## 2. Core Discovery Logic

- [ ] 2.1 Add `get_requirement_file_path(control_id, requirement_id) -> RequirementFilePath | None` method to `ControlDiscovery` class in `src/content_agent/core/discovery/controls.py`
- [ ] 2.2 Add module-level convenience function `get_requirement_file_path` in `src/content_agent/core/discovery/controls.py`
- [ ] 2.3 Export `get_requirement_file_path` from `src/content_agent/core/discovery/__init__.py`

## 3. MCP Tool Handler

- [ ] 3.1 Add `get_requirement_file_path` tool definition to `TOOLS` list in `src/content_agent/server/handlers/tools.py`
- [ ] 3.2 Add handler case for `get_requirement_file_path` in `handle_tool_call` in `src/content_agent/server/handlers/tools.py`

## 4. Tests

- [ ] 4.1 Create `tests/unit/test_requirement_file_path.py` with test cases: inline found, directory found, directory missing file, nonexistent control, nonexistent inline requirement, path is absolute

## 5. Quality & Docs

- [ ] 5.1 Run mypy and ruff, fix any issues
- [ ] 5.2 Add `get_requirement_file_path` tool and `RequirementFilePath` model to `docs/api_reference.md`
