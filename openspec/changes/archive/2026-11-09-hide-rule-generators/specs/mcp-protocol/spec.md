## ADDED Requirements

### Requirement: Rule authoring tool discovery

The server SHALL omit `generate_rule_boilerplate` and
`generate_rule_from_template` from `tools/list`. Rule validation, discovery
and control-file tools SHALL remain advertised. The internal generator
functions and dispatch handlers SHALL remain in place.

#### Scenario: Discover tools for rule authoring

- **WHEN** a client lists tools through an MCP session
- **THEN** neither rule generator appears in the result
- **AND** `validate_rule_yaml`, `validate_control_file` and
  `update_requirement_rules` remain available in the tool list

#### Scenario: Internal generator code is retained

- **WHEN** the advertised generator definitions are removed
- **THEN** the internal generator functions and dispatch handlers remain
- **AND** the change does not implement or repair those generators
