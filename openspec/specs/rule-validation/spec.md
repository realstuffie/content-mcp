## ADDED Requirements

### Requirement: documentation_complete as the build reads it
`validate_rule_yaml` SHALL NOT require `documentation_complete`, since the content build treats a rule without it as complete. The build leaves a rule out, except in Debug builds, only when the field's text is exactly `false`, quoted or not, because ComplianceAsCode's YAML loader keeps booleans as text. The validator SHALL warn, without making the rule invalid:

- when the value is `false`, that the build leaves the rule out
- when the value is another YAML false, such as `False` or `no`, that the build counts it as complete
- when the value is another YAML true, such as `yes`, that rules write `true`
- when the value is not a boolean, that the build counts it as complete

#### Scenario: Rule without the field
- **WHEN** a rule has no `documentation_complete` line
- **THEN** the rule is valid and no warning is given about the field

#### Scenario: Rule left out of the build
- **WHEN** a rule has `documentation_complete: false`
- **THEN** the rule is valid, with a warning that the build leaves it out

#### Scenario: Spelling the build doesn't read as false
- **WHEN** a rule has `documentation_complete: False`
- **THEN** the rule is valid, with a warning that the build counts it as complete
