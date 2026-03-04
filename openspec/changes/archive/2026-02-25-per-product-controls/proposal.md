## Why

Upstream ComplianceAsCode/content PR #14060 introduces per-product control directories at `products/<product>/controls/`. Product-specific control files (e.g., `cis_rhel9.yml`) are being moved from the global `controls/` directory to `products/rhel9/controls/`. The `ControlsManager` now accepts a list of directories and supports override semantics (product-specific controls override global ones with the same policy ID).

content-agent's control tools currently hardcode a single `controls/` directory, so they will miss all product-specific control files once upstream adopts the new layout.

## What Changes

- **Add `product` parameter to control discovery**: `ControlDiscovery` methods gain an optional `product` parameter. When set, discovery scans both `controls/` (global) and `products/<product>/controls/` (product-specific). When unset, it scans `controls/` plus all `products/*/controls/` directories.
- **Implement override semantics**: When the same policy ID exists in both global and product-specific directories, the product-specific version wins (matching upstream behavior). A warning is logged.
- **Add `product` parameter to MCP tools**: All control-related MCP tools (`list_controls`, `get_control_details`, `get_control_stats`, `get_control_rule_index`, `find_similar_requirements`, `search_control_requirements`, `get_requirement_file_path`, `list_unmapped_requirements`, `update_requirement_rules`) gain an optional `product` string parameter.
- **Track source location on ControlFile model**: Add `source_dir` field to `ControlFile` to record which directory a control was loaded from, enabling correct path resolution for product-specific controls.
- **Update scaffolding for product-specific output**: `ControlGenerator` and `ControlUpdater` support product-specific output directories when a `product` parameter is provided.

## Non-goals

- Changing the upstream ComplianceAsCode control file format or schema.
- Multi-product merging (combining controls from multiple products in a single query) — queries scope to one product or global.
- Modifying product discovery itself — we reuse existing `ProductDiscovery` to locate product directories.

## Capabilities

### New Capabilities
- `per-product-control-discovery`: Support discovering, reading, searching, and writing control files from both `controls/` and `products/<product>/controls/` directories, with an optional `product` parameter on all control MCP tools.

### Modified Capabilities
- `control-stats`: Add optional `product` parameter to scope stats to a product's controls.
- `requirement-file-path`: Add optional `product` parameter and support resolving paths in product-specific control directories.
- `unmapped-requirements`: Add optional `product` parameter to scope unmapped listing to a product's controls.
- `requirement-rules-update`: Add optional `product` parameter to locate and update control files in product-specific directories.
- `control-rule-index`: Add optional `product` parameter to scope indexing to a product's controls.
- `similar-requirements`: Add optional `product` parameter to scope similarity search to a product's controls.

## Impact

- **Core layer** (`core/discovery/controls.py`): Major changes to `ControlDiscovery` — multi-directory scanning, override logic, product-aware path resolution.
- **Core layer** (`core/scaffolding/control_updater.py`, `control_generator.py`): Accept product-scoped output directories.
- **MCP Protocol layer** (`server/handlers/tools.py`): All control tool schemas gain optional `product` parameter; handler dispatch passes it through.
- **Models** (`models/control.py`): `ControlFile` gains `source_dir` field.
- **Backward compatible**: All changes are additive. Omitting `product` preserves current behavior (global `controls/` directory only, plus auto-discovery of all product controls).
