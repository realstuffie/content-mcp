## Why

Rule discovery looked for rules in a fixed list of directories: `linux_os`, `applications` and `shared`. The Firefox product keeps its 36 rules in `products/firefox/guide`, so `search_rules`, `get_rule_details` and `get_rule_product_availability` could not find them, and `search_rules(product="firefox")` returned nothing. Template discovery had its own, different list.

## What Changes

- Read rules from each product's `benchmark_root`, as the content build does, in a shared `rule_paths` module.
- Use it in both rule discovery and template discovery.

## Non-goals

- Validating `benchmark_root` values beyond ignoring ones outside the repository.

## Capabilities

### New Capabilities

- `rule-directories`: where rules are read from.

## Impact

- **Affected code**: `core/discovery/rule_paths.py` (new), `core/discovery/rules.py`, `core/discovery/templates.py`.
- **Results** at `f09d243`: the three roots are `applications`, `linux_os/guide` and `products/firefox/guide`. Indexed rules go from 2530 to 2566, and `search_rules(product="firefox")` from 0 to 36. All 36 Firefox rules load and pass `validate_rule_yaml`. `shared` held no rules, so nothing is lost by dropping it.
