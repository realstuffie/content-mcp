## ADDED Requirements

### Requirement: Format parameter is required
The `generate_control_files` MCP tool SHALL accept a `format` parameter with allowed values `"inline"` or `"directory"`. The parameter SHALL be required with no default value.

#### Scenario: Caller passes format as inline
- **WHEN** `format` is `"inline"`
- **THEN** the system generates a single monolithic control file

#### Scenario: Caller passes format as directory
- **WHEN** `format` is `"directory"`
- **THEN** the system generates a parent file and a directory of individual requirement files (existing behavior)

#### Scenario: Caller omits format
- **WHEN** `format` is not provided
- **THEN** the MCP tool returns a validation error indicating `format` is required

### Requirement: Inline format generates a single file
When `format` is `"inline"`, the system SHALL generate a single YAML file at `<output_dir>/<policy_id>.yml` containing policy metadata (`policy`, `title`, `id`, `version`, `source`, `levels`) and all requirements in a `controls` list. The file SHALL NOT contain a `controls_dir` field. No subdirectory SHALL be created.

#### Scenario: Inline generation with three requirements
- **WHEN** `format` is `"inline"` and three requirements are provided
- **THEN** a single file `<policy_id>.yml` is created containing a `controls` list with three entries
- **THEN** no `<policy_id>/` directory is created
- **THEN** the file does not contain a `controls_dir` key

#### Scenario: Inline result shape
- **WHEN** `format` is `"inline"` and generation succeeds
- **THEN** `ControlGenerationResult.parent_file_path` points to the single file
- **THEN** `ControlGenerationResult.requirement_files` is empty
- **THEN** `ControlGenerationResult.total_requirements` equals the number of requirements provided

### Requirement: Inline control items match directory control items
Each control item in the inline `controls` list SHALL have the same structure as the control items written to individual files in directory mode: `id`, `title`, `levels` (if present), `rules` (if present), `status`, `related_rules` (if present), `references` (if present), `notes` (if present).

#### Scenario: Control item field parity
- **WHEN** a requirement with id, title, description, rules, status, and notes is generated in inline mode
- **THEN** the control item in the `controls` list contains `id`, `title`, `rules`, `status`, and `notes` fields with matching values to what directory mode would produce

### Requirement: Existing structure conflict check applies to inline
When `format` is `"inline"`, the system SHALL check if the output file already exists and return an error if so, consistent with directory mode behavior.

#### Scenario: Inline file already exists
- **WHEN** `format` is `"inline"` and `<policy_id>.yml` already exists
- **THEN** generation fails with an error indicating the file already exists

## REMOVED Requirements

### Requirement: nested_by_section parameter
**Reason**: The `nested_by_section` parameter was deprecated and already a no-op. It is removed from both the generator method signature and the MCP tool schema.
**Migration**: Remove any usage of `nested_by_section` — it had no effect.

### Requirement: _group_by_section and _clean_section_id methods
**Reason**: Dead code left from the deprecated nested section feature. Never called.
**Migration**: No migration needed — these were internal methods with no external callers.
