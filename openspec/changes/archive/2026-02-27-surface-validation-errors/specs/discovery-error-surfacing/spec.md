## ADDED Requirements

### Requirement: DiscoveryResult type for list methods
The system SHALL provide a `DiscoveryResult[T]` generic dataclass with fields `items: list[T]` and `errors: list[str]` for returning list results with accumulated parse errors.

#### Scenario: List method encounters parse error
- **WHEN** a list discovery method (e.g., `list_products()`) encounters an item that fails YAML parsing or Pydantic validation
- **THEN** the error message (including the item identifier and exception detail) SHALL be appended to `DiscoveryResult.errors` and the method SHALL continue processing remaining items

#### Scenario: List method with no errors
- **WHEN** all items parse successfully
- **THEN** `DiscoveryResult.errors` SHALL be an empty list and `DiscoveryResult.items` SHALL contain all parsed items

### Requirement: Detail methods propagate parse errors
Detail discovery methods (`get_product_details`, `get_rule_details`, `get_profile_details`) SHALL return `None` only when the requested entity does not exist on disk. When the entity exists but fails to parse (YAML syntax error, Pydantic validation error), the method SHALL raise the exception instead of catching it and returning `None`.

#### Scenario: Entity exists but has invalid YAML
- **WHEN** `get_product_details("rhel9")` is called and `products/rhel9/product.yml` exists but contains invalid YAML
- **THEN** the method SHALL raise the YAML parsing exception (not return `None`)

#### Scenario: Entity exists but fails Pydantic validation
- **WHEN** `get_rule_details("some_rule")` is called and `rule.yml` exists but has a field with an incompatible type
- **THEN** the method SHALL raise `pydantic.ValidationError` (not return `None`)

#### Scenario: Entity genuinely does not exist
- **WHEN** `get_product_details("nonexistent")` is called and no directory exists for that product
- **THEN** the method SHALL return `None`

### Requirement: Control file tracks per-requirement parse errors
The `ControlFile` Pydantic model SHALL include a `parse_errors: list[str]` field (default empty list). When `parse_control_file()` encounters a requirement file that fails to parse, the error SHALL be recorded in this field and parsing SHALL continue with the remaining requirements.

#### Scenario: Some requirements fail to parse in a control file
- **WHEN** a control file references 50 requirements and 3 fail Pydantic validation
- **THEN** the returned `ControlFile` SHALL contain 47 requirements in `controls` and 3 error messages in `parse_errors`

#### Scenario: All requirements parse successfully
- **WHEN** all referenced requirements parse without error
- **THEN** `parse_errors` SHALL be an empty list

### Requirement: MCP handler surfaces errors in response text
The MCP tool handlers SHALL include error information in the response text when discovery methods return errors.

#### Scenario: List tool with parse errors
- **WHEN** a list tool (e.g., `list_products`) returns a `DiscoveryResult` with non-empty `errors`
- **THEN** the response text SHALL include a warning section listing the parse errors, in addition to the successful results

#### Scenario: Detail tool with parse error
- **WHEN** a detail tool (e.g., `get_product_details`) raises an exception due to parse failure
- **THEN** the handler's top-level exception handler SHALL return the error message as response text (existing behavior, no change needed)

#### Scenario: Control detail with parse errors
- **WHEN** `get_control_details` returns a `ControlFile` with non-empty `parse_errors`
- **THEN** the response text SHALL include the parse errors alongside the control file data

### Requirement: No silent exception blocks
All `except Exception: pass` blocks in the discovery layer SHALL be replaced with at minimum a `logger.warning()` call that includes the exception message.

#### Scenario: Template README read failure
- **WHEN** reading a template README file raises an exception
- **THEN** the exception SHALL be logged at warning level (not silently swallowed with `pass`)

#### Scenario: Template CSV example read failure
- **WHEN** reading a template CSV example file raises an exception
- **THEN** the exception SHALL be logged at warning level (not silently swallowed with `pass`)

### Requirement: Rule YAML fallback logs warning
When `_load_rule_yaml()` falls back from SSG Jinja2 expansion to direct YAML loading, the fallback SHALL be logged at warning level so users know expansion was skipped.

#### Scenario: SSG expansion fails, fallback to direct YAML
- **WHEN** `ssg_yaml.open_and_expand()` raises an exception and the method falls back to `yaml.load()`
- **THEN** a warning SHALL be logged indicating the fallback occurred, including the rule path and exception
