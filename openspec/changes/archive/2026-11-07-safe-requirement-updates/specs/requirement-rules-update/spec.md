## MODIFIED Requirements

### Requirement: Tool accepts control_id, requirement_id, rules, and optional status
The `status` parameter SHALL only accept the ComplianceAsCode control statuses listed in the `canonical-control-status` capability, taken from the same definition the control model uses.

#### Scenario: Call with a status name the tool used to accept
- **WHEN** the tool is called with `status="not_applicable"` or `status="partially_automated"`
- **THEN** the tool SHALL return an error that names the status to use instead, `not applicable` or `partial`
- **AND** the file SHALL be unchanged

### Requirement: Tool locates correct file for inline format
The requirement's keys line up with `id`, so the tool SHALL take their indentation from the `id` line, which handles both `- id:` and `-   id:`.

### Requirement: Tool replaces rules list entirely

#### Scenario: Comments inside the rules list
- **WHEN** the existing rules list contains a comment line between items
- **THEN** every old item SHALL be removed, including those after the comment

## ADDED Requirements

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
