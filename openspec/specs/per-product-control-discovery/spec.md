## ADDED Requirements

### Requirement: Discover controls from multiple directories

The `ControlDiscovery` class SHALL scan both the global `controls/` directory and product-specific `products/<product>/controls/` directories when listing or resolving control files. An internal `_get_controls_dirs(product: str | None)` method SHALL return an ordered list of directories:
1. `<repo>/controls/` (always included first)
2. If `product` is specified: validate that the product exists, then append `<repo>/products/<product>/controls/` (if it exists)
3. If `product` is `None`: enumerate all known products and append existing `<repo>/products/<product>/controls/` directories (sorted alphabetically)

A known product SHALL be a directory under `<repo>/products/` that has a `product.yml`. The check SHALL list directories without reading each `product.yml`, and SHALL read the directories on every call. When `product` is specified but not known, the method SHALL raise a `ValueError` with a descriptive message.

#### Scenario: Product specified with product controls directory

- **WHEN** `_get_controls_dirs(product="rhel9")` is called and `rhel9` is a known product and `products/rhel9/controls/` exists
- **THEN** the result SHALL be `[<repo>/controls/, <repo>/products/rhel9/controls/]`

#### Scenario: Product specified without product controls directory

- **WHEN** `_get_controls_dirs(product="fedora")` is called and `fedora` is a known product but `products/fedora/controls/` does not exist
- **THEN** the result SHALL be `[<repo>/controls/]`

#### Scenario: Invalid product raises error

- **WHEN** `_get_controls_dirs(product="nonexistent")` is called and `nonexistent` is not a known product
- **THEN** a `ValueError` SHALL be raised with a message indicating the product is not recognized

#### Scenario: No product specified discovers all product controls

- **WHEN** `_get_controls_dirs(product=None)` is called and known products `rhel8` and `rhel9` both have `controls/` directories
- **THEN** the result SHALL be `[<repo>/controls/, <repo>/products/rhel8/controls/, <repo>/products/rhel9/controls/]`

### Requirement: Override semantics for duplicate policy IDs

When the same policy ID (YAML filename stem) exists in multiple control directories, the file from the later directory in the scan order SHALL override the earlier one. A warning SHALL be logged when an override occurs, including the paths of both files.

#### Scenario: Product control overrides global control

- **WHEN** `list_controls(product="rhel9")` is called and both `controls/cis_rhel9.yml` and `products/rhel9/controls/cis_rhel9.yml` exist
- **THEN** `cis_rhel9` SHALL appear once in the result, and `get_control_details("cis_rhel9", product="rhel9")` SHALL load from `products/rhel9/controls/cis_rhel9.yml`

#### Scenario: Warning logged on override

- **WHEN** a policy ID exists in both global and product-specific directories
- **THEN** a warning SHALL be logged containing both file paths

### Requirement: list_controls accepts optional product parameter

The `list_controls` method and its module-level convenience function SHALL accept an optional `product: str | None` parameter. The MCP tool `list_controls` SHALL include an optional `product` string in its `inputSchema`.

#### Scenario: list_controls with product

- **WHEN** `list_controls(product="rhel9")` is called
- **THEN** the result SHALL include control IDs from both `controls/` and `products/rhel9/controls/`, with product-specific overrides applied

#### Scenario: list_controls without product

- **WHEN** `list_controls()` is called without a product parameter
- **THEN** the result SHALL include control IDs from `controls/` and all `products/*/controls/` directories

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

#### Scenario: Product-specific control loaded

- **WHEN** `get_control_details("cis_rhel9", product="rhel9")` is called and `products/rhel9/controls/cis_rhel9.yml` exists
- **THEN** the returned `ControlFile` SHALL be parsed from the product-specific file, with `source_dir` set to `products/rhel9/controls/`

#### Scenario: Global control loaded when no product override

- **WHEN** `get_control_details("anssi", product="rhel9")` is called and `anssi.yml` exists only in `controls/`
- **THEN** the returned `ControlFile` SHALL be parsed from `controls/anssi.yml`, with `source_dir` set to `controls/`

### Requirement: search_control_requirements accepts optional product parameter

The `search_controls` method, its convenience function, and the `search_control_requirements` MCP tool SHALL accept an optional `product` parameter to scope the search.

#### Scenario: Search scoped to product

- **WHEN** `search_controls(query="password", product="rhel9")` is called
- **THEN** only controls visible to `rhel9` (global + rhel9 product-specific, with overrides) SHALL be searched

### Requirement: ControlFile source_dir field

The `ControlFile` Pydantic model SHALL include a `source_dir: Path | None` field (default `None`). This field records the directory from which the control file was loaded.

#### Scenario: source_dir set on load

- **WHEN** a `ControlFile` is parsed from `products/rhel9/controls/cis_rhel9.yml`
- **THEN** `source_dir` SHALL be set to the `Path` representing `products/rhel9/controls/`

#### Scenario: source_dir is None for legacy code

- **WHEN** a `ControlFile` is constructed without specifying `source_dir`
- **THEN** `source_dir` SHALL default to `None`

### Requirement: MCP tool schemas include optional product parameter

All control-related MCP tools (`list_controls`, `get_control_details`, `get_control_stats`, `get_control_rule_index`, `find_similar_requirements`, `search_control_requirements`, `get_requirement_file_path`, `list_unmapped_requirements`, `update_requirement_rules`) SHALL include an optional `product` string parameter in their `inputSchema` properties.

#### Scenario: Tool schema includes product

- **WHEN** the MCP server lists the `list_controls` tool schema
- **THEN** the `inputSchema.properties` SHALL include `product` with `type: "string"` and a description indicating it scopes to a product's controls

#### Scenario: Tools work without product parameter

- **WHEN** any control MCP tool is called without the `product` parameter
- **THEN** tools that read one policy SHALL resolve it as `get_control_details` does, returning its error for a policy several products define
- **AND** `get_control_rule_index` and `find_similar_requirements` SHALL include each product's version of such a policy, and every requirement they return SHALL carry `product`: the product whose file it comes from, or null for a global file
- **AND** `search_control_requirements` without `control_id` SHALL leave such policies out and name them in its result

### Requirement: generate_control_files accepts optional product parameter

The `generate_control_files` MCP tool and `ControlGenerator.generate_control_structure()` SHALL accept an optional `product` parameter. When set, the default output directory SHALL be `products/<product>/controls/` instead of `controls/`.

#### Scenario: Generate into product controls directory

- **WHEN** `generate_control_structure(policy_id="my_policy", ..., product="rhel9")` is called without an explicit `output_dir`
- **THEN** the parent file SHALL be created at `products/rhel9/controls/my_policy.yml` and requirement files at `products/rhel9/controls/my_policy/`

#### Scenario: Generate into global directory without product

- **WHEN** `generate_control_structure(policy_id="my_policy", ...)` is called without a `product` parameter
- **THEN** the output SHALL be in `controls/my_policy.yml` as before
