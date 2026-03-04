## REMOVED Requirements

### Requirement: Suggest rule mappings with cross-framework evidence
**Reason**: The `suggest_rule_mappings` MCP tool makes a redundant Claude API call. The primary caller is already Claude (via the `map-requirement` skill), which can perform the same reasoning using data from the existing `search_rules` and `find_similar_requirements` tools. The cross-reference feature duplicates work already done by the skill in a separate step.

**Migration**: Callers SHALL use the existing `search_rules` MCP tool to retrieve rule catalogs and perform matching reasoning directly. Cross-framework evidence is available via the existing `find_similar_requirements` MCP tool.

### Requirement: Suggest rule mappings for a control requirement
**Reason**: Removed along with the parent capability. The base tool (without cross-framework/product parameters) is equally redundant.

**Migration**: Same as above — use `search_rules` for rule data and reason about matches in the calling context.
