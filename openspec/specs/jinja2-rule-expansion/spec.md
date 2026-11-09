## ADDED Requirements

### Requirement: Rule YAML loading with Jinja2 expansion
The `RuleDiscovery` class SHALL use `ssg.yaml.open_and_expand()` to load rule YAML files instead of direct `yaml.load()`. This SHALL process Jinja2 control structures (`{% if %}`, `{% endif %}`, `{% set %}`) before YAML parsing, making rules with block-level Jinja2 templates discoverable.

When a product is given, the system SHALL expand the rule with that product's variables as the build does: the product's `product.yml` plus the `product_properties` directory. Without a product, the system SHALL expand the rule with `product` set to an empty string.

#### Scenario: Rule with Jinja2 control structures is discoverable without product
- **WHEN** `get_rule_details` is called for a rule whose `rule.yml` contains `{% if product == "rhel10" %}` blocks and no `product` parameter is provided
- **THEN** the system SHALL return a valid `RuleDetail` with core metadata (title, severity, identifiers) populated

#### Scenario: Rule with Jinja2 control structures is discoverable with product
- **WHEN** `get_rule_details` is called for a rule whose `rule.yml` contains `{% if product == "rhel10" %}` blocks and `product="rhel10"` is provided
- **THEN** the system SHALL return a valid `RuleDetail` with product-specific content (e.g., warnings, platform constraints) from the matching conditional branch

#### Scenario: Product variables are expanded
- **WHEN** `get_rule_details` is called with `product="ubuntu2204"` for a rule whose description starts with `{{{ full_name }}}`
- **THEN** the description starts with "Ubuntu 22.04"

#### Scenario: Rule testing the product name loads without a product
- **WHEN** `get_rule_details` is called without `product` for a rule whose `rule.yml` contains `{{% if 'ubuntu' in product %}}`
- **THEN** the system SHALL return a valid `RuleDetail`, with that condition evaluated as false

#### Scenario: Rule without Jinja2 templates loads normally
- **WHEN** `get_rule_details` is called for a rule whose `rule.yml` contains no Jinja2 control structures
- **THEN** the system SHALL return the same `RuleDetail` as before this change

### Requirement: Search includes rules with Jinja2 control structures
The `search_rules` method SHALL find and return rules whose `rule.yml` contains Jinja2 block-level control structures. These rules SHALL NOT be silently dropped from search results.

#### Scenario: Search by query matches rule with Jinja2 blocks
- **WHEN** `search_rules` is called with a query matching a rule that has `{% if %}` blocks in its `rule.yml`
- **THEN** the rule SHALL appear in the search results with correct title and severity

#### Scenario: Search with product parameter expands templates
- **WHEN** `search_rules` is called with a `product` parameter and matches a rule with Jinja2 blocks
- **THEN** the search result SHALL contain product-specific content from the expanded template

### Requirement: Fallback to raw YAML on expansion failure
If `ssg.yaml.open_and_expand()` raises an exception for a rule file, the system SHALL fall back to loading the file with `yaml.load(content, Loader=yaml.FullLoader)`. This preserves existing behavior when the SSG module is unavailable or the file has expansion errors.

#### Scenario: SSG expansion fails gracefully
- **WHEN** `ssg.yaml.open_and_expand()` raises an exception for a rule file
- **THEN** the system SHALL attempt to load the file using direct `yaml.load()` and return the result if successful

#### Scenario: Expansion without a product needs product variables
- **WHEN** no `product` is given and both the generic expansion and direct `yaml.load()` fail for a rule file
- **THEN** the system SHALL expand the rule again keeping `{{{ full_name }}}` as literal text, and then with the variables of each product in alphabetical order, returning the first result that loads

#### Scenario: Both expansion and raw loading fail
- **WHEN** every expansion and direct `yaml.load()` fail for a rule file
- **THEN** the system SHALL return `None` (existing error handling behavior)

### Requirement: Expansions read current files
The system SHALL expand rules and control files with `ssg.yaml.open_and_expand()` through one function that turns off the template cache of `ssg.jinja`'s environment, because that cache treats a compiled template as current while its file's modification time is unchanged. The system SHALL drop that environment, so `ssg.jinja` makes a new one, when a file in `shared/macros`, a `product.yml` or a `.yml` file in `product_properties` changed since it was made, or when the system didn't make it.

#### Scenario: Rule rewritten with its old modification time
- **WHEN** a rule is expanded, then rewritten with contents of the same size and its old modification time, then expanded again
- **THEN** the second expansion returns the new contents

#### Scenario: Macro change
- **WHEN** a file in `shared/macros` changes between two expansions
- **THEN** the second expansion uses a new environment with the changed macros
