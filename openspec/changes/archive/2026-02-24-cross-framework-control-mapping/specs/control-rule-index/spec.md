## ADDED Requirements

### Requirement: Build cross-framework control rule index
The system SHALL provide a `get_control_rule_index` MCP tool that builds a complete index of all requirements and their rule mappings across all control frameworks. The tool SHALL accept an optional `include_unmapped` boolean (default `true`) and an optional `control_ids` string list to filter which frameworks to index. The result SHALL include `total_controls`, `total_requirements`, `total_mapped_rules` counts and a list of `IndexedRequirement` objects.

#### Scenario: Index all control frameworks
- **WHEN** `get_control_rule_index` is called with no arguments
- **THEN** the system returns a `ControlRuleIndex` with all control frameworks indexed, including requirements with and without rule mappings

#### Scenario: Filter by specific control IDs
- **WHEN** `get_control_rule_index` is called with `control_ids: ["anssi", "cis_rhel9"]`
- **THEN** the system returns a `ControlRuleIndex` containing only requirements from the specified frameworks

#### Scenario: Exclude unmapped requirements
- **WHEN** `get_control_rule_index` is called with `include_unmapped: false`
- **THEN** the system returns only requirements that have at least one rule in their `rules` list

#### Scenario: Control framework not found
- **WHEN** `get_control_rule_index` is called with `control_ids: ["nonexistent"]`
- **THEN** the system returns a `ControlRuleIndex` with `total_controls: 0`, `total_requirements: 0`, and an empty requirements list

### Requirement: Flatten nested control structures
The system SHALL recursively flatten nested control structures when building the index. Control files that contain controls with nested sub-controls SHALL have all leaf requirements included in the index with their parent control framework ID preserved.

#### Scenario: Inline nested controls
- **WHEN** a control file has controls containing nested `controls` lists
- **THEN** all leaf-level requirements are included in the index with `control_id` set to the top-level framework ID

#### Scenario: controls_dir pattern
- **WHEN** a control file uses `controls_dir` to reference a subdirectory of individual control YAML files
- **THEN** the requirements from those files are loaded and included in the index

### Requirement: IndexedRequirement model
The system SHALL define an `IndexedRequirement` Pydantic model with fields: `control_id` (str), `requirement_id` (str), `title` (str), `description` (str, truncated to 300 chars), `rules` (list[str]), `status` (str, default "pending"), `levels` (list[str]).

#### Scenario: Description truncation
- **WHEN** a requirement has a description longer than 300 characters
- **THEN** the `IndexedRequirement.description` field contains only the first 300 characters

### Requirement: ControlRuleIndex model
The system SHALL define a `ControlRuleIndex` Pydantic model with fields: `total_controls` (int), `total_requirements` (int), `total_mapped_rules` (int, count of unique rule IDs), `requirements` (list[IndexedRequirement]).

#### Scenario: Unique rule counting
- **WHEN** the same rule ID appears in multiple requirements across different frameworks
- **THEN** `total_mapped_rules` counts it only once
