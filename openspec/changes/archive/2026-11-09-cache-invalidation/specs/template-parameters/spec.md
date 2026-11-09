## MODIFIED Requirements

### Requirement: Parameters from the rules that use a template
The system SHALL read the `vars` of the `template` block of every `rule.yml` under `linux_os/`, `applications/` and `products/`. Product overrides such as `pkgname@ubuntu2204` SHALL count as the base parameter. Jinja2 statements in the block SHALL be dropped, so the vars of every branch count, and Jinja2 expressions SHALL be read as a placeholder.

For each parameter, `used_by_rules` SHALL give the number of rules that set it, and `type` the YAML types of the values rules use, or `unknown` when no rule sets it. Parameters that rules set but the reference does not list SHALL be included after the documented ones, with a description saying so. `used_by_rules` on the schema SHALL give the number of rules that use the template.

The rule scan SHALL be cached per content repository and refreshed when a rule file is added, removed or modified, or a `product.yml` changes. Rule files SHALL be compared individually by modification time, status change time and size, and the rule directories SHALL be listed again on each check.

#### Scenario: Parameter the reference leaves out
- **WHEN** rules using `sshd_lineinfile` set `xccdf_variable` and the reference does not list it
- **THEN** the schema lists `xccdf_variable` with the number of rules that set it

#### Scenario: Template the reference doesn't document
- **WHEN** `mount_option_home` has no section in the reference and its rules set `mountoption`
- **THEN** the schema lists `mountoption`

#### Scenario: Jinja2 in a template block
- **WHEN** a rule sets `pkgname` in both branches of a `{{% if %}}` block
- **THEN** the rule counts once toward `pkgname`
