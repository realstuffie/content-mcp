## Context

The content-agent MCP server provides discovery tools for ComplianceAsCode/content, including control framework browsing (`list_controls`, `get_control_details`, `search_controls`) and AI-powered rule mapping (`suggest_rule_mappings`). Currently, each tool operates in isolation — there's no way to see all rule mappings across frameworks at once, find similar requirements between frameworks, or check which products a rule actually applies to. The AI mapper sends up to 100 rules to the Claude API without cross-framework evidence, missing obvious mappings that exist in other control files.

The existing architecture follows a layered pattern: MCP handlers → core discovery/AI classes → content repository. New tools fit cleanly into the `core/discovery/` layer (deterministic tools) and `core/ai/` layer (AI enhancement). The `ControlDiscovery` class already handles control file parsing including both inline controls and `includes`-based patterns. The `controls_dir` pattern (used by some CAC control files) may need handling — this needs verification during implementation.

## Goals / Non-Goals

**Goals:**
- Enable cross-framework rule discovery through a complete index of all requirements and their mapped rules
- Enable similarity-based requirement matching using deterministic text similarity (Jaccard)
- Enable cross-product availability checking for individual rules (identifiers, profiles, build artifacts)
- Enhance AI rule mapping with cross-framework evidence and product-aware prioritization
- Follow existing code patterns (Pydantic models, module-level convenience functions, handler dispatcher)

**Non-Goals:**
- Vector/embedding-based similarity (would require new dependencies)
- Real-time index updates or caching persistence across server restarts
- Changes to MCP transport (stdio → HTTP migration is Phase 4)
- Modifying existing tool response formats or breaking existing tool contracts
- Performance optimization beyond instance-level caching

## Decisions

### 1. Jaccard similarity over embeddings for requirement matching

**Choice:** Use Jaccard coefficient on tokenized text (stopword-filtered, lowercased).

**Rationale:** Deterministic, zero external dependencies, no API calls. Compliance requirements use domain-specific vocabulary ("authentication", "audit", "encryption") where keyword overlap is a strong signal. Jaccard with compliance-tuned stopwords (removing "ensure", "operating", "system", "information") gives meaningful results for this domain.

**Alternative considered:** Embedding-based similarity via Claude API — higher quality but adds latency, cost, and complexity. Not justified for a discovery/indexing tool.

### 2. New methods on existing discovery classes (not new classes)

**Choice:** Add `get_control_rule_index()` and `find_similar_requirements()` to `ControlDiscovery`; add `get_rule_product_availability()` to `RuleDiscovery`.

**Rationale:** Follows the existing pattern where each discovery class owns its domain. Both new control tools need `self.content_repo` and existing parsing methods. The rule availability tool needs rule loading and profile scanning, which spans `RuleDiscovery` and `ProfileDiscovery`.

**Alternative considered:** A new `CrossFrameworkDiscovery` class — rejected because it would duplicate repository access patterns and not follow the established convention.

### 3. Recursive control flattening for nested structures

**Choice:** Implement recursive flattening of `controls` lists, since some CAC control files embed controls within controls (nested structure).

**Rationale:** The existing `parse_control_file()` returns a flat `controls` list for `includes`-based files, but inline controls can have nesting. The index tool must handle both patterns to provide complete coverage.

### 4. Instance-level caching for profile→rule reverse index

**Choice:** Cache the `{rule_id → [(product, profile_id)]}` reverse index on the `RuleDiscovery` instance, following the `_rule_cache` pattern at line 203 of `rules.py`.

**Rationale:** Profile scanning is expensive (iterates all profiles across all products). The reverse index needs to be built once per tool invocation session. Instance-level caching (not global) avoids stale data issues.

### 5. Optional parameters for suggest_rule_mappings enhancement

**Choice:** Add `cross_reference: bool = False` and `target_product: str | None = None` as optional parameters to the existing tool schema.

**Rationale:** Backward compatible — existing callers are unaffected. The MCP tool schema supports optional properties naturally. The AI prompt is augmented only when these flags are set.

## Risks / Trade-offs

- **[Performance] Large content repositories with 45+ control files** → Index building iterates all control files on each call. Mitigation: Instance-level caching on `ControlDiscovery`. For the MCP use case (interactive queries, not batch), this is acceptable.

- **[Correctness] `controls_dir` pattern not handled by current `parse_control_file()`** → Some CAC control files use `controls_dir` to reference a subdirectory of individual control YAML files, which differs from the `includes` pattern. Mitigation: Verify during implementation; add `controls_dir` support to `parse_control_file()` if missing.

- **[Quality] Jaccard similarity may produce low-relevance matches** → The 0.2 default threshold and 20-result cap limit noise. Users can increase `min_similarity` to filter further. Compliance-tuned stopwords improve signal quality.

- **[Scope] Profile scanning for product availability is O(products × profiles)** → Mitigation: Reverse index cache built once per instance. Profile count is bounded by the content repository size (typically < 200 profiles across all products).

- **[Integration] AI prompt modification for cross_reference may exceed context limits** → Mitigation: Limit cross-referenced rules to top 10 similar requirements' rule lists. The existing 100-rule cap in `_build_rules_context()` provides a natural bound.
