## MODIFIED Requirements

### Requirement: Tool accepts control_id, requirement_id, rules, and optional status
The `update_requirement_rules` MCP tool SHALL accept `control_id` (string, required), `requirement_id` (string, required), `rules` (array of strings, required), `status` (string, optional, default `"automated"`), and `product` (string, optional).

The `status` parameter SHALL only accept the ComplianceAsCode control statuses listed in the `canonical-control-status` capability, taken from the same definition the control model uses.

When `product` is provided, the tool SHALL resolve the control file using product-aware discovery (searching `controls/` then `products/<product>/controls/`, with the product-specific file taking precedence).

#### Scenario: Valid call with all parameters
- **WHEN** the tool is called with `control_id="anssi"`, `requirement_id="R1"`, `rules=["rule_a", "rule_b"]`, `status="automated"`
- **THEN** the tool SHALL update the requirement and return a `ControlUpdateResult` with `success=True`

#### Scenario: Call with invalid status
- **WHEN** the tool is called with `status="unknown"`
- **THEN** the tool SHALL return an error result

#### Scenario: Call with a status name the tool used to accept
- **WHEN** the tool is called with `status="not_applicable"` or `status="partially_automated"`
- **THEN** the tool SHALL return an error that names the status to use instead, `not applicable` or `partial`
- **AND** the file SHALL be unchanged

#### Scenario: Call without status uses default
- **WHEN** the tool is called without a `status` parameter
- **THEN** the tool SHALL use `"automated"` as the default status value

#### Scenario: Update product-specific control file
- **WHEN** the tool is called with `control_id="cis_rhel9"`, `requirement_id="1.1.1"`, `rules=["rule_x"]`, `product="rhel9"` and `cis_rhel9.yml` exists in `products/rhel9/controls/`
- **THEN** the tool SHALL update the requirement in `products/rhel9/controls/cis_rhel9.yml` (or its controls_dir subdirectory)

### Requirement: Tool locates correct file for inline format
For control files without a `controls_dir` field, the tool SHALL locate the file using product-aware path resolution and find the requirement block by matching `- id: <requirement_id>` within the `controls:` list. The requirement's keys line up with `id`, so the tool SHALL take their indentation from the `id` line, which handles both `- id:` and `-   id:`.

#### Scenario: Inline control file exists
- **WHEN** the tool is called with `control_id="anssi"` and `requirement_id="R1"` and `controls/anssi.yml` exists as an inline file containing requirement `R1`
- **THEN** the tool SHALL update the `rules` and `status` fields within the `R1` block in `controls/anssi.yml`

#### Scenario: Requirement not found in inline file
- **WHEN** the tool is called with a `requirement_id` that does not exist in the inline file
- **THEN** the tool SHALL return a `ControlUpdateResult` with `success=False` and an error message

### Requirement: Tool locates correct file for directory-based format
For control files with a `controls_dir` field, the tool SHALL locate the requirement file relative to the control file's parent directory (which may be in `controls/` or `products/<product>/controls/`).

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

#### Scenario: Comments inside the rules list
- **WHEN** the existing rules list contains a comment line between items
- **THEN** every old item SHALL be removed, including those after the comment

#### Scenario: Empty rules list clears rules
- **WHEN** the tool is called with `rules=[]`
- **THEN** the resulting file SHALL contain `rules: []`

### Requirement: Tool changes only the requirement's own rules and status
The tool SHALL change only the `rules` and `status` keys at the requirement's own indentation. Keys of nested requirements and text inside block scalars SHALL be left unchanged. When the requirement has no `rules` or `status` key, the tool SHALL add it before the requirement's nested `controls` list if it has one, and otherwise at the end of the requirement. Blank lines after the requirement SHALL be kept.

#### Scenario: Parent requirement with nested requirements
- **WHEN** the tool updates requirement `1.2`, which has nested requirements `1.2.1` and `1.2.2` with their own rules and statuses
- **THEN** only the rules and status of `1.2` SHALL change

#### Scenario: Requirement files with wide list indentation
- **WHEN** a `srg_gpos` requirement file uses `-   id:` with keys four columns after the dash
- **THEN** the updated file SHALL load with ComplianceAsCode's `ControlsManager`

#### Scenario: Status text inside a description
- **WHEN** a requirement's block scalar description contains a line starting with `status:`
- **THEN** the description SHALL be unchanged

### Requirement: Tool checks the edit before writing
The tool SHALL parse the file before and after the edit, expanding Jinja2 the way control discovery does, and SHALL write the file only when the only difference is the requirement's `rules` and `status`. Otherwise it SHALL return `success=False` and leave the file unchanged. When the original file does not parse, the tool SHALL write the edit and return a warning that it could not be checked.

#### Scenario: Edit that would break the file
- **WHEN** the edited text would not parse
- **THEN** the tool SHALL return an error and the file SHALL be unchanged

#### Scenario: Edit that would change another requirement
- **WHEN** the edited text changes anything besides the requirement's rules and status
- **THEN** the tool SHALL return an error and the file SHALL be unchanged

### Requirement: Tool refuses requirements it can't edit safely
The tool SHALL refuse to edit a requirement, and leave the file unchanged, when its rules list contains Jinja2 statements such as `{{% if %}}`, when it has more than one `rules` or `status` key, or when a Jinja2 statement splits the requirement. Replacing such a list would drop product-specific rules.

#### Scenario: Rules selected per product
- **WHEN** the rules of `SRG-OS-000366-GPOS-00153` are wrapped in `{{% if 'ubuntu' in product %}}` blocks
- **THEN** the tool SHALL return an error asking for a manual edit

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
The tool SHALL return a `ControlUpdateResult` with `file_path`, `requirements_updated=1`, `requirements_added=0`, `requirements_unchanged=0`, `success=True`, and empty `errors` on success. Problems that did not stop the update, such as an unchecked edit, SHALL be listed in `warnings`.

#### Scenario: Successful result fields
- **WHEN** the tool successfully updates a requirement
- **THEN** `result.file_path` SHALL be the path to the modified file, `result.requirements_updated` SHALL be `1`, and `result.success` SHALL be `True`

#### Scenario: Error result on missing control
- **WHEN** the tool is called with a `control_id` that has no corresponding file
- **THEN** `result.success` SHALL be `False` and `result.errors` SHALL contain a descriptive message

### Requirement: Tool registered as MCP tool
The tool SHALL be registered in the MCP tools list in `server/handlers/tools.py` with the name `update_requirement_rules` and a handler in `handle_tool_call`. The tool schema SHALL include an optional `product` string parameter.

#### Scenario: Tool appears in tool listing
- **WHEN** the MCP server lists available tools
- **THEN** `update_requirement_rules` SHALL be present with its input schema including the `product` parameter
