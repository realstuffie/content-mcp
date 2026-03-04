## 1. Core Discovery Logic

- [x] 1.1 Add `list_unmapped_requirements(control_id, status_filter) -> list[IndexedRequirement] | None` method to `ControlDiscovery` class in `src/content_agent/core/discovery/controls.py`
- [x] 1.2 Add module-level convenience function `list_unmapped_requirements` in `src/content_agent/core/discovery/controls.py`
- [x] 1.3 Export `list_unmapped_requirements` from `src/content_agent/core/discovery/__init__.py`

## 2. MCP Tool Handler

- [x] 2.1 Add `list_unmapped_requirements` tool definition to `TOOLS` list in `src/content_agent/server/handlers/tools.py`
- [x] 2.2 Add handler case for `list_unmapped_requirements` in `handle_tool_call` in `src/content_agent/server/handlers/tools.py`

## 3. Tests

- [x] 3.1 Create `tests/unit/test_list_unmapped_requirements.py` with test cases: default pending filter, empty rules included, custom status filter, nonexistent control, all mapped, description truncation

## 4. Quality & Docs

- [x] 4.1 Run ruff and black, fix any issues
- [x] 4.2 Add `list_unmapped_requirements` tool to `docs/api_reference.md`
