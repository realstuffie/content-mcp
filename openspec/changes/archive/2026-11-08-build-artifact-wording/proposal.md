## Why

`has_build_artifacts` said whether rendered content exists. Its implementation
requires `build/<product>/rules/<rule_id>.json`, even if OVAL or remediation
files exist. The field also omits products with no reported result. A caller
could read its broad name as a check for any artifact or a built datastream.

## What changes

- Describe the per-rule JSON check in the model, tool description, and API reference.
- Distinguish false entries from omitted results.
- Add a test with rendered rule JSON for one product, OVAL and remediation
  files alone for another, and an unbuilt product.

## Capabilities

### Modified capabilities

- `rule-product-availability`: specify what the build artifact flags prove.

## Scope

The field name, check, and response values stay the same. This change clarifies
their meaning. It does not add artifact types to the check.
