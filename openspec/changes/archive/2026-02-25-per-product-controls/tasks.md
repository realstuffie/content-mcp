## 1. Model Changes

- [x] 1.1 Add `source_dir: Path | None = None` field to `ControlFile` model in `models/control.py`

## 2. Core Discovery Layer

- [x] 2.1 Add `_get_controls_dirs(product: str | None) -> list[Path]` helper to `ControlDiscovery` that validates the product via `ProductDiscovery` (raises `ValueError` for unknown products) and returns ordered list of control directories (global first, then product-specific)
- [x] 2.2 Update `list_controls()` to accept optional `product` parameter, scan all resolved directories, and apply override semantics (later dirs win for duplicate policy IDs, log warning)
- [x] 2.3 Update `get_control_details()` to accept optional `product` parameter, resolve control file from product-aware directories, and set `source_dir` on the returned `ControlFile`
- [x] 2.4 Update `parse_control_file()` to accept and propagate `source_dir` to the `ControlFile` it returns
- [x] 2.5 Update `search_controls()` to accept optional `product` parameter and pass it through to `list_controls` and `get_control_details`
- [x] 2.6 Update `get_control_rule_index()` to accept optional `product` parameter and pass it through to `list_controls` and `get_control_details`
- [x] 2.7 Update `get_control_stats()` to accept optional `product` parameter and pass it through to `get_control_details`
- [x] 2.8 Update `find_similar_requirements()` to accept optional `product` parameter and pass it through to `get_control_rule_index`
- [x] 2.9 Update `get_requirement_file_path()` to accept optional `product` parameter and resolve control file from product-aware directories using `source_dir` for correct path resolution
- [x] 2.10 Update `list_unmapped_requirements()` to accept optional `product` parameter and pass it through to `get_control_details`
- [x] 2.11 Update all module-level convenience functions in `controls.py` to accept and pass through the `product` parameter

## 3. Scaffolding Layer

- [x] 3.1 Update `ControlUpdater.update_requirement_rules()` to accept optional `product` parameter and resolve control file from product-aware directories
- [x] 3.2 Update `ControlGenerator.generate_control_structure()` to accept optional `product` parameter, defaulting output directory to `products/<product>/controls/` when product is set
- [x] 3.3 Update `ControlValidator.validate_control_directory()` to support product control directories

## 4. MCP Tool Schemas and Handlers

- [x] 4.1 Add optional `product` string parameter to `inputSchema` of all control MCP tools: `list_controls`, `get_control_details`, `get_control_stats`, `get_control_rule_index`, `find_similar_requirements`, `search_control_requirements`, `get_requirement_file_path`, `list_unmapped_requirements`, `update_requirement_rules`, `generate_control_files`
- [x] 4.2 Update `handle_tool_call` dispatch in `tools.py` to extract and pass `product` argument to core layer functions for all affected tools

## 5. Tests

- [x] 5.1 Add unit tests for `_get_controls_dirs` with valid product, without product, with product that has no controls dir, and with invalid product (expect `ValueError`)
- [x] 5.2 Add unit tests for override semantics in `list_controls` (duplicate policy ID in global and product dirs)
- [x] 5.3 Add unit tests for `get_control_details` loading from product-specific directory and setting `source_dir`
- [x] 5.4 Add unit tests for `get_requirement_file_path` resolving paths in product-specific control directories
- [x] 5.5 Add unit tests for `update_requirement_rules` with product parameter targeting product-specific control files
- [x] 5.6 Add unit tests for `generate_control_structure` with product parameter writing to product-specific directory
- [x] 5.7 Update existing control tests to verify backward compatibility (no product parameter = same behavior as before)

## 6. Linting and Type Checking

- [x] 6.1 Run `mypy src/` and fix any type errors introduced by the changes
- [x] 6.2 Run `black --check src/ tests/` and `ruff check src/ tests/` to verify formatting and lint compliance

## 7. Documentation

- [x] 7.1 Update `docs/api_reference.md` to document the new `product` parameter on all affected MCP tools
- [x] 7.2 Update the "Available Tools" list in `README.md` to reflect the new `product` parameter
