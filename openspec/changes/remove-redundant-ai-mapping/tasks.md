## 1. Remove `suggest_rule_mappings` MCP tool

- [x] 1.1 Remove the `suggest_rule_mappings` tool definition dict from `TOOLS` list in `src/content_agent/server/handlers/tools.py`
- [x] 1.2 Remove the `elif name == "suggest_rule_mappings"` handler block in `src/content_agent/server/handlers/tools.py`
- [x] 1.3 Remove or update any tests for the `suggest_rule_mappings` handler (search `tests/` for references)

## 2. Update documentation

- [x] 2.1 Remove `suggest_rule_mappings` from `docs/api_reference.md`
- [x] 2.2 Remove `suggest_rule_mappings` from the "Available Tools" list in `README.md`

## 3. Verification

- [x] 3.1 Run `pytest` and confirm all tests pass
- [x] 3.2 Run `black --check src/ tests/ && ruff check src/ tests/ && mypy src/` and confirm no issues
