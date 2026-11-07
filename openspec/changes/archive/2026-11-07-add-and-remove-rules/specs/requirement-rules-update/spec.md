## MODIFIED Requirements

### Requirement: Tool accepts control_id, requirement_id, rules, and optional status
The `update_requirement_rules` MCP tool SHALL accept `control_id` (string, required), `requirement_id` (string, required), `rules` (array of strings, required), `status` (string, optional), `product` (string, optional), and `mode` (`replace`, `add` or `remove`, optional, default `replace`). In replace mode, `status` SHALL default to `"automated"`; in add and remove modes, the status SHALL be left unchanged unless `status` is given.

The `status` parameter SHALL only accept the ComplianceAsCode control statuses listed in the `canonical-control-status` capability, taken from the same definition the control model uses.

When `product` is provided, the tool SHALL resolve the control file using product-aware discovery (searching `controls/` then `products/<product>/controls/`, with the product-specific file taking precedence).

### Requirement: Tool replaces rules list entirely
In replace mode, the tool SHALL replace the entire `rules` list with the provided rules, not append to existing rules.

### Requirement: Tool returns ControlUpdateResult
The tool SHALL return a `ControlUpdateResult` with `file_path`, `requirements_updated=1`, `requirements_added=0`, `requirements_unchanged=0`, `success=True`, and empty `errors` on success. Problems that did not stop the update, such as an unchecked edit, SHALL be listed in `warnings`. In every mode, `rules` SHALL give the requirement's rules after the update, and `rules_added` and `rules_removed` what changed, so a replace that drops rules says which.

## ADDED Requirements

### Requirement: Tool adds or removes rules
In add mode, the tool SHALL add the given rules that the requirement doesn't have yet, after its current rules, in the order given. In remove mode, it SHALL remove the given rules. Both SHALL change only the affected list items, so other lines of the list, comments included, stay; a list stored inline, such as `rules: [a]`, SHALL be rewritten as a block list. Removing the last rule SHALL leave `rules: []`. When the rules and status would not change, the tool SHALL write nothing and report the requirement as unchanged.

#### Scenario: Add one rule
- **WHEN** a requirement has rules `rule_a` and `rule_b`, after a comment, and the tool is called with `rules=["rule_c"]` and `mode="add"`
- **THEN** its rules SHALL be `rule_a`, `rule_b` and `rule_c`, the comment SHALL stay, and its status SHALL be unchanged

#### Scenario: Add a rule that is already there
- **WHEN** the tool is called with `mode="add"` and rules the requirement already has
- **THEN** the file SHALL be unchanged and the result SHALL have `requirements_unchanged=1`

#### Scenario: Remove one rule
- **WHEN** the tool is called with `rules=["rule_a"]` and `mode="remove"`
- **THEN** only the `rule_a` item SHALL be removed from the list
