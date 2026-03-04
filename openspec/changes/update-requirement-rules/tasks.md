## 1. Core Implementation

- [ ] 1.1 Create `src/content_agent/core/scaffolding/control_updater.py` with `ControlUpdater` class and `update_requirement_rules` method
- [ ] 1.2 Implement text-based requirement block detection (find `- id: <requirement_id>` line, determine block extent via indentation)
- [ ] 1.3 Implement `_format_rules_block` helper to produce YAML rules list at correct indentation
- [ ] 1.4 Implement rules/status field replacement within a requirement block (handle existing and missing fields)
- [ ] 1.5 Implement directory-based format support (resolve `controls_dir`, locate requirement file, update using same text-based approach)
- [ ] 1.6 Add status validation (only accept the 5 valid values)
- [ ] 1.7 Add quoting-aware ID matching (`R1`, `"R1"`, `'R1'`)

## 2. MCP Tool Registration

- [ ] 2.1 Add `update_requirement_rules` tool definition to `TOOLS` list in `server/handlers/tools.py`
- [ ] 2.2 Add handler branch in `handle_tool_call` that instantiates `ControlUpdater` and calls `update_requirement_rules`
- [ ] 2.3 Export `ControlUpdater` from `core/scaffolding/__init__.py`

## 3. Tests

- [ ] 3.1 Create `tests/unit/test_control_updater.py` with test fixtures for inline and directory-based control files
- [ ] 3.2 Add tests for inline format: replace existing rules, add missing rules field, add missing status field
- [ ] 3.3 Add tests for directory-based format: update rules and status
- [ ] 3.4 Add tests for preservation: Jinja2 templating, YAML comments, other requirements unchanged
- [ ] 3.5 Add tests for error cases: nonexistent control, nonexistent requirement, invalid status
- [ ] 3.6 Add tests for edge cases: empty rules list, quoted requirement IDs
- [ ] 3.7 Add integration test: update then validate with `ControlValidator`

## 4. Quality and Documentation

- [ ] 4.1 Run mypy type checking and fix any type errors
- [ ] 4.2 Run black and ruff, fix any formatting/lint issues
- [ ] 4.3 Update `docs/api_reference.md` with the new tool
- [ ] 4.4 Update the "Available Tools" list in `README.md`
