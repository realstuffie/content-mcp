## Why

The MCP server's discovery layer catches all exceptions (including Pydantic `ValidationError`) with broad `except Exception` blocks, returning `None` or empty lists. The MCP handler layer then tells clients "not found" when the real problem is a parse/validation error. This silently discards data — a control file with 50 requirements might show 47 with no warning, or `get_product_details("rhel9")` reports "Product not found" when the file exists but has a schema mismatch. Users cannot diagnose or fix these issues because they never learn about them.

## What Changes

- **Detail methods** (`get_product_details`, `get_rule_details`, `get_profile_details`, `get_control_details`, `get_rendered_rule`): Remove broad `except Exception` blocks around model construction. Only return `None` for genuine not-found cases (file/directory doesn't exist). Let parse and validation errors propagate to the handler's top-level `except` block, which already returns error text to the MCP client.
- **List methods** (`list_products`, `list_profiles`, `search_rules`): Introduce a `DiscoveryResult[T]` dataclass that carries both `items: list[T]` and `errors: list[str]`. Parse errors for individual items are accumulated rather than silently dropped.
- **Control file parsing** (`parse_control_file`): Track per-requirement parse failures in a new `parse_errors` field on the `ControlFile` model. The control file still loads successfully, but includes information about which requirements couldn't be parsed.
- **Silent exception blocks**: Replace `except Exception: pass` in `templates.py` with logged warnings.
- **Handler layer** (`server/handlers/tools.py`): Update list tool handlers to unpack `DiscoveryResult` and include error warnings in response text. Update control detail handlers to surface `parse_errors`.

## Non-goals

- Changing Pydantic model field optionality or defaults (e.g., making `ControlRequirement.rules` required instead of defaulting to `[]`). That's a separate model-strictness concern.
- Adding structured error codes or error models — plain error strings in the response text are sufficient for now.
- Changing build artifact error handling in `build_artifacts.py` search methods — partial results from file reads are a legitimate pattern there (OVAL/remediation components are optional).

## Capabilities

### New Capabilities
- `discovery-error-surfacing`: Error propagation and accumulation in the discovery layer so validation/parse failures are surfaced to MCP clients instead of silently discarded.

### Modified Capabilities

## Impact

- **Core logic layer** (`core/discovery/`): All 6 discovery modules changed — products, profiles, rules, controls, build_artifacts, templates.
- **Models layer** (`models/`): New `DiscoveryResult` dataclass in `models/common.py`. New `parse_errors` field on `ControlFile`.
- **MCP protocol layer** (`server/handlers/tools.py`): Handler updates for list and control-detail tools.
- **Public API** (`core/discovery/__init__.py`): Return type changes for list functions.
- **No breaking changes to MCP tool schemas**: The tool input/output JSON structure stays the same. Error information is added to the response text, not to new fields.
