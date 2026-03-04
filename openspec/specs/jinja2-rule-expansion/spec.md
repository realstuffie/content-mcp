## ADDED Requirements

### Requirement: Rule YAML loading with Jinja2 expansion
The `RuleDiscovery` class SHALL use `ssg.yaml.open_and_expand()` to load rule YAML files instead of direct `yaml.load()`. This SHALL process Jinja2 control structures (`{% if %}`, `{% endif %}`, `{% set %}`) before YAML parsing, making rules with block-level Jinja2 templates discoverable.

#### Scenario: Rule with Jinja2 control structures is discoverable without product
- **WHEN** `get_rule_details` is called for a rule whose `rule.yml` contains `{% if product == "rhel10" %}` blocks and no `product` parameter is provided
- **THEN** the system SHALL return a valid `RuleDetail` with core metadata (title, severity, identifiers) populated

#### Scenario: Rule with Jinja2 control structures is discoverable with product
- **WHEN** `get_rule_details` is called for a rule whose `rule.yml` contains `{% if product == "rhel10" %}` blocks and `product="rhel10"` is provided
- **THEN** the system SHALL return a valid `RuleDetail` with product-specific content (e.g., warnings, platform constraints) from the matching conditional branch

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

#### Scenario: Both expansion and raw loading fail
- **WHEN** both `ssg.yaml.open_and_expand()` and direct `yaml.load()` fail for a rule file
- **THEN** the system SHALL return `None` (existing error handling behavior)
