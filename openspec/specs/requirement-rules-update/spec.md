## ADDED Requirements

### Requirement: Tool accepts control_id, requirement_id, rules, and optional status
The `update_requirement_rules` MCP tool SHALL accept `control_id` (string, required), `requirement_id` (string, required), `rules` (array of strings, required), and `status` (string, optional, default `"automated"`).

The `status` parameter SHALL only accept the values: `automated`, `partially_automated`, `manual`, `not_applicable`, `pending`.

#### Scenario: Valid call with all parameters
- **WHEN** the tool is called with `control_id="anssi"`, `requirement_id="R1"`, `rules=["rule_a", "rule_b"]`, `status="automated"`
- **THEN** the tool SHALL update the requirement and return a `ControlUpdateResult` with `success=True`

#### Scenario: Call with invalid status
- **WHEN** the tool is called with `status="unknown"`
- **THEN** the tool SHALL return an error result

#### Scenario: Call without status uses default
- **WHEN** the tool is called without a `status` parameter
- **THEN** the tool SHALL use `"automated"` as the default status value

### Requirement: Tool locates correct file for inline format
For control files without a `controls_dir` field, the tool SHALL locate the file at `controls/<control_id>.yml` and find the requirement block by matching `- id: <requirement_id>` within the `controls:` list.

#### Scenario: Inline control file exists
- **WHEN** the tool is called with `control_id="anssi"` and `requirement_id="R1"` and `controls/anssi.yml` exists as an inline file containing requirement `R1`
- **THEN** the tool SHALL update the `rules` and `status` fields within the `R1` block in `controls/anssi.yml`

#### Scenario: Requirement not found in inline file
- **WHEN** the tool is called with a `requirement_id` that does not exist in the inline file
- **THEN** the tool SHALL return a `ControlUpdateResult` with `success=False` and an error message

### Requirement: Tool locates correct file for directory-based format
For control files with a `controls_dir` field, the tool SHALL locate the requirement file at `controls/<controls_dir>/<requirement_id>.yml`.

#### Scenario: Directory-based requirement file exists
- **WHEN** the tool is called with `control_id="srg_gpos"` and `requirement_id="SRG-OS-000001"` and the parent file has `controls_dir: srg_gpos`
- **THEN** the tool SHALL update the `rules` and `status` fields in `controls/srg_gpos/SRG-OS-000001.yml`

#### Scenario: Directory-based requirement file missing
- **WHEN** the tool is called and the requirement file does not exist in the directory
- **THEN** the tool SHALL return a `ControlUpdateResult` with `success=False` and an error message

### Requirement: Tool replaces rules list entirely
The tool SHALL replace the entire `rules` list with the provided rules, not append to existing rules.

#### Scenario: Existing rules replaced
- **WHEN** a requirement has `rules: [existing_rule_a, existing_rule_b]` and the tool is called with `rules=["new_rule"]`
- **THEN** the resulting file SHALL contain only `new_rule` in the rules list

#### Scenario: Empty rules list clears rules
- **WHEN** the tool is called with `rules=[]`
- **THEN** the resulting file SHALL contain `rules: []`

### Requirement: Tool preserves Jinja2 templating
The tool SHALL NOT corrupt Jinja2 syntax (`{{{ ... }}}`, `{% ... %}`) anywhere in the file.

#### Scenario: Jinja2 in same requirement block
- **WHEN** a requirement contains `{{{ full_name }}}` in its description and the tool updates its rules
- **THEN** the Jinja2 expression SHALL remain intact after the update

#### Scenario: Jinja2 in other requirement blocks
- **WHEN** an inline file has multiple requirements and another requirement contains Jinja2
- **THEN** the Jinja2 in the untouched requirement SHALL remain intact

### Requirement: Tool preserves comments and formatting
The tool SHALL preserve YAML comments, multiline scalars (`>-`, `|-`), and existing indentation style throughout the file.

#### Scenario: Comments preserved
- **WHEN** a control file contains YAML comments (lines starting with `#`)
- **THEN** all comments SHALL remain unchanged after the update

#### Scenario: Other requirements unchanged
- **WHEN** an inline file has three requirements and the tool updates the middle one
- **THEN** the first and third requirements SHALL be byte-identical before and after the update

### Requirement: Tool handles quoting variations
The tool SHALL match requirement IDs regardless of YAML quoting style (unquoted `R1`, single-quoted `'R1'`, double-quoted `"R1"`).

#### Scenario: Quoted requirement ID
- **WHEN** the file contains `- id: "R1"` and the tool is called with `requirement_id="R1"`
- **THEN** the tool SHALL find and update the requirement

### Requirement: Tool returns ControlUpdateResult
The tool SHALL return a `ControlUpdateResult` with `file_path`, `requirements_updated=1`, `requirements_added=0`, `requirements_unchanged=0`, `success=True`, and empty `errors` on success.

#### Scenario: Successful result fields
- **WHEN** the tool successfully updates a requirement
- **THEN** `result.file_path` SHALL be the path to the modified file, `result.requirements_updated` SHALL be `1`, and `result.success` SHALL be `True`

#### Scenario: Error result on missing control
- **WHEN** the tool is called with a `control_id` that has no corresponding file
- **THEN** `result.success` SHALL be `False` and `result.errors` SHALL contain a descriptive message

### Requirement: Tool registered as MCP tool
The tool SHALL be registered in the MCP tools list in `server/handlers/tools.py` with the name `update_requirement_rules` and a handler in `handle_tool_call`.

#### Scenario: Tool appears in tool listing
- **WHEN** the MCP server lists available tools
- **THEN** `update_requirement_rules` SHALL be present with its input schema
