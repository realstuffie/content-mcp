## Why

The existing `suggest_rule_mappings` tool operates in isolation: it sends up to 100 rules to the Claude API with no awareness of other control frameworks or cross-product availability. When mapping requirements for one framework (e.g., CIS), it cannot leverage the fact that a similar requirement in another framework (e.g., NIST 800-53) already has rules mapped. This forces redundant AI calls and misses obvious mappings. Users also lack visibility into which products a rule actually applies to, making cross-product compliance work tedious.

## Non-goals

- No changes to the MCP transport layer (stdio/HTTP).
- No embedding-based or vector similarity — text similarity uses deterministic Jaccard tokenization.
- No changes to existing tool signatures beyond adding optional parameters to `suggest_rule_mappings`.
- No UI or client-side changes.

## What Changes

- **Three new deterministic MCP tools** added to the core discovery layer and exposed via MCP:
  - `get_control_rule_index` — builds a complete cross-framework index of all requirements and their rule mappings.
  - `find_similar_requirements` — finds requirements with similar text across control frameworks using Jaccard similarity.
  - `get_rule_product_availability` — reports which products include a given rule (via identifiers, profiles, and build artifacts).
- **Enhancement to `suggest_rule_mappings`** — two new optional parameters (`cross_reference`, `target_product`) that inject cross-framework evidence and product-aware prioritization into the AI mapping prompt.
- **New Pydantic models** in the models layer to represent indexed requirements, similarity results, and product availability.
- **Unit and integration tests** for all new functionality.

## Capabilities

### New Capabilities
- `control-rule-index`: Cross-framework indexing of all control requirements and their mapped rules. Covers the `get_control_rule_index` MCP tool, `ControlRuleIndex`/`IndexedRequirement` models, and recursive control flattening logic.
- `similar-requirements`: Text similarity search across control framework requirements. Covers the `find_similar_requirements` MCP tool, `SimilarRequirement` model, tokenization, and Jaccard similarity.
- `rule-product-availability`: Cross-product availability checking for individual rules. Covers the `get_rule_product_availability` MCP tool, `RuleProductAvailability` model, profile scanning, and build artifact checking.

### Modified Capabilities
- `suggest-rule-mappings`: Adding optional `cross_reference` and `target_product` parameters to inject cross-framework evidence and product-aware rule prioritization into the AI mapping prompt.

## Impact

- **Core logic layer** (`core/discovery/controls.py`, `core/discovery/rules.py`): New methods on `ControlDiscovery` and `RuleDiscovery` classes.
- **AI layer** (`core/ai/rule_mapper.py`): Modified `RuleMapper` to accept and use cross-reference and product targeting params.
- **Models layer** (`models/control.py`, `models/rule.py`): New Pydantic v2 models.
- **MCP protocol layer** (`server/handlers/tools.py`): Three new tool definitions and handler cases; updated schema for `suggest_rule_mappings`.
- **Dependencies**: No new external dependencies. All similarity logic is pure Python (set operations, regex tokenization).
- **Existing tests**: Integration test file (`tests/integration/test_tools.py`) extended with new tool handler tests.
