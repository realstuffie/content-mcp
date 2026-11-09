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
- **THEN** `has_build_artifacts` contains an entry for each checked built product, true when `build/<product>/rules/<rule_id>.json` can be loaded and false when it is absent
- **AND** OVAL or remediation files alone do not make an entry true
- **AND** an omitted product has no reported result, and the field does not report datastream presence

### Requirement: RuleProductAvailability model
The system SHALL define a `RuleProductAvailability` Pydantic model with fields: `rule_id` (str), `products_with_identifiers` (list[str]), `products_in_profiles` (dict[str, list[str]]), `platforms` (list[str]), `template` (dict | None), `has_build_artifacts` (dict[str, bool]).

#### Scenario: Model validation
- **WHEN** a `RuleProductAvailability` is created with valid data
- **THEN** all fields are populated according to their types and defaults

### Requirement: Profile scanning with reverse index cache
The system SHALL build a reverse index `{rule_id → [(product, profile_id)]}` on first call and share it between `RuleDiscovery` instances for the same content repository, because each MCP tool call creates a new instance. The system SHALL rebuild the index when a file it was built from is added, removed, or modified: a profile, a control file, a `rule.yml` under a rule directory that a `product.yml` names, a `product.yml`, or a `.yml` file in `product_properties`.

The system SHALL compare each file's modification time, status change time and size individually, not only the newest time. It SHALL list the rule directories again on each check, down to each rule directory, so a rule added or removed at any depth is noticed without relying on directory timestamps. When a `product.yml` changes, the rebuilt index SHALL watch the rule directories the changed file names.

#### Scenario: Cache reuse
- **WHEN** `get_rule_product_availability` is called twice, from the same or different `RuleDiscovery` instances
- **THEN** profile scanning occurs only once; the second call uses the cached reverse index

#### Scenario: Cache invalidation
- **WHEN** a profile or control file changes between two calls
- **THEN** the second call rebuilds the reverse index

#### Scenario: Rule change
- **WHEN** a rule's `platform` changes between two calls, so a profile's `filter_rules` now excludes it
- **THEN** the second call rebuilds the reverse index without that membership

#### Scenario: Change to a file that is not the newest
- **WHEN** two watched files have modification times 100 and 200, and the first one's time becomes 150
- **THEN** the next call rebuilds the reverse index

#### Scenario: Copy that keeps the modification time
- **WHEN** a watched file is replaced with contents of the same size and its old modification time
- **THEN** its new status change time makes the next call rebuild the reverse index

#### Scenario: Rule in a new nested group
- **WHEN** a rule is added in a new group nested in an existing group, or in an existing empty directory
- **THEN** the next call rebuilds the reverse index

#### Scenario: Rule directories move
- **WHEN** a `product.yml` changes its `benchmark_root` or adds `additional_content_directories`
- **THEN** the next call rebuilds the reverse index, and later changes under the new directories are noticed

### Requirement: Product filter in rule search
When `search_rules` is called with a `product`, a rule SHALL match the product filter when any profile of that product selects it, as resolved by the reverse index, or when it has identifiers for that product.

Hidden profiles SHALL contribute their rules to product-filtered searches but
SHALL NOT appear in `products_in_profiles`. The shared cache SHALL preserve
both selectable-profile memberships and rules contributed by hidden profiles.

#### Scenario: Hidden profile contributes an otherwise unselected rule

- **WHEN** a hidden default profile selects a rule that no selectable profile selects
- **THEN** a rule search for that product includes it
- **AND** `products_in_profiles` does not claim that the hidden profile selects it for a scan

#### Scenario: Selectable profile extends a hidden profile

- **WHEN** a selectable profile inherits rules from a hidden profile
- **THEN** the inherited rules list the selectable child in `products_in_profiles`
- **AND** the hidden parent is omitted

#### Scenario: Rule selected only through a profile
- **WHEN** `search_rules` is called with `product="ubuntu2204"` and a rule has no `ubuntu2204` identifiers but a `ubuntu2204` profile selects it
- **THEN** the rule is included in the results

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

#### Scenario: Profile filter_rules
- **WHEN** a profile has `filter_rules`, such as `'"ocp4-node" not in platform'`
- **THEN** only the selected rules the expression accepts count as selected by that profile, after `extends` and unselections
- **AND** the expression is evaluated with ComplianceAsCode's `ssg.utils.safe_eval_filter` against the rule's attributes, expanded with the product's variables: `id_`, `platform` (empty when unset), and `platforms`, which includes `platform`
- **AND** a rule that can't be loaded or evaluated stays selected

#### Scenario: Rules the product's build doesn't load
- **WHEN** a profile selects, through a control file, a rule outside the directories the product's build reads (its `benchmark_root` and any `additional_content_directories`), or a rule marked `documentation_complete: false`
- **THEN** the rule does not count as selected by that profile, as the build drops it from control selections
