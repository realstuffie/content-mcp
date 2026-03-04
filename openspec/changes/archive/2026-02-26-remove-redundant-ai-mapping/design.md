## Context

The `suggest_rule_mappings` MCP tool wraps `RuleMapper`, which:
1. Fetches up to 100 rules from `RuleDiscovery.search_rules()` and formats them as text context
2. Optionally gathers cross-framework evidence via `ControlDiscovery.find_similar_requirements()`
3. Sends both to Claude API and parses the JSON response into `RuleSuggestion` objects

The primary consumer is the `map-requirement` skill, where the outer Claude session already has full conversational context. The skill also calls `find_similar_requirements` separately in Step 2a, duplicating the cross-reference work.

Meanwhile, a `search_rules` MCP tool already exists (`server/handlers/tools.py:39`) that exposes `RuleDiscovery.search_rules()` directly with query, product, severity, and limit parameters. This tool returns `RuleSearchResult` objects (rule_id, title, severity, description, products, file_path) — essentially the same data that `RuleMapper._build_rules_context()` formats for the inner Claude call.

## Goals / Non-Goals

**Goals:**
- Remove the `suggest_rule_mappings` MCP tool and its handler
- Update documentation to reflect the removal

**Non-Goals:**
- Removing `RuleMapper` class itself — it's still used by `review_control_generation` and `MappingReviewer`
- Modifying `search_rules` — it already provides the needed data
- Removing the `RuleSuggestion` model — still used by `MappingReviewer`
- Updating the `map-requirement` skill — that lives in the content repo and is tracked separately in `skill-update-plan.md`

## Decisions

### 1. Remove the tool, keep the class

**Decision**: Delete the `suggest_rule_mappings` tool definition and handler from `tools.py`. Keep `core/ai/rule_mapper.py` since `review_control_generation` (tools.py:1038) and `MappingReviewer` still import it.

**Alternative considered**: Deprecate instead of remove. Rejected because the tool has no external consumers beyond the skill we control, and deprecation adds complexity without value.

### 2. Use existing `search_rules` — no new tool needed

**Decision**: The existing `search_rules` MCP tool already returns rule IDs, titles, descriptions, severities, and product lists. The `map-requirement` skill can call this directly. No new tool is needed.

**Alternative considered**: Create a `list_candidate_rules` tool with richer output (references, identifiers). Rejected because `search_rules` provides sufficient data for the outer Claude to reason about, and `get_rule_details` can be used for deeper inspection of specific candidates.

## Risks / Trade-offs

- **[Risk] Existing tests for `suggest_rule_mappings` handler break** → Mitigation: remove the corresponding tests alongside the handler.
- **[Risk] Downstream skill breakage** → The `map-requirement` skill in the content repo will fail on Step 2b until updated. Mitigation: `skill-update-plan.md` documents the required changes; the skill's error handling (line 171) already gracefully handles unavailable AI suggestions by skipping Step 2b.
