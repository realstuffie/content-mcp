## ADDED Requirements

### Requirement: Accept all canonical control statuses

The `ControlRequirement.status` field SHALL accept exactly the 10 statuses defined in the upstream ComplianceAsCode `shared/schemas/control.json`:

- `automated`
- `documentation`
- `does not meet`
- `inherently met`
- `manual`
- `not applicable`
- `partial`
- `pending`
- `planned`
- `supported`

The default value SHALL remain `"pending"`.

#### Scenario: Parse control file with all canonical statuses

- **WHEN** a control YAML file contains requirements using each of the 10 canonical statuses
- **THEN** `parse_control_file` SHALL successfully parse all requirements without validation errors

#### Scenario: Reject unknown status values

- **WHEN** a `ControlRequirement` is constructed with a status value not in the canonical list (e.g., `"partially_automated"`)
- **THEN** Pydantic SHALL raise a validation error

## REMOVED Requirements

### Requirement: Remove non-canonical statuses

The following non-canonical status values SHALL no longer be accepted:

- `partially_automated` (replaced by `partial`)
- `not_applicable` (replaced by `not applicable`)
