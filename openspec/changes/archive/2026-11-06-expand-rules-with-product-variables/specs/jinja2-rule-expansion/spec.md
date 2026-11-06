## MODIFIED Requirements

### Requirement: Rule YAML loading with Jinja2 expansion
When a product is given, the system SHALL expand the rule with that product's variables as the build does: the product's `product.yml` plus the `product_properties` directory. Without a product, the system SHALL expand the rule with `product` set to an empty string.

#### Scenario: Product variables are expanded
- **WHEN** `get_rule_details` is called with `product="ubuntu2204"` for a rule whose description starts with `{{{ full_name }}}`
- **THEN** the description starts with "Ubuntu 22.04"

#### Scenario: Rule testing the product name loads without a product
- **WHEN** `get_rule_details` is called without `product` for a rule whose `rule.yml` contains `{{% if 'ubuntu' in product %}}`
- **THEN** the system SHALL return a valid `RuleDetail`, with that condition evaluated as false

### Requirement: Fallback to raw YAML on expansion failure

#### Scenario: Expansion without a product needs product variables
- **WHEN** no `product` is given and both the generic expansion and direct `yaml.load()` fail for a rule file
- **THEN** the system SHALL expand the rule again keeping `{{{ full_name }}}` as literal text, and then with the variables of each product in alphabetical order, returning the first result that loads
