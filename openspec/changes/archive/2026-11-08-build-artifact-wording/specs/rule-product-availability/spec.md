## MODIFIED Requirements

### Requirement: Get rule product availability
The system SHALL provide a `get_rule_product_availability` MCP tool that reports which products include a given rule. The tool SHALL accept `rule_id` (str, required) and return a `RuleProductAvailability` object containing: products from identifiers (cce@/stigid@ keys in rule.yml), products from profile selections, platform constraints, template info, and build artifact presence.

#### Scenario: Rule with multiple product identifiers
- **WHEN** `get_rule_product_availability` is called for a rule that has `cce@rhel8`, `cce@rhel9`, and `stigid@rhel8` identifiers
- **THEN** `products_with_identifiers` includes "rhel8" and "rhel9"

#### Scenario: Rule selected in profiles
- **WHEN** `get_rule_product_availability` is called for a rule selected in profiles for rhel8 and rhel9
- **THEN** `products_in_profiles` contains `{"rhel8": ["cis", "stig"], "rhel9": ["cis"]}` (or similar mapping of product to profile names)

#### Scenario: Control references in profiles resolved
- **WHEN** a profile selection contains a control reference like `anssi:all:minimal`
- **THEN** the rules of the selected requirements count as selected by that profile
- **AND** the control reference itself is not indexed as a rule ID

#### Scenario: Rule not found
- **WHEN** `get_rule_product_availability` is called with a `rule_id` that does not exist
- **THEN** the system returns `null`/None

#### Scenario: Build artifact checking
- **WHEN** `get_rule_product_availability` is called for a rule with built products
- **THEN** `has_build_artifacts` contains an entry for each checked built product, true when `build/<product>/rules/<rule_id>.json` can be loaded and false when it is absent
- **AND** OVAL or remediation files alone do not make an entry true
- **AND** an omitted product has no reported result, and the field does not report datastream presence
