## Why

`search_rules` matched the `product` filter only against `cce@` and `stigid@` identifiers. Ubuntu and Debian rules rarely have identifiers, so `search_rules(product="ubuntu2204")` returned no rules, while the Ubuntu 22.04 profiles select 639. The same was true for ubuntu2404, debian12 and debian13, and other products were undercounted: rhel9 returned 1140 of 1551.

The profile index that could answer this was cached on the `RuleDiscovery` instance, but each MCP tool call creates a new instance, so every `get_rule_product_availability` call rebuilt it, taking about 15 seconds.

## What Changes

- A rule matches the product filter when the product's profiles select it or it has identifiers for the product.
- Share the profile index between `RuleDiscovery` instances and rebuild it when a profile or control file changes.

## Non-goals

- Caching parsed rules for `search_rules` itself, which still takes about 4 seconds per call.

## Capabilities

### Modified Capabilities

- `rule-product-availability`: the reverse index is shared between instances and used by the `search_rules` product filter.

## Impact

- **Affected code**: `core/discovery/rules.py`, the `search_rules` tool description in `server/handlers/tools.py`.
- **Results**: `search_rules(product=...)` returns 639 rules for ubuntu2204, matching its built datastream, 648 for ubuntu2404, 887 for debian12, 802 for debian13, 1551 for rhel9 and 986 for sle15. After the first index build, `get_rule_product_availability` takes about 0.1 seconds instead of 15.
