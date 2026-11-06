## Why

`get_rule_product_availability` skipped every profile selection containing `:`, so rules selected through control files never counted. Most current profiles select rules that way, for example `stig_rhel9:all` or `cis_rhel9:all:l2_server`. For `accounts_umask_interactive_users` the tool reported ol7, rhv4 and sle15 and missed the RHEL 8, 9 and 10, AlmaLinux 9 and OL 8, 9 and 10 STIG profiles.

The profile parser also ended the `selections` section at the first indented comment or Jinja line, and kept quotes and inline comments in selections. 125 of 321 profiles in current content lost selections, including all 481 of `ol8/stig`.

## What Changes

- Add `ProfileRuleResolver`, which resolves a profile's selections into rule IDs: control references (`policy:all`, `policy:all:level`, `policy:requirement`), level inheritance, nested and referenced requirements, `extends`, and `!rule` unselections.
- Build the profile reverse index from resolved rules instead of raw selections.
- Fix the profile parser: skip indented comments, keep the section open across Jinja lines, and strip quotes and inline comments from selections.

## Non-goals

- Evaluating Jinja in profiles or control files. Selections from every Jinja branch are kept.
- Applying `filter_rules` from profiles.
- Changing the `get_rule_product_availability` tool interface or the `RuleProductAvailability` model.

## Capabilities

### Modified Capabilities

- `rule-product-availability`: profile selections are resolved like the build, so control references, `extends` and unselections affect `products_in_profiles`.

## Impact

- **Affected code**: `core/discovery/profile_resolution.py` (new), `core/discovery/rules.py` (`_build_profile_rule_index`), `core/discovery/profiles.py` (`_parse_profile`).
- **APIs**: No schema changes.
- **Performance**: Building the index reads each control file once per product. It takes about 16 seconds against current content, on first use only.
- **Risk**: Low. Results for direct rule selections are unchanged, except that unselected rules and the quoted `"!rule"` entries the old parser produced no longer appear.
