## Context

The `generate_control_files` MCP tool currently only generates directory-based control file structures (parent YAML + directory of individual requirement files). ComplianceAsCode supports both this format and a monolithic inline format. The codebase already handles both formats at the read/update layers (`ControlUpdater`, `ControlValidator`, `ControlDiscovery`) but not at the generation layer.

A deprecated `nested_by_section` parameter and associated dead code (`_group_by_section`, `_clean_section_id`) remain in the generator from a previous design that organized requirements into subdirectories by section.

## Goals / Non-Goals

**Goals:**
- Allow callers to choose between inline and directory output formats when generating control files
- Force an explicit format choice (no default) so callers are aware of the tradeoff
- Clean up dead code left from the deprecated `nested_by_section` feature

**Non-Goals:**
- Changing downstream consumers (validators, updater, reviewer, discovery) — they already handle both formats
- Modifying the `ControlGenerationResult` model
- Adding auto-selection heuristics based on requirement count

## Decisions

### 1. Branch in `generate_control_structure` based on `format` parameter

The `format` parameter (`Literal["inline", "directory"]`) is added to `generate_control_structure()`. The method branches early:
- `"directory"`: existing behavior — creates `<policy_id>.yml` parent + `<policy_id>/` directory with individual files
- `"inline"`: creates a single `<policy_id>.yml` with metadata and all requirements in a `controls:` list

**Why not a separate method?** The setup logic (output directory resolution, requirement conversion, existence checks) is shared. A single method with an early branch keeps the interface simple and avoids duplicating the shared setup.

### 2. Inline file structure follows ComplianceAsCode conventions

The inline file includes: `policy`, `title`, `id`, `version` (optional), `source` (optional), `levels`, and `controls` (the requirement list). No `controls_dir` field — its absence is how downstream code distinguishes inline from directory format.

### 3. Reuse `generate_requirement_file` logic for building control items

The existing `generate_requirement_file` method builds a well-structured control item dict. For inline mode, a new private method `_build_control_item` extracts the dict-building logic so it can be reused without writing to a file. Both the directory path (via `generate_requirement_file`) and inline path (via `_build_control_item`) produce identical control item structures.

### 4. MCP tool schema: `format` is required, `nested_by_section` removed

The `format` parameter is added to both `properties` and `required` in the tool's `inputSchema`. `nested_by_section` is removed entirely. This is a breaking change but `nested_by_section` was already a no-op.

### 5. Result shape for inline mode

`ControlGenerationResult` for inline: `parent_file_path` points to the single file, `requirement_files` is `[]`, `total_requirements` reflects the count. No model changes needed.

## Risks / Trade-offs

- **Breaking change for callers not passing `format`** → Acceptable since this is a new required parameter. Callers will get a clear validation error with the expected values.
- **Inline files can get large for policies with many requirements** → This is the caller's choice. The tool description can mention the tradeoff.

## Architectural Fit

This change is scoped to two layers:
- **Core logic** (`core/scaffolding/control_generator.py`): Generation path branching and dead code removal
- **MCP protocol** (`server/handlers/tools.py`): Tool schema update and parameter forwarding

No async considerations — the generator is synchronous (file I/O only).
