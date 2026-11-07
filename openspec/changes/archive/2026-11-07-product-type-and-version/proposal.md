## Why

`list_products` and `get_product_details` reported every product type as `unknown` and no version, because they read `product_type` and `product_version` from `product.yml`, and ComplianceAsCode has no such fields. `get_product_details` also read a `cpe` field that doesn't exist; products list theirs under `cpes`.

## What Changes

- Split the product ID into type and version as `ssg.utils.parse_name` does, with the same pattern, so it works without the `ssg` modules.
- Report the first CPE from `cpes`.

## Capabilities

### New Capabilities

- `product-details`: product type, version, and CPE.

## Impact

- **Affected code**: `core/discovery/products.py`.
- **Results** at `f09d243`: all 40 products get a type and, where the ID has one, a version, matching `ssg.utils.parse_name` for every product; none report `unknown`. Products such as `fedora` and `firefox` have no version in their ID and report none.
