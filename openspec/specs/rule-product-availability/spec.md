## ADDED Requirements

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

### Requirement: Resolve profile selections like the build
The system SHALL resolve each profile's selections into rule IDs the way the ComplianceAsCode build does before adding them to the reverse index. Control files SHALL be resolved per product, so product-specific control files override global ones.

#### Scenario: Whole control file
- **WHEN** a profile selects `policy:all`
- **THEN** the rules of every requirement in that control file, at any nesting depth, are selected

#### Scenario: Control file level
- **WHEN** a profile selects `policy:all:level`
- **THEN** the rules of requirements in that level, or in a level it inherits from, are selected
- **AND** a requirement without `levels` belongs to the control file's first level, or to `default` when the file defines no levels

#### Scenario: Single requirement
- **WHEN** a profile selects `policy:requirement_id`
- **THEN** the rules of that requirement, its nested requirements, and the requirements it references are selected

#### Scenario: Extended profile
- **WHEN** a profile has `extends: parent`
- **THEN** the rules selected by the parent profile are selected by this profile too

#### Scenario: Unselection
- **WHEN** a profile contains `!rule_id`
- **THEN** `rule_id` is not selected by that profile, even when a control reference or the parent profile selects it

#### Scenario: Variables and refinements
- **WHEN** a profile or requirement entry contains `=`
- **THEN** the entry selects no rule
