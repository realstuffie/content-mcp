## MODIFIED Requirements

### Requirement: get_control_details accepts optional product parameter

The `get_control_details` method and its module-level convenience function SHALL accept an optional `product: str | None` parameter. With a product, the method SHALL search control directories in order and return the last matching file (override semantics). Without one, it SHALL use the global file when there is one; otherwise the file of the only product that defines the policy, expanded with that product's variables; and when several products define the policy, it SHALL raise `AmbiguousControlError`, a `ValueError` whose message names the products. The loaded `ControlFile` SHALL have its `source_dir` field set to the directory containing the file.

#### Scenario: Policy several products define, without a product

- **WHEN** `get_control_details("nist_800_53")` is called and only `products/fedora`, `rhel8`, `rhel9` and `rhel10` define it
- **THEN** `AmbiguousControlError` SHALL be raised, naming the four products, instead of one product's file being used

#### Scenario: Policy one product defines, without a product

- **WHEN** `get_control_details("stig_rhel9")` is called and only `products/rhel9/controls/stig_rhel9.yml` exists
- **THEN** the returned `ControlFile` SHALL be parsed from that file

#### Scenario: Global file without a product

- **WHEN** `get_control_details("shared")` is called and both `controls/shared.yml` and `products/rhel9/controls/shared.yml` exist
- **THEN** the returned `ControlFile` SHALL be parsed from `controls/shared.yml`; the product's file overrides it only for `rhel9`

### Requirement: MCP tool schemas include optional product parameter

#### Scenario: Tools work without product parameter

- **WHEN** any control MCP tool is called without the `product` parameter
- **THEN** tools that read one policy SHALL resolve it as `get_control_details` does, returning its error for a policy several products define
- **AND** `get_control_rule_index` and `find_similar_requirements` SHALL include each product's version of such a policy, and every requirement they return SHALL carry `product`: the product whose file it comes from, or null for a global file
- **AND** `search_control_requirements` without `control_id` SHALL leave such policies out and name them in its result
