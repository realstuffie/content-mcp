## ADDED Requirements

### Requirement: Return requirement counts for a control file

The `get_control_stats` MCP tool SHALL accept a `control_id` string parameter and return a `ControlStats` object containing:
- `control_id`: the control framework identifier
- `title`: the control framework title
- `total`: total number of requirements
- `by_status`: a dict mapping each status string to its count. The canonical statuses as defined in the ComplianceAsCode control schema are: `automated`, `documentation`, `does not meet`, `inherently met`, `manual`, `not applicable`, `partial`, `pending`, `planned`, `supported`. Only statuses present in the control file SHALL appear as keys.
- `mapped`: count of requirements with at least one rule
- `unmapped`: count of requirements with an empty rules list

The `ControlStats` model SHALL be a Pydantic v2 `BaseModel` defined in `models/control.py`.

#### Scenario: Control with mixed statuses

- **WHEN** `get_control_stats` is called with a `control_id` whose control file has requirements with statuses `automated`, `pending`, `partial`, and `not applicable`
- **THEN** the response SHALL include `by_status` with keys `automated`, `pending`, `partial`, `not applicable` and correct counts for each, and `total` SHALL equal the sum of all `by_status` values

#### Scenario: Control with all canonical statuses

- **WHEN** `get_control_stats` is called with a control file containing requirements using all 10 canonical statuses (`automated`, `documentation`, `does not meet`, `inherently met`, `manual`, `not applicable`, `partial`, `pending`, `planned`, `supported`)
- **THEN** `by_status` SHALL contain all 10 keys with correct counts

#### Scenario: Control with all requirements mapped

- **WHEN** `get_control_stats` is called and every requirement has at least one rule in its rules list
- **THEN** `mapped` SHALL equal `total` and `unmapped` SHALL equal `0`

#### Scenario: Control with no requirements mapped

- **WHEN** `get_control_stats` is called and no requirement has any rules
- **THEN** `unmapped` SHALL equal `total` and `mapped` SHALL equal `0`

### Requirement: Handle nonexistent control

The tool SHALL return an error message when the requested `control_id` does not correspond to any known control file.

#### Scenario: Unknown control ID

- **WHEN** `get_control_stats` is called with a `control_id` that does not exist
- **THEN** the response SHALL contain a text message `"Control not found: <control_id>"`

### Requirement: Handle empty control file

The tool SHALL return zero counts when a control file exists but contains no requirements.

#### Scenario: Control with no requirements

- **WHEN** `get_control_stats` is called for a control file that has zero requirements
- **THEN** `total`, `mapped`, and `unmapped` SHALL all be `0`, and `by_status` SHALL be an empty dict

### Requirement: Mapped/unmapped consistency

The sum of `mapped` and `unmapped` SHALL always equal `total`.

#### Scenario: Invariant holds for any control file

- **WHEN** `get_control_stats` returns a result for any valid control file
- **THEN** `mapped + unmapped` SHALL equal `total`
