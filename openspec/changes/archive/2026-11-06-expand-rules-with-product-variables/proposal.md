## Why

`get_rule_details` failed for rules whose Jinja2 needs product variables. Without a product, `product` was undefined, so conditions like `{{% if 'ubuntu' in product %}}` raised an error, and an empty `{{{ full_name }}}` at the start of a description broke the YAML indentation. With a product, only `product` was passed, so variables such as `full_name`, `auid` and `audisp_conf_path` expanded to empty text. In current content 16 of 2530 rules failed to load without a product and 9 with `ubuntu2204`, including rules the Ubuntu CIS controls select, such as `service_tftp_disabled` and `file_permissions_sshd_private_key`. `validate_control_file` reported them as nonexistent.

## What Changes

- With a product, expand rules with the product's variables, loaded like `ssg.environment.open_environment()`: `product.yml` plus `product_properties`.
- Without a product, expand with `product` set to an empty string.
- Without a product, when both expansion and plain YAML fail, retry with `{{{ full_name }}}` kept as literal text, then with each product's variables.

## Non-goals

- Changing what rules look like when they already loaded without a product, apart from two rules whose generic expansion now succeeds.
- Loading the CMake build configuration, which rule.yml files don't need.

## Capabilities

### Modified Capabilities

- `jinja2-rule-expansion`: product expansion uses the build's product variables, and rules that need product variables load without a product.

## Impact

- **Affected code**: `core/discovery/rules.py` (`_load_rule_yaml`, new `_product_substitutions`).
- **Results**: all 2530 rules in current content load, with and without a product. With `ubuntu2204`, 1102 rules now show product values, such as the product name and file paths, where they showed empty text.
- **Risk**: Low. Product variables are loaded once per product and cached.
