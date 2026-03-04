## Why

The `suggest_rule_mappings` MCP tool sends rules context to the Claude API to get mapping suggestions, but its primary caller is already Claude (via the `map-requirement` skill). This creates a redundant AI-to-AI call — Claude asks the MCP server to ask Claude to reason about rule mappings, when the outer Claude could do that reasoning itself with the same data. Additionally, the skill already calls `find_similar_requirements` in Step 2a, but then passes `cross_reference: true` to `suggest_rule_mappings` which performs the same cross-framework lookup again internally.

## What Changes

- **Replace `suggest_rule_mappings`** with a new `search_rules` tool that returns the rules catalog as pure data (rule IDs, titles, descriptions, product lists) without making any AI call. **BREAKING**: The `suggest_rule_mappings` tool is removed.
- **Remove `RuleMapper`** class and its Claude API dependency from the tool layer. The `core/ai/rule_mapper.py` module is no longer used by any MCP tool.
## Non-goals

- Removing the `core/ai/` module entirely — `ClaudeClient` and requirement extraction are still used by other tools (`review_control_generation`, policy document ingestion).
- Changing `find_similar_requirements` — it stays as-is.
- Adding new AI capabilities — this is purely about removing a redundant indirection.
- Updating the `map-requirement` skill in the content repo — that is tracked separately in `plan.md` at the project root.

## Capabilities

### New Capabilities
None. The existing `search_rules` MCP tool already provides the needed data interface.

### Modified Capabilities
- `suggest-rule-mappings`: This capability is being **removed**. The AI-powered rule suggestion is replaced by the already-existing `search_rules` tool, with the AI reasoning delegated to the calling Claude session.

## Impact

- **MCP protocol layer**: `server/handlers/tools.py` — remove `suggest_rule_mappings` tool definition and handler.
- **Core logic layer**: `core/ai/rule_mapper.py` — no longer called from MCP tools. Kept for programmatic use by `review_control_generation` and `MappingReviewer`.
- **Breaking change**: Any client relying on `suggest_rule_mappings` must switch to `search_rules` + local reasoning.
