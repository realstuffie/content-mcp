## Context

The discovery layer (`core/discovery/`) has 6 modules (products, profiles, rules, controls, build_artifacts, templates) that load data from the ComplianceAsCode/content repository. Every module follows the same anti-pattern: broad `except Exception` blocks catch all errors during YAML parsing and Pydantic model construction, returning `None` or skipping items. The MCP handler layer (`server/handlers/tools.py`) then interprets `None` as "not found" — indistinguishable from a genuinely missing entity.

The architecture has three layers relevant to this change:
```
MCP Handlers (server/handlers/tools.py)  ← surfaces results to client
  → Discovery Layer (core/discovery/)    ← where errors are swallowed
    → Content Repository (filesystem)    ← where data lives
```

The handler already has a top-level `except Exception` (line 1278) that returns error text to the MCP client. If the discovery layer stopped swallowing errors, they would naturally reach this handler and be reported.

## Goals / Non-Goals

**Goals:**
- Parse/validation errors in discovery methods are surfaced to MCP clients as error messages
- List methods report how many items failed to parse alongside successful results
- Control file parsing reports which individual requirements failed to parse
- All `except Exception: pass` blocks are replaced with at minimum a logged warning

**Non-Goals:**
- Changing Pydantic model strictness (field optionality, defaults, `extra="allow"`)
- Adding structured error codes or error response models
- Changing build_artifacts search methods (partial results from optional file reads is legitimate)
- Changing MCP tool input/output schemas

## Decisions

### 1. Use a generic `DiscoveryResult[T]` dataclass for list methods

**Decision**: Introduce a `DiscoveryResult` generic dataclass that wraps `items: list[T]` and `errors: list[str]`.

**Why not return `tuple[list[T], list[str]]`**: Tuples are positional and error-prone. A named type is self-documenting and extensible.

**Why a dataclass, not a Pydantic model**: `DiscoveryResult` is an internal transport type between discovery and handler layers. It never gets serialized to JSON or sent over the wire. A `dataclass` avoids Pydantic overhead and Generic complexity.

**Why not add errors to each item model**: List methods return homogeneous items. Errors represent items that *couldn't* be constructed — they don't have a model to attach to.

### 2. Let detail method errors propagate instead of catching them

**Decision**: Remove `except Exception` blocks around model construction in detail methods. Keep `return None` only for genuine not-found cases (file/directory doesn't exist on disk).

**Why not wrap in a result type too**: Detail methods either succeed or fail entirely. There's no partial success. The handler's existing top-level `except` (line 1278) already converts exceptions to error text for the client. Adding a result wrapper would be unnecessary complexity.

**Alternative considered**: Custom exception types (e.g., `DiscoveryParseError`). Rejected because the handler already catches `Exception` generically — custom types add indirection without benefit at this stage.

### 3. Add `parse_errors` field to `ControlFile` model

**Decision**: Add `parse_errors: list[str] = Field(default_factory=list)` to the `ControlFile` Pydantic model.

**Why on the model, not on `DiscoveryResult`**: Control files have a parent-child structure. The parent file parses successfully, but individual requirements may fail. This is partial success within a single entity — different from list methods where each item is independent. The errors belong on the model because they describe the model's own completeness.

### 4. Keep per-file catches in build_artifacts search methods

**Decision**: `search_rendered_content()` and per-component reads (OVAL, remediations) in `get_rendered_rule()` keep their `try/except` blocks.

**Why**: These are optional components. A rule can have rendered YAML without OVAL. A search can return partial results when some files are unreadable. This is legitimate graceful degradation, not error suppression.

## Risks / Trade-offs

- **[Risk] Errors that were previously silent now surface to users** → This is the goal, but some errors may be noisy (e.g., a known-broken file in the content repo). Mitigation: errors appear in response text, not as MCP protocol errors, so the client can still process successful results.

- **[Risk] `_load_rule_yaml` fallback from SSG expansion to direct YAML** → This silent fallback is intentional (SSG modules may not be available). Keeping this as-is; it's a recovery path, not error suppression. Adding a logged warning when fallback is used.

- **[Trade-off] Detail methods now raise instead of returning None on parse errors** → Callers that chain detail method results (e.g., `get_control_rule_index` calling `get_control_details` in a loop) need to handle exceptions. Mitigation: these internal callers get their own per-item try/except that accumulates errors, matching the list method pattern.

- **[No migration needed]**: No MCP tool schema changes. No database. No external API changes. This is a pure behavior change in error handling.
