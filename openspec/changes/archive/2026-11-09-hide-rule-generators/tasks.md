## Implementation

- [x] Remove `generate_rule_boilerplate` and `generate_rule_from_template` from the advertised tool definitions.
- [x] Retain the internal generator functions and dispatch handlers.
- [x] Update the existing MCP session discovery test to assert both names are absent.
- [x] Update the README, API reference and architecture documentation.
- [x] Record the change and update the current OpenSpec requirements.

## Verification

- [x] Compare the catalog before and after: exactly the two generators removed, with 27 tools remaining.
- [x] Run the MCP protocol and tool-handler tests: 76 passed, with the pre-existing stdio timeout case deselected.
- [x] Check changed Python files with Black and run Ruff, mypy and whitespace checks.
