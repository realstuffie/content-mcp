## Context

The ComplianceAsCode/content project is introducing per-product control directories (PR #14060). Product-specific control files (e.g., `cis_rhel9.yml`) move from the global `controls/` to `products/<product>/controls/`. The upstream `ControlsManager` now accepts a list of directories and applies override semantics: product-specific controls replace global ones sharing the same policy ID.

content-agent's `ControlDiscovery` class currently hardcodes `self.content_repo.path / "controls"` as the sole controls directory. This is used by all control MCP tools (list, details, stats, index, search, path resolution, update). The `ControlUpdater` and `ControlGenerator` scaffolding modules similarly hardcode the global path.

The existing `ProductDiscovery` class already knows how to enumerate product directories at `products/<product>/`, which we can reuse to locate per-product control directories.

## Goals / Non-Goals

**Goals:**
- Make all control discovery methods scan both `controls/` and `products/<product>/controls/`
- Add an optional `product` parameter to all control-related MCP tools to scope queries to a specific product
- Implement upstream-compatible override semantics (product controls win over global, with a logged warning)
- Track the source directory on loaded `ControlFile` objects for correct path resolution
- Update scaffolding tools to generate/update controls in product-specific directories

**Non-Goals:**
- Multi-product merge queries (combining controls from several products in one call)
- Changing the upstream YAML schema or control file format
- Modifying `ProductDiscovery` itself
- Supporting product controls without a corresponding `products/<product>/` directory

## Decisions

### 1. Add `product` parameter to `ControlDiscovery` methods rather than constructor

**Decision**: Each `ControlDiscovery` method (`list_controls`, `get_control_details`, etc.) gains an optional `product: str | None` parameter.

**Rationale**: `ControlDiscovery` is instantiated fresh per call (no persistent state), so passing `product` at the method level is simpler than threading it through the constructor. This also matches the existing pattern where each module-level convenience function creates a new `ControlDiscovery()`.

**Alternative considered**: Adding `product` to `__init__`. Rejected because it would require changing all call sites to pass product upfront, and the class is already stateless per invocation.

### 2. Internal `_get_controls_dirs(product)` helper to resolve directories

**Decision**: Add a private method `_get_controls_dirs(product: str | None) -> list[Path]` that returns the ordered list of control directories to scan:
- Always includes `<repo>/controls/` first
- If `product` is specified: appends `<repo>/products/<product>/controls/` if it exists
- If `product` is `None`: appends all existing `<repo>/products/*/controls/` directories (sorted)

**Rationale**: Centralizes directory resolution logic. The ordering (global first, product-specific second) matches upstream override semantics where later entries win.

### 3. Override semantics via ordered dict merge

**Decision**: When listing or resolving controls, iterate directories in order and build a `dict[str, Path]` mapping policy ID to file path. Later entries (product-specific) overwrite earlier ones (global). Log a warning when an override occurs.

**Rationale**: Matches upstream `ControlsManager._load()` behavior exactly. The dict approach is simple and avoids complex merge logic.

### 4. Add `source_dir` field to `ControlFile` model

**Decision**: Add `source_dir: Path | None = None` to the `ControlFile` Pydantic model. This records the directory from which the control was loaded (e.g., `controls/` or `products/rhel9/controls/`).

**Rationale**: Required for correct path resolution in `get_requirement_file_path` and `update_requirement_rules` — these need to know where the control file physically lives, which is no longer always `controls/`.

**Alternative considered**: Storing the full file path instead of directory. Rejected because `source_dir` is more versatile and aligns with how `controls_dir` subdirectories are resolved (relative to the parent file's directory).

### 5. Product validation uses ProductDiscovery

**Decision**: When `product` is specified, validate it against known products using `ProductDiscovery` (which relies on SSG modules). If the product is not recognized, return an error rather than silently falling back to global-only results.

**Rationale**: SSG modules are always available — they are loaded at startup and many other features depend on them. Using `ProductDiscovery` provides proper validation and catches typos early. A raw filesystem check would silently degrade, making debugging harder for users.

### 6. MCP tool schema changes are additive

**Decision**: All control MCP tools gain an optional `product` string parameter in their `inputSchema`. The parameter is not required, preserving backward compatibility.

**Rationale**: Existing tool consumers (Claude Desktop, other MCP clients) can ignore the new parameter. No breaking changes.

### 7. Scaffolding output directory parameterized via `product`

**Decision**: `ControlGenerator.generate_control_structure()` and `ControlUpdater.update_requirement_rules()` accept an optional `product` parameter. When set, the output/lookup directory becomes `products/<product>/controls/` instead of `controls/`.

**Rationale**: Follows the same pattern as discovery. The generator already has an `output_dir` parameter; for product-specific generation, it defaults to `products/<product>/controls/`.

## Risks / Trade-offs

**[Risk] No product controls directory exists yet** → For new content repos or products that haven't adopted the new layout, `_get_controls_dirs` simply returns only the global directory. No behavior change.

**[Risk] Policy ID collisions without product scoping** → When `product=None`, all product control directories are scanned, and a policy ID appearing in multiple products would cause unexpected overrides. → Mitigation: Log a warning for each override including source paths. Users should specify `product` for product-specific work.

**[Risk] Performance with many products** → Scanning all `products/*/controls/` directories adds filesystem ops. → Mitigation: The glob is cheap (just directory listing), and the number of products is small (typically <20). No caching needed at this stage.

**[Trade-off] Product validation couples ControlDiscovery to ProductDiscovery** → `ControlDiscovery` now depends on `ProductDiscovery` (and transitively on SSG modules) for product validation. → Acceptable because SSG modules are always loaded at startup and this coupling already exists in other parts of the codebase. The benefit is early, clear error messages on invalid product names.

## Open Questions

None — the upstream PR #14060 behavior is well-defined and we are matching it.
