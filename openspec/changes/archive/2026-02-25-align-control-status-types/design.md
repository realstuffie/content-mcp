## Context

The `ControlRequirement.status` Literal type was defined during initial scaffolding with 5 guessed statuses. The upstream ComplianceAsCode project defines 10 canonical statuses in `shared/schemas/control.json`. Real control files use these canonical values, causing Pydantic validation failures when parsed.

## Goals / Non-Goals

**Goals:**
- Align `ControlRequirement.status` with upstream `control.json` schema
- Update all tests referencing removed statuses

**Non-Goals:**
- Adding migration logic for existing generated control files
- Changing any business logic (counting, indexing, searching)

## Decisions

### 1. Direct Literal replacement

Replace the existing 5-value Literal with a 10-value Literal matching the upstream enum exactly. This is a one-line model change.

**Alternative**: Using `str` instead of `Literal` — rejected because it loses compile-time validation and documentation value.

### 2. No backward compatibility shim

The old values `partially_automated` and `not_applicable` are not used in any upstream control files — they were invented during scaffolding. No migration path is needed.

## Risks / Trade-offs

- **Breaking change**: Any locally generated control files using `partially_automated` or `not_applicable` will fail to parse. This is acceptable since these values were never upstream-compatible.
- **Status strings with spaces**: Canonical statuses like `"does not meet"` and `"inherently met"` contain spaces. This is consistent with how they appear in upstream YAML files and the JSON schema.
