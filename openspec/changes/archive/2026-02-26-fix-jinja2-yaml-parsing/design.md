## Context

`RuleDiscovery` in `core/discovery/rules.py` loads rule YAML files using `yaml.load(content, Loader=yaml.FullLoader)` directly on raw file content. This works for most rules, but 242 rule files contain Jinja2 block-level control structures (`{% if product == "rhel10" %}`) that are not valid YAML. These cause `ScannerError`, which is silently caught, making the rules invisible to `get_rule_details` and `search_rules`.

The SSG Python module (already loaded at startup via `core/integration/ssg_modules.py`) provides `ssg.yaml.open_and_expand()`, which processes Jinja2 templates before YAML parsing — exactly what the build system uses.

## Goals / Non-Goals

**Goals:**
- Make all 242+ rules with Jinja2 control structures discoverable via MCP tools
- Use existing SSG infrastructure (`ssg.yaml.open_and_expand`) rather than writing custom Jinja2 handling
- Support product-specific expansion when `product` parameter is provided
- Provide graceful fallback to raw YAML parsing if SSG expansion fails

**Non-Goals:**
- Adding Jinja2 expansion to other discovery modules (profiles, controls, templates)
- Changing MCP tool API signatures
- Handling rules that are invalid even after Jinja2 expansion

## Decisions

### 1. Use `ssg.yaml.open_and_expand()` instead of custom Jinja2 stripping

**Decision**: Delegate to the SSG module's built-in template expansion.

**Alternatives considered**:
- *Regex-strip Jinja2 blocks before YAML parsing*: Fragile, loses product-specific content, risks breaking valid YAML structure.
- *Custom Jinja2 environment*: Duplicates SSG's macro loading and template resolution logic.

**Rationale**: `open_and_expand` is battle-tested in the build system, handles macro loading from `shared/macros/`, and produces the same output the build pipeline does. It's already available via `get_ssg_modules().yaml`.

### 2. Centralize YAML loading in a `_load_rule_yaml` helper

**Decision**: Add a single private method `_load_rule_yaml(rule_path, product)` to `RuleDiscovery` that encapsulates the expand-then-parse logic.

**Rationale**: Both `get_rule_details` and `_load_search_result` need the same loading logic. A helper avoids duplication and provides a single place to add fallback handling.

### 3. Empty substitutions dict for product-less queries

**Decision**: When no `product` is provided, call `open_and_expand(path, {})`. This causes all `{% if product == ... %}` conditionals to evaluate to false, producing a generic fallback.

**Rationale**: Core metadata (title, severity, identifiers, references) is almost never inside conditionals. The generic fallback is sufficient for discovery and search. Product-specific content (warnings, platform constraints) requires the `product` parameter.

### 4. Fallback to raw `yaml.load()` on SSG expansion failure

**Decision**: If `ssg.yaml.open_and_expand()` raises any exception, fall back to direct `yaml.load()`.

**Rationale**: Preserves current behavior for non-templated files if the SSG module has issues. The fallback is the existing code path, so it can't make things worse.

## Risks / Trade-offs

- **[Performance]** `open_and_expand` does Jinja2 template processing, which is slower than direct `yaml.load()`. → Mitigated: only affects rule loading, not bulk operations. `search_rules` already iterates rules individually.
- **[Macro availability]** `open_and_expand` loads macros from `shared/macros/` in the content repo. If macros are missing, expansion may fail. → Mitigated: fallback to raw YAML loading.
- **[Generic fallback accuracy]** With empty substitutions, `{% set %}` variables resolve to empty strings, which may produce slightly odd text in description fields. → Acceptable: core metadata is unaffected, and users can pass `product` for accurate content.

## Architectural Fit

This change is confined to the **core business logic layer** (`core/discovery/rules.py`). It uses the existing **integration layer** (`core/integration/ssg_modules.py`) to access SSG modules. No changes to the **MCP protocol layer** — existing tool signatures and parameter threading are sufficient.
