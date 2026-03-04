## MODIFIED Requirements

### Requirement: Suggest rule mappings with cross-framework evidence
The existing `suggest_rule_mappings` MCP tool SHALL accept two new optional parameters: `cross_reference` (boolean, default false) and `target_product` (string, optional). When `cross_reference` is true, the AI prompt SHALL include rules mapped to similar requirements in other control frameworks. When `target_product` is set, rule context SHALL prioritize rules with identifiers for that product.

#### Scenario: Cross-reference enabled
- **WHEN** `suggest_rule_mappings` is called with `cross_reference: true` for a requirement about SSH configuration
- **THEN** the AI prompt includes a section listing rules mapped to similar requirements from other control frameworks (e.g., rules from NIST 800-53 AC-17 when mapping a CIS SSH requirement)

#### Scenario: Target product filtering
- **WHEN** `suggest_rule_mappings` is called with `target_product: "rhel9"`
- **THEN** the AI prompt prioritizes rules that have identifiers for rhel9, and includes a secondary section listing rules that exist in other products but not rhel9

#### Scenario: Both parameters combined
- **WHEN** `suggest_rule_mappings` is called with `cross_reference: true` and `target_product: "rhel9"`
- **THEN** the AI prompt includes both cross-framework evidence and product-aware prioritization

#### Scenario: Backward compatibility
- **WHEN** `suggest_rule_mappings` is called without the new parameters
- **THEN** the tool behaves identically to its current implementation (no cross-framework evidence, no product filtering)
