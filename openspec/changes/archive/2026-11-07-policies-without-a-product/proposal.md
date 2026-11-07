## Why

Without a product, control tools resolved a policy by scanning the global directory and then every product's, and used the last file found. For `nist_800_53`, which fedora, rhel8, rhel9 and rhel10 each define with no global file, that meant rhel9's file, silently: `get_control_details("nist_800_53")` returned RHEL 9's mappings with nothing saying so, and the rule index and similarity search across all policies included only RHEL 9's NIST. The same rule would also have let a product's override replace a global policy for every caller, though no policy at `f09d243` has both.

## What Changes

- Without a product, use the global file when there is one. A policy only one product defines resolves to that product's file, expanded with its variables. A policy several products define raises `AmbiguousControlError`, which names the products, so single-policy tools ask for a product.
- `get_control_rule_index` and `find_similar_requirements` include each product's version of such a policy, and their results carry `product`.
- `search_control_requirements` without a product or policy leaves such policies out, since its results don't name their policy, and lists them in the result.

## Capabilities

### Modified Capabilities

- `per-product-control-discovery`: resolution without a product, and the `product` field on indexed and similar requirements.

## Impact

- **Affected code**: `core/discovery/controls.py`, `models/control.py`, `server/handlers/tools.py`.
- **Results** at `f09d243`: `nist_800_53` is the only policy several products define; 18 others belong to one product and still resolve without one. Without a product, the rule index now has 72 control file versions and 19756 requirements, against 69 and 16168, with all four NIST versions tagged by product. Profile resolution and updates are unchanged, since they always pass a product or use only the global directory.
