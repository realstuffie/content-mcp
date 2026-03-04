## 1. Model

- [ ] 1.1 Add `ControlStats` Pydantic model to `src/content_agent/models/control.py` with fields: `control_id`, `title`, `total`, `by_status`, `mapped`, `unmapped`
- [ ] 1.2 Export `ControlStats` from `src/content_agent/models/__init__.py`

## 2. Discovery Logic

- [ ] 2.1 Add `get_control_stats` method to `ControlDiscovery` class in `src/content_agent/core/discovery/controls.py`
- [ ] 2.2 Add module-level `get_control_stats` convenience function in the same file
- [ ] 2.3 Export `get_control_stats` from `src/content_agent/core/discovery/__init__.py`

## 3. MCP Tool Registration

- [ ] 3.1 Add `get_control_stats` tool definition to `TOOLS` list in `src/content_agent/server/handlers/tools.py`
- [ ] 3.2 Add `get_control_stats` handler in `handle_tool_call` function in the same file

## 4. Documentation

- [ ] 4.1 Add `get_control_stats` tool entry to `docs/api_reference.md` under the Control File Tools section (after `get_control_details`), following the existing format (description, parameters, returns)
- [ ] 4.2 Add `ControlStats` data model to `docs/api_reference.md` Data Models section with TypeScript-style schema

## 5. Tests

- [ ] 5.1 Create `tests/unit/test_control_stats.py` with test cases: basic stats, empty control, nonexistent control, all mapped, all unmapped, status counting across all 10 canonical statuses (`automated`, `documentation`, `does not meet`, `inherently met`, `manual`, `not applicable`, `partial`, `pending`, `planned`, `supported`), and requirements with no status set

## 6. Verification

- [ ] 6.1 Run `pytest tests/unit/test_control_stats.py -v` and confirm all tests pass
- [ ] 6.2 Run `black --check src/ tests/` and `ruff check src/ tests/` and `mypy src/` to confirm compliance
