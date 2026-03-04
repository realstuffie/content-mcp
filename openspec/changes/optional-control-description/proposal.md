## Why

The `ControlRequirement` model requires a `description` field, but upstream ComplianceAsCode control files (e.g., `products/rhel9/controls/cis_rhel9.yml`) don't include `description` on their control entries — they use `title` and `notes` instead. This causes `get_control_stats` and other tools to fail with Pydantic validation errors (302 errors for `cis_rhel9` alone) when parsing real control files.

## What Changes

- Make `ControlRequirement.description` optional (`str | None`, default `None`) in the core data model.
- Update any downstream code that assumes `description` is always present (e.g., `IndexedRequirement.description`, string formatting, comparisons).

## Non-goals

- Changing the upstream YAML format or adding `description` fields to upstream files.
- Refactoring other model fields or the control parsing pipeline.
- Changing the control file resolution logic (it already works correctly).

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `control-stats`: Requirements will parse successfully even without `description`, fixing the tool for product-specific CIS controls.

## Impact

- **Core logic layer**: `models/control.py` — `ControlRequirement` and `IndexedRequirement` models.
- **Discovery layer**: `core/discovery/controls.py` — any code that reads `.description` on parsed requirements.
- **Tests**: Unit tests that construct `ControlRequirement` with `description=...` still work; tests that omit it should now also pass.
