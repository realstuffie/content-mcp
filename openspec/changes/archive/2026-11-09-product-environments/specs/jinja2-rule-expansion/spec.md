## MODIFIED Requirements

### Requirement: Expansions read current files
The system SHALL expand rules and control files with `ssg.yaml.open_and_expand()` through one function that turns off the template cache of `ssg.jinja`'s environment, because that cache treats a compiled template as current while its file's modification time is unchanged. The system SHALL drop its environments, so `ssg.jinja` makes new ones, when a file in `shared/macros`, a `product.yml` or a `.yml` file in `product_properties` changed since they were made. An environment the system didn't make SHALL NOT be used.

The system SHALL use a separate environment for each set of variables, so macros read the variables of the product being expanded. It SHALL keep at most 16 environments, dropping the least recently used, and SHALL make them with `ssg.jinja`'s bytecode cache in a temporary directory. It SHALL NOT change the caller's variables.

#### Scenario: Rule rewritten with its old modification time
- **WHEN** a rule is expanded, then rewritten with contents of the same size and its old modification time, then expanded again
- **THEN** the second expansion returns the new contents

#### Scenario: Macro change
- **WHEN** a file in `shared/macros` changes between two expansions
- **THEN** the second expansion uses a new environment with the changed macros

#### Scenario: Macros use the expanded product
- **WHEN** a rule whose description calls `describe_package_install` is expanded for `rhel9`, then for `ubuntu2204`
- **THEN** the `rhel9` description says `dnf install` and the `ubuntu2204` description says `apt-get install`
