## MODIFIED Requirements

### Requirement: Build cross-framework control rule index
The system SHALL provide a `get_control_rule_index` MCP tool that builds a complete index of all requirements and their rule mappings across all control frameworks. The tool SHALL accept an optional `include_unmapped` boolean (default `true`), an optional `control_ids` string list to filter which frameworks to index, and an optional `product` string to scope discovery to a specific product's controls. The result SHALL include `total_controls`, `total_requirements`, `total_mapped_rules` counts and a list of `IndexedRequirement` objects.

When `product` is provided, the tool SHALL use product-aware discovery to resolve control files (global + product-specific directories with override semantics).

#### Scenario: Index all control frameworks
- **WHEN** `get_control_rule_index` is called with no arguments
- **THEN** the system returns a `ControlRuleIndex` with all control frameworks indexed (from global and all product directories), including requirements with and without rule mappings

#### Scenario: Filter by specific control IDs
- **WHEN** `get_control_rule_index` is called with `control_ids: ["anssi", "cis_rhel9"]`
- **THEN** the system returns a `ControlRuleIndex` containing only requirements from the specified frameworks

#### Scenario: Exclude unmapped requirements
- **WHEN** `get_control_rule_index` is called with `include_unmapped: false`
- **THEN** the system returns only requirements that have at least one rule in their `rules` list

#### Scenario: Control framework not found
- **WHEN** `get_control_rule_index` is called with `control_ids: ["nonexistent"]`
- **THEN** the system returns a `ControlRuleIndex` with `total_controls: 0`, `total_requirements: 0`, and an empty requirements list

#### Scenario: Index scoped to product
- **WHEN** `get_control_rule_index` is called with `product: "rhel9"` and `products/rhel9/controls/` contains product-specific controls
- **THEN** the system returns a `ControlRuleIndex` built from global controls plus rhel9 product-specific controls, with override semantics applied

### Requirement: Flatten nested control structures
The system SHALL recursively flatten nested control structures when building the index. Control files that contain controls with nested sub-controls SHALL have all leaf requirements included in the index with their parent control framework ID preserved.

#### Scenario: Inline nested controls
- **WHEN** a control file has controls containing nested `controls` lists
- **THEN** all leaf-level requirements are included in the index with `control_id` set to the top-level framework ID

#### Scenario: controls_dir pattern
- **WHEN** a control file uses `controls_dir` to reference a subdirectory of individual control YAML files
- **THEN** the requirements from those files are loaded and included in the index

#### Scenario: Requirement files with a controls list
- **WHEN** a file in the `controls_dir` subdirectory holds its requirements in a top-level `controls` list, like the NIST 800-53 family files
- **THEN** every requirement in that list is loaded

#### Scenario: Requirement files with Jinja2
- **WHEN** a requirement file uses Jinja2, such as `{{{ full_name }}}` in a title
- **THEN** the file is expanded with the product's variables when a product is given
- **AND** without a product, it is expanded with an empty product name, no product families, and "The operating system" as `full_name`

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
