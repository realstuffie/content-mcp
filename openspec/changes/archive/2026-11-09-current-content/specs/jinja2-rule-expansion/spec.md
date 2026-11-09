## ADDED Requirements

### Requirement: Expansions read current files
The system SHALL expand rules and control files with `ssg.yaml.open_and_expand()` through one function that turns off the template cache of `ssg.jinja`'s environment, because that cache treats a compiled template as current while its file's modification time is unchanged. The system SHALL drop that environment, so `ssg.jinja` makes a new one, when a file in `shared/macros`, a `product.yml` or a `.yml` file in `product_properties` changed since it was made, or when the system didn't make it.

#### Scenario: Rule rewritten with its old modification time
- **WHEN** a rule is expanded, then rewritten with contents of the same size and its old modification time, then expanded again
- **THEN** the second expansion returns the new contents

#### Scenario: Macro change
- **WHEN** a file in `shared/macros` changes between two expansions
- **THEN** the second expansion uses a new environment with the changed macros
