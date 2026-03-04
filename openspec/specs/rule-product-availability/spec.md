## ADDED Requirements

### Requirement: Get rule product availability
The system SHALL provide a `get_rule_product_availability` MCP tool that reports which products include a given rule. The tool SHALL accept `rule_id` (str, required) and return a `RuleProductAvailability` object containing: products from identifiers (cce@/stigid@ keys in rule.yml), products from profile selections, platform constraints, template info, and build artifact presence.

#### Scenario: Rule with multiple product identifiers
- **WHEN** `get_rule_product_availability` is called for a rule that has `cce@rhel8`, `cce@rhel9`, and `stigid@rhel8` identifiers
- **THEN** `products_with_identifiers` includes "rhel8" and "rhel9"

#### Scenario: Rule selected in profiles
- **WHEN** `get_rule_product_availability` is called for a rule selected in profiles for rhel8 and rhel9
- **THEN** `products_in_profiles` contains `{"rhel8": ["cis", "stig"], "rhel9": ["cis"]}` (or similar mapping of product to profile names)

#### Scenario: Control references in profiles not matched
- **WHEN** a profile selection contains a control reference like `anssi:all:minimal` (not a direct rule ID)
- **THEN** the system does NOT count that as a match for any rule

#### Scenario: Rule not found
- **WHEN** `get_rule_product_availability` is called with a `rule_id` that does not exist
- **THEN** the system returns `null`/None

#### Scenario: Build artifact checking
- **WHEN** `get_rule_product_availability` is called for a rule with built products
- **THEN** `has_build_artifacts` contains a mapping of product names to booleans indicating whether rendered content exists

### Requirement: RuleProductAvailability model
The system SHALL define a `RuleProductAvailability` Pydantic model with fields: `rule_id` (str), `products_with_identifiers` (list[str]), `products_in_profiles` (dict[str, list[str]]), `platforms` (list[str]), `template` (dict | None), `has_build_artifacts` (dict[str, bool]).

#### Scenario: Model validation
- **WHEN** a `RuleProductAvailability` is created with valid data
- **THEN** all fields are populated according to their types and defaults

### Requirement: Profile scanning with reverse index cache
The system SHALL build a reverse index `{rule_id → [(product, profile_id)]}` on first call and cache it on the `RuleDiscovery` instance. Subsequent calls SHALL use the cached index.

#### Scenario: Cache reuse
- **WHEN** `get_rule_product_availability` is called twice on the same `RuleDiscovery` instance
- **THEN** profile scanning occurs only once; the second call uses the cached reverse index
