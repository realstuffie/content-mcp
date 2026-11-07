## Why

`get_requirement_file_path` and `update_requirement_rules` looked for a requirement in a file named after it, such as `nist_800_53/ac-2.yml`. Many policies don't work that way:

- NIST 800-53 keeps a whole family in one file, so `ac-2` and `ac-2.1` are both in `ac.yml`. None of the 4 × 1196 NIST requirements could be found or updated.
- Policies without `controls_dir`, such as `cis_ocp_200`, keep their requirements in a directory named after the control file, and their files hold whole sections.
- `srg_gpos` defines `Variables` in `srg_gpos.yml` itself, next to its directory.

At `f09d243`, `get_requirement_file_path` found 14007 of the 19392 requirements that ComplianceAsCode loads across 70 policies. All 5385 misses were in these cases.

## What Changes

- Add `find_requirement_file`: it tries the file named after the requirement, then the control file, then every other file in the policy's requirement directory, searching the text for the requirement's `id`.
- Use it in `get_requirement_file_path` and `update_requirement_rules`.
- When a requirement doesn't exist in a directory-based policy, `get_requirement_file_path` still returns where its file would go, with `exists=false`.
- When `update_requirement_rules` is called without a product for a policy that exists only per product, such as `nist_800_53`, the error lists the products to choose from.

## Non-goals

- Speeding up lookups. Each lookup still validates the product by loading every `product.yml`, about 0.2 seconds; that is a separate change.

## Capabilities

### Modified Capabilities

- `requirement-file-path`: requirements are found in any file of the policy.
- `requirement-rules-update`: the same lookup, and a clearer error for per-product policies.

## Impact

- **Affected code**: `core/discovery/controls.py`, `core/scaffolding/control_updater.py`, `server/handlers/tools.py`.
- **Results** at `f09d243`: `get_requirement_file_path` finds all 19392 requirements the build loads, against 14007 before.
