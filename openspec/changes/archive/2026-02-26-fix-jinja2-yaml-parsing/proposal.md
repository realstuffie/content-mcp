## Why

Rules whose `rule.yml` contains Jinja2 block-level control structures (`{% if product == "rhel10" %}`) fail YAML parsing with `ScannerError`, which is silently caught — making the rule invisible to `get_rule_details` and `search_rules`. 242 rule files contain such blocks, so a significant portion of the content repository is silently undiscoverable.

## What Changes

- Replace direct `yaml.load()` calls in `RuleDiscovery` with `ssg.yaml.open_and_expand()`, which processes Jinja2 templates before YAML parsing
- When a `product` parameter is provided, expand templates with product context for accurate product-specific content
- When no product is provided, expand with an empty substitutions dict (conditionals evaluate to false, producing a generic fallback sufficient for discovery)
- Add fallback to raw `yaml.load()` if SSG expansion fails, preserving current behavior for non-templated files

## Non-goals

- Modifying how the SSG module itself handles Jinja2 expansion
- Adding product-aware expansion to other discovery modules (profiles, controls, templates)
- Changing the MCP tool API signatures — the existing optional `product` parameter is already sufficient

## Capabilities

### New Capabilities
- `jinja2-rule-expansion`: Rule YAML loading uses Jinja2 template expansion via `ssg.yaml.open_and_expand()` so that rules with control-flow blocks are discoverable and product-specific content is correctly resolved

### Modified Capabilities

## Impact

- **Core logic layer**: `core/discovery/rules.py` — `_load_rule_yaml` helper added, `get_rule_details` and `_load_search_result` updated to use it
- **Integration layer**: Uses existing `ssg.yaml` module via `get_ssg_modules()` — no new dependencies
- **MCP protocol layer**: No API changes; existing `product` parameter on `get_rule_details` and `search_rules` is already threaded through
