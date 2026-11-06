## MODIFIED Requirements

### Requirement: Profile scanning with reverse index cache
The system SHALL build a reverse index `{rule_id → [(product, profile_id)]}` on first call and share it between `RuleDiscovery` instances for the same content repository, because each MCP tool call creates a new instance. The system SHALL rebuild the index when a profile or control file is added, removed, or modified.

#### Scenario: Cache invalidation
- **WHEN** a profile or control file changes between two calls
- **THEN** the second call rebuilds the reverse index

## ADDED Requirements

### Requirement: Product filter in rule search
When `search_rules` is called with a `product`, a rule SHALL match the product filter when any profile of that product selects it, as resolved by the reverse index, or when it has identifiers for that product.

#### Scenario: Rule selected only through a profile
- **WHEN** `search_rules` is called with `product="ubuntu2204"` and a rule has no `ubuntu2204` identifiers but a `ubuntu2204` profile selects it
- **THEN** the rule is included in the results
