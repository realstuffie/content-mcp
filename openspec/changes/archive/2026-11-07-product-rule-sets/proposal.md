## Why

The build loads a product's rules from its `benchmark_root` and any `additional_content_directories`, skipping rules marked `documentation_complete: false`, and then drops every other rule from control selections (`ControlsManager.remove_selections_not_known`). The server kept them. Control files are shared between products, so at `f09d243` the profile index had 771 entries for rules a product's build never includes. For example, the `ocp4` STIG profiles counted Linux audit rules such as `audit_access_failed` from `linux_os/guide`, though `ocp4` reads its rules from `applications`, and the `rhcos4` profiles counted 365 OpenShift rules the other way round.

## What Changes

- Add `product_rule_directories` and `product_rule_ids`, which find the rules a product's build loads, reading each shared directory once.
- Keep only those rules when resolving a product's profiles, before `filter_rules`. When a product's rules can't be determined, nothing is dropped.

## Capabilities

### Modified Capabilities

- `rule-product-availability`: profiles count only rules their product's build loads.

## Impact

- **Affected code**: `core/discovery/rule_paths.py`, `core/discovery/profile_resolution.py`, `core/discovery/rules.py`.
- **Results** at `f09d243`: rule selections across all profiles go from 69768 to 68997, all 771 removed entries coming from control selections. No profile selects a rule outside its product directly, which would fail the build, so the product rule sets agree with what the build accepts. The profile index builds in 9.0 seconds, against 9.2, since fewer rules need `filter_rules` evaluated.
