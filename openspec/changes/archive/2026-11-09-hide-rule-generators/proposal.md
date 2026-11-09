## Why

The MCP tool list advertised two rule generators that this fork does not
maintain. `generate_rule_boilerplate` produces output the content build
rejects, and `generate_rule_from_template` is not implemented. Advertising
them lets agents select an unsuitable tool when they can draft rules through
file access and check the YAML with `validate_rule_yaml`.

## What changes

- Omit both generators from `TOOLS`, so `tools/list` no longer advertises them.
- Keep their internal functions and dispatch handlers.
- Keep rule validation, discovery and control-file tools advertised.
- Replace generator entries and examples in the README and API reference with
  rule draft validation, and update the architecture's validation flow.
- Check their absence through an SDK session in the existing discovery test.

## Capabilities

### Modified capabilities

- `mcp-protocol`: omit the two rule generators from tool discovery.
- `api-reference-completeness`: document the advertised tool list and explain
  how to validate a rule drafted through file access.

## Scope

This changes tool discovery, not the generator implementations. It does not
remove the internal functions or handlers, implement rule generation, or
change control-file generation and requirement updates. The catalog has 27
tools after this change, down from 29.

Clients should refresh their tool list after restarting the MCP connection.
Agents that need to author rules can use file access, then submit the draft
to `validate_rule_yaml`.
