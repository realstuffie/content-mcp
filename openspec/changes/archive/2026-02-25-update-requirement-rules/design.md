## Context

The `map-controls` skill workflow currently relies on the LLM issuing `Read` + `Edit` tool calls to update control files after mapping decisions. Control files come in two formats:

1. **Inline** — monolithic YAML (e.g., `controls/anssi.yml`) with all requirements in a `controls:` list
2. **Directory-based** — a parent YAML pointing to a `controls_dir` subdirectory with one file per requirement

Both formats may contain Jinja2 templating (`{{{ full_name }}}`, `{% ... %}`), YAML comments, and multiline scalars (`>-`, `|-`). LLM-driven editing of these files is error-prone, motivating a deterministic MCP tool.

The `ControlUpdateResult` model already exists at `models/control.py:368`. The `ControlDiscovery` class in `core/discovery/controls.py` already handles locating control files and resolving `controls_dir`. The `ControlValidator` in `core/scaffolding/control_validators.py` provides a validation pattern to follow.

## Goals / Non-Goals

**Goals:**
- Deterministic, format-preserving updates to `rules` and `status` fields in control requirements
- Support both inline and directory-based control file formats
- Preserve Jinja2 templating, YAML comments, and formatting
- Fit into the existing scaffolding layer alongside `control_generator.py` and `control_validators.py`

**Non-Goals:**
- Batch updates (multiple requirements per call)
- Creating new requirements or modifying fields beyond `rules` and `status`
- Full YAML round-trip parsing (explicitly avoided to protect Jinja2)

## Decisions

### 1. Text-based editing over YAML round-trip

**Decision**: Use line-by-line text manipulation instead of `yaml.safe_load()` → modify → `yaml.dump()`.

**Rationale**: Control files frequently contain Jinja2 syntax (`{{{ full_name }}}`), YAML comments, and carefully formatted multiline scalars. `yaml.dump()` would destroy all of these. Text-based editing is more complex but preserves the file exactly except for the targeted fields.

**Alternative considered**: YAML round-trip via `ruamel.yaml` — would preserve comments and formatting but still mangle Jinja2 syntax. Adds a new dependency for marginal benefit.

### 2. Unified text-based approach for both formats

**Decision**: Use the same text-based editing approach for both inline and directory-based files, rather than using `yaml.dump()` for directory files and text editing for inline.

**Rationale**: Directory-based files can also contain Jinja2 (e.g., `srg_gpos` files). A single code path is simpler and safer than format-specific branching with edge cases.

### 3. New module in scaffolding layer

**Decision**: Create `core/scaffolding/control_updater.py` with a `ControlUpdater` class.

**Rationale**: Follows the existing pattern — `control_generator.py` creates files, `control_validators.py` validates them, `control_updater.py` modifies them. All are stateless classes instantiated per-call in the handler.

### 4. Synchronous implementation

**Decision**: The `update_requirement_rules` method is synchronous (not async), matching `ControlValidator.validate_control_file()`.

**Rationale**: The operation is pure file I/O on the local filesystem with no network calls. The handler wraps it synchronously, consistent with existing scaffolding tools. Async would add complexity for no benefit.

### 5. Replace semantics for rules

**Decision**: The `rules` parameter replaces the entire rules list rather than appending.

**Rationale**: The caller (skill) handles merge logic and presents the final list. Replace semantics are simpler, idempotent, and avoid duplicate-detection complexity.

## Risks / Trade-offs

- **[Regex fragility]** → Text-based parsing depends on consistent YAML formatting. Mitigated by: handling common quoting variations (`- id: R1`, `- id: "R1"`), using indentation-based block detection rather than content-specific parsing.
- **[Concurrent edits]** → No file locking. Mitigated by: MCP server is single-session, and control file editing is sequential within a skill workflow.
- **[Indentation mismatch]** → Inserted rules block could use wrong indentation. Mitigated by: detecting the indentation of the existing requirement block and matching it.
