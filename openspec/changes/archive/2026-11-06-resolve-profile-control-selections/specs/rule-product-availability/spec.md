## MODIFIED Requirements

### Requirement: Get rule product availability

#### Scenario: Control references in profiles resolved
- **WHEN** a profile selection contains a control reference like `anssi:all:minimal`
- **THEN** the rules of the selected requirements count as selected by that profile
- **AND** the control reference itself is not indexed as a rule ID

## ADDED Requirements

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
