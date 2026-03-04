## 1. Remove `suggest_rule_mappings` MCP tool

- [ ] 1.1 Remove the `suggest_rule_mappings` tool definition dict from `TOOLS` list in `src/content_agent/server/handlers/tools.py`
- [ ] 1.2 Remove the `elif name == "suggest_rule_mappings"` handler block in `src/content_agent/server/handlers/tools.py`
- [ ] 1.3 Remove or update any tests for the `suggest_rule_mappings` handler (search `tests/` for references)

## 2. Update documentation

- [ ] 2.1 Remove `suggest_rule_mappings` from `docs/api_reference.md`
- [ ] 2.2 Remove `suggest_rule_mappings` from the "Available Tools" list in `README.md`

## 3. Verification

- [ ] 3.1 Run `pytest` and confirm all tests pass
- [ ] 3.2 Run `black --check src/ tests/ && ruff check src/ tests/ && mypy src/` and confirm no issues
