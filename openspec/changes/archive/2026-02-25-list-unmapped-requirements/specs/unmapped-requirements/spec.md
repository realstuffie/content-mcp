## ADDED Requirements

### Requirement: Filter by pending status by default

The tool SHALL return requirements with `status` matching the filter, defaulting to `["pending"]` when no `status_filter` is provided.

#### Scenario: Default pending filter

- **WHEN** `list_unmapped_requirements(control_id="test")` is called without `status_filter` and the control has requirements with statuses "pending", "automated", and "manual"
- **THEN** only requirements with `status="pending"` are returned

### Requirement: Include empty-rules requirements

The tool SHALL include requirements with an empty rules list regardless of their status, even if the status does not match the filter.

#### Scenario: Automated status but empty rules

- **WHEN** a requirement has `status="automated"` but `rules=[]` and the default filter `["pending"]` is active
- **THEN** the requirement is included in the results

### Requirement: Custom status filter

The tool SHALL accept an optional `status_filter` parameter to override the default. When provided, requirements matching any of the listed statuses (or with empty rules) SHALL be returned.

#### Scenario: Multiple status filter

- **WHEN** `list_unmapped_requirements(control_id="test", status_filter=["manual", "pending"])` is called
- **THEN** requirements with `status="manual"` or `status="pending"` or `rules=[]` are returned

### Requirement: Return None for nonexistent control

The tool SHALL return `None` when the control file does not exist.

#### Scenario: Control not found

- **WHEN** `list_unmapped_requirements(control_id="nonexistent")` is called
- **THEN** the tool returns `None`

### Requirement: Return empty list when all mapped

The tool SHALL return an empty list when the control exists but all requirements are fully mapped and have a non-matching status.

#### Scenario: All requirements mapped

- **WHEN** all requirements have `status="automated"` and non-empty `rules` lists, with the default filter
- **THEN** the tool returns `[]`

### Requirement: Truncate descriptions

The tool SHALL truncate requirement descriptions to 300 characters, consistent with `get_control_rule_index`.

#### Scenario: Long description truncated

- **WHEN** a requirement has a description longer than 300 characters
- **THEN** the returned `IndexedRequirement` has `description` truncated to 300 characters

### Requirement: MCP tool interface

The tool SHALL be exposed as an MCP tool named `list_unmapped_requirements` with required parameter `control_id` (string) and optional parameter `status_filter` (array of strings).

#### Scenario: MCP tool returns results

- **WHEN** the MCP tool is called with a valid `control_id`
- **THEN** the response includes a count summary and JSON array of `IndexedRequirement` objects

#### Scenario: MCP tool returns error for not found

- **WHEN** the MCP tool is called with a nonexistent `control_id`
- **THEN** the response includes a text message indicating the control was not found
