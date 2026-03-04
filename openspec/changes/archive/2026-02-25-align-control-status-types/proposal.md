## Why

The `ControlRequirement.status` field uses a hardcoded Literal type with 5 statuses (`automated`, `partially_automated`, `manual`, `not_applicable`, `pending`) that don't match the upstream ComplianceAsCode control schema (`shared/schemas/control.json`), which defines 10 canonical statuses. This causes Pydantic validation errors when parsing real control files that use statuses like `supported`, `partial`, `documentation`, or `does not meet`.

## What Changes

- **BREAKING**: Replace the `ControlRequirement.status` Literal type with the 10 canonical statuses from the upstream schema: `automated`, `documentation`, `does not meet`, `inherently met`, `manual`, `not applicable`, `partial`, `pending`, `planned`, `supported`
- Remove non-canonical statuses `partially_automated` and `not_applicable`
- Update the default status from `"pending"` to `"pending"` (unchanged — `pending` exists in both sets)
- Update all tests referencing the old status values

## Non-goals

- Changing control file parsing logic beyond the status type
- Adding status validation or migration tooling
- Modifying how `get_control_stats` counts statuses (it already works with any string values)

## Capabilities

### New Capabilities

- `canonical-control-status`: Align ControlRequirement.status with upstream ComplianceAsCode control.json schema statuses

### Modified Capabilities

_None — no existing spec-level requirements are changing._

## Impact

- **Models layer** (`models/control.py`): `ControlRequirement.status` Literal type updated
- **Core logic layer**: No changes — status is treated as an opaque string in counting/indexing logic
- **MCP protocol layer**: No changes — handlers pass through status values
- **Tests**: `test_control_stats.py`, `test_control_models.py` updated for new status values
