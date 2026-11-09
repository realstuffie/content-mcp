## ADDED Requirements

### Requirement: Rule authoring documentation matches tool discovery

The README and API reference SHALL omit the two rule generators from their
available-tool entries and runnable examples. They SHALL explain that agents
with file access can draft rules directly and submit their YAML to
`validate_rule_yaml`. The documentation SHALL distinguish the retained,
unmaintained internal code from the advertised MCP tools.

#### Scenario: Find a supported rule authoring workflow

- **WHEN** a user reads the available tools or rule authoring examples
- **THEN** the documentation directs them to validate a rule draft
- **AND** it does not present either generator as an advertised MCP tool

## MODIFIED Requirements

### Requirement: Consistent formatting
All new tool entries SHALL follow the same formatting pattern as existing entries: `#### tool_name` heading, description paragraph, `**Parameters:**` list (or "None"), `**Returns:**` description, optional `**Example:**` with JSON code block.

#### Scenario: New entries match existing style
- **WHEN** a new tool entry is compared against existing entries like `search_rules` or `validate_rule_yaml`
- **THEN** the heading level, parameter format, and returns format are identical in structure
