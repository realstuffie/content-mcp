## Why

Profiles can set `filter_rules`, an expression the build uses to keep only some of the rules a profile selects. The OpenShift profiles rely on it to split one control file between a platform profile and a node profile: both select `cis_ocp_200:all`, and `filter_rules` keeps platform rules in `cis` and node rules in `cis-node`. The server ignored it, so every rule counted for both. At `f09d243`, 23 profiles of `ocp4`, `eks` and `rhcos4` use it; the OpenShift CIS profile counted 199 rules where the build selects 96.

## What Changes

- Read `filter_rules` from profiles, including expressions continued on indented lines, and return it in `get_profile_details`.
- Apply it when resolving profiles, after `extends` and unselections, so a parent's filter applies to the parent's rules and the child's to everything.
- Evaluate it with ComplianceAsCode's own `ssg.utils.safe_eval_filter`, against the rule's attributes expanded with the product's variables, since platforms such as `{{{ product }}}-node` use Jinja2. Rules that can't be loaded or evaluated stay selected.

## Capabilities

### Modified Capabilities

- `rule-product-availability`: profile `filter_rules` applies.

## Impact

- **Affected code**: `core/discovery/profiles.py`, `core/discovery/profile_resolution.py`, `core/discovery/rules.py`, `models/profile.py`.
- **Results** at `f09d243`: for all 23 profiles, the result matches resolving the same selections with the build's `Rule.from_yaml` objects and `rule_filter_from_def`. For the two `rhcos4` STIG profiles that needs one note: three kubevirt rules are outside `rhcos4`'s benchmark, so the build can't load them for `rhcos4`; the build leaves them out, and so does the server. Rule selections across all profiles go from 73568 to 69768. The OpenShift CIS profile goes from 199 rules to 96, and its node profile from 197 to 103.
- **Cost**: building the shared profile index takes about 0.7 seconds longer, 9.2 instead of 8.5, to load the rules of filtered profiles.
