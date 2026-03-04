## 1. Core Implementation

- [x] 1.1 Create `src/content_agent/core/scaffolding/control_updater.py` with `ControlUpdater` class and `update_requirement_rules` method
- [x] 1.2 Implement text-based requirement block detection (find `- id: <requirement_id>` line, determine block extent via indentation)
- [x] 1.3 Implement `_format_rules_block` helper to produce YAML rules list at correct indentation
- [x] 1.4 Implement rules/status field replacement within a requirement block (handle existing and missing fields)
- [x] 1.5 Implement directory-based format support (resolve `controls_dir`, locate requirement file, update using same text-based approach)
- [x] 1.6 Add status validation (only accept the 5 valid values)
- [x] 1.7 Add quoting-aware ID matching (`R1`, `"R1"`, `'R1'`)

## 2. MCP Tool Registration

- [x] 2.1 Add `update_requirement_rules` tool definition to `TOOLS` list in `server/handlers/tools.py`
- [x] 2.2 Add handler branch in `handle_tool_call` that instantiates `ControlUpdater` and calls `update_requirement_rules`
- [x] 2.3 Export `ControlUpdater` from `core/scaffolding/__init__.py`

## 3. Tests

- [x] 3.1 Create `tests/unit/test_control_updater.py` with test fixtures for inline and directory-based control files
- [x] 3.2 Add tests for inline format: replace existing rules, add missing rules field, add missing status field
- [x] 3.3 Add tests for directory-based format: update rules and status
- [x] 3.4 Add tests for preservation: Jinja2 templating, YAML comments, other requirements unchanged
- [x] 3.5 Add tests for error cases: nonexistent control, nonexistent requirement, invalid status
- [x] 3.6 Add tests for edge cases: empty rules list, quoted requirement IDs
- [ ] 3.7 Add integration test: update then validate with `ControlValidator`

## 4. Quality and Documentation

- [x] 4.1 Run mypy type checking and fix any type errors
- [x] 4.2 Run black and ruff, fix any formatting/lint issues
- [x] 4.3 Update `docs/api_reference.md` with the new tool
- [x] 4.4 Update the "Available Tools" list in `README.md`
