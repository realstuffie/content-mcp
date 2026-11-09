## MODIFIED Requirements

### Requirement: Profile scanning with reverse index cache
The system SHALL build a reverse index `{rule_id → [(product, profile_id)]}` on first call and share it between `RuleDiscovery` instances for the same content repository, because each MCP tool call creates a new instance. The system SHALL rebuild the index when a file it was built from is added, removed, or modified: a profile, a control file, a `rule.yml` under a rule directory that a `product.yml` names, a `product.yml`, or a `.yml` file in `product_properties`.

The system SHALL compare each file's modification time, status change time and size individually, not only the newest time. It SHALL list the rule directories again on each check, down to each rule directory, so a rule added or removed at any depth is noticed without relying on directory timestamps. When a `product.yml` changes, the rebuilt index SHALL watch the rule directories the changed file names.

#### Scenario: Cache reuse
- **WHEN** `get_rule_product_availability` is called twice, from the same or different `RuleDiscovery` instances
- **THEN** profile scanning occurs only once; the second call uses the cached reverse index

#### Scenario: Cache invalidation
- **WHEN** a profile or control file changes between two calls
- **THEN** the second call rebuilds the reverse index

#### Scenario: Rule change
- **WHEN** a rule's `platform` changes between two calls, so a profile's `filter_rules` now excludes it
- **THEN** the second call rebuilds the reverse index without that membership

#### Scenario: Change to a file that is not the newest
- **WHEN** two watched files have modification times 100 and 200, and the first one's time becomes 150
- **THEN** the next call rebuilds the reverse index

#### Scenario: Copy that keeps the modification time
- **WHEN** a watched file is replaced with contents of the same size and its old modification time
- **THEN** its new status change time makes the next call rebuild the reverse index

#### Scenario: Rule in a new nested group
- **WHEN** a rule is added in a new group nested in an existing group, or in an existing empty directory
- **THEN** the next call rebuilds the reverse index

#### Scenario: Rule directories move
- **WHEN** a `product.yml` changes its `benchmark_root` or adds `additional_content_directories`
- **THEN** the next call rebuilds the reverse index, and later changes under the new directories are noticed
