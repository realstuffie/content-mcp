## MODIFIED Requirements

### Requirement: Resolve profile selections like the build

#### Scenario: Profile filter_rules
- **WHEN** a profile has `filter_rules`, such as `'"ocp4-node" not in platform'`
- **THEN** only the selected rules the expression accepts count as selected by that profile, after `extends` and unselections
- **AND** the expression is evaluated with ComplianceAsCode's `ssg.utils.safe_eval_filter` against the rule's attributes, expanded with the product's variables: `id_`, `platform` (empty when unset), and `platforms`, which includes `platform`
- **AND** a rule that can't be loaded or evaluated stays selected
