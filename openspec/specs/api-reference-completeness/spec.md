## ADDED Requirements

### Requirement: Build Artifact Tools section
The `docs/api_reference.md` file SHALL contain a "Build Artifact Tools" section under MCP Tools that documents the following 4 tools: `list_built_products`, `get_rendered_rule`, `get_datastream_info`, `search_rendered_content`. Each tool entry SHALL include parameters (name, type, required/optional, default, description), return type description, and at least one JSON example for tools with non-trivial return structures. Parameter documentation SHALL match the `inputSchema` definitions in `src/content_agent/server/handlers/tools.py`.

#### Scenario: Build artifact tools are documented
- **WHEN** a user reads the "Build Artifact Tools" section of `docs/api_reference.md`
- **THEN** all 4 tools (`list_built_products`, `get_rendered_rule`, `get_datastream_info`, `search_rendered_content`) are present with accurate parameter and return type documentation

### Requirement: Control File Tools section
The `docs/api_reference.md` file SHALL contain a "Control File Tools" section under MCP Tools that documents the following 8 tools: `parse_policy_document`, `generate_control_files`, `suggest_rule_mappings`, `validate_control_file`, `review_control_generation`, `list_controls`, `get_control_details`, `search_control_requirements`. Each tool entry SHALL include parameters (name, type, required/optional, default, enum values, description) and return type description. Parameter documentation SHALL match the `inputSchema` definitions in `src/content_agent/server/handlers/tools.py`.

#### Scenario: Control file tools are documented
- **WHEN** a user reads the "Control File Tools" section of `docs/api_reference.md`
- **THEN** all 8 tools are present with accurate parameter and return type documentation

### Requirement: Updated get_rule_details parameters
The `get_rule_details` entry in `docs/api_reference.md` SHALL document the `include_rendered` (boolean, optional, default true), `product` (string, optional), and `rendered_detail` (string, optional, enum ["metadata", "full"], default "metadata") parameters in addition to the existing `rule_id` parameter.

#### Scenario: get_rule_details shows all parameters
- **WHEN** a user reads the `get_rule_details` tool entry
- **THEN** the parameters section lists `rule_id`, `include_rendered`, `product`, and `rendered_detail` with their types, defaults, and descriptions

### Requirement: Every tool in TOOLS list is documented
The `docs/api_reference.md` file SHALL contain an entry for every tool defined in the `TOOLS` list in `src/content_agent/server/handlers/tools.py`. No tool SHALL be omitted.

#### Scenario: Tool count matches
- **WHEN** the number of `#### tool_name` entries under the "MCP Tools" section is counted
- **THEN** it equals the number of tool definitions in the `TOOLS` list in `tools.py`

### Requirement: Consistent formatting
All new tool entries SHALL follow the same formatting pattern as existing entries: `#### tool_name` heading, description paragraph, `**Parameters:**` list (or "None"), `**Returns:**` description, optional `**Example:**` with JSON code block.

#### Scenario: New entries match existing style
- **WHEN** a new tool entry is compared against existing entries like `search_rules` or `generate_rule_boilerplate`
- **THEN** the heading level, parameter format, and returns format are identical in structure
