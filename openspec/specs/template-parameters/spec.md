## ADDED Requirements

### Requirement: Parameters from the template reference
`get_template_schema` SHALL return the parameters listed under "Parameters:" in the template's section of `docs/templates/template_reference.md`, in the order listed, each with its description. Bold markers SHALL be removed from descriptions.

#### Scenario: Documented template
- **WHEN** `get_template_schema("package_installed")` is called and the reference lists `pkgname` and `evr`
- **THEN** the schema lists `pkgname` and `evr` with their descriptions

### Requirement: Parameters from the rules that use a template
The system SHALL read the `vars` of the `template` block of every `rule.yml` under `linux_os/`, `applications/` and `products/`. Product overrides such as `pkgname@ubuntu2204` SHALL count as the base parameter. Jinja2 statements in the block SHALL be dropped, so the vars of every branch count, and Jinja2 expressions SHALL be read as a placeholder.

For each parameter, `used_by_rules` SHALL give the number of rules that set it, and `type` the YAML types of the values rules use, or `unknown` when no rule sets it. Parameters that rules set but the reference does not list SHALL be included after the documented ones, with a description saying so. `used_by_rules` on the schema SHALL give the number of rules that use the template.

The system SHALL read the rule files on each call, so an added, removed or changed rule counts in the next schema.

#### Scenario: Parameter the reference leaves out
- **WHEN** rules using `sshd_lineinfile` set `xccdf_variable` and the reference does not list it
- **THEN** the schema lists `xccdf_variable` with the number of rules that set it

#### Scenario: Template the reference doesn't document
- **WHEN** `mount_option_home` has no section in the reference and its rules set `mountoption`
- **THEN** the schema lists `mountoption`

#### Scenario: Jinja2 in a template block
- **WHEN** a rule sets `pkgname` in both branches of a `{{% if %}}` block
- **THEN** the rule counts once toward `pkgname`

### Requirement: Required parameters
A documented parameter SHALL be required unless its description says "optional" or mentions a default, or at least one rule using the template leaves it out. A parameter only rules set SHALL be required when every rule using the template sets it. When a documented parameter is optional and its description gives a default, the default SHALL be returned.

#### Scenario: Documented parameter some rules leave out
- **WHEN** the reference doesn't call `value` optional, but some `sshd_lineinfile` rules set `xccdf_variable` instead
- **THEN** `value` is not required

### Requirement: Supported languages and an example
The schema SHALL include the `supported_languages` from the template's `template.yml`. `example_usage` SHALL be the vars of a real rule using the template, and `example_rule` its ID. The example SHALL be the smallest set of vars that includes every required parameter, preferring rules without Jinja2 or product overrides in the block.

#### Scenario: Example from a rule
- **WHEN** `package_tmux_installed` sets only `pkgname: tmux` and other rules add product overrides
- **THEN** `example_rule` is `package_tmux_installed` and `example_usage` is `{"pkgname": "tmux"}`

### Requirement: No invented parameters
When neither the reference nor any rule gives parameters for a template, the schema SHALL list none.

#### Scenario: Unused, undocumented template
- **WHEN** a template has no section in the reference and no rule uses it
- **THEN** `parameters` is empty and `example_usage` is null

### Requirement: Template descriptions
`list_templates` and `get_template_schema` SHALL describe each template with the first paragraph of its section in the reference: the first bullet, or the opening paragraph when the section starts with one.

#### Scenario: Section that opens with a paragraph
- **WHEN** the `key_value_pair_in_file` section starts with a paragraph instead of a bullet
- **THEN** the description is that paragraph
