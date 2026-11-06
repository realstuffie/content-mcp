## MODIFIED Requirements

### Requirement: Flatten nested control structures

#### Scenario: Requirement files with a controls list
- **WHEN** a file in the `controls_dir` subdirectory holds its requirements in a top-level `controls` list, like the NIST 800-53 family files
- **THEN** every requirement in that list is loaded

#### Scenario: Requirement files with Jinja2
- **WHEN** a requirement file uses Jinja2, such as `{{{ full_name }}}` in a title
- **THEN** the file is expanded with the product's variables when a product is given
- **AND** without a product, it is expanded with an empty product name, no product families, and "The operating system" as `full_name`
