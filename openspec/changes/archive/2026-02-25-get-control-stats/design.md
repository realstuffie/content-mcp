## Context

The `get_control_details` tool returns the full control file including all requirements. When an AI assistant needs summary statistics (e.g., "how many requirements are mapped?"), it must count items in the response — a task LLMs perform unreliably. Other discovery tools like `get_control_rule_index` already follow the pattern of providing purpose-built views of control data.

## Goals / Non-Goals

**Goals:**
- Provide a single MCP tool call that returns deterministic requirement counts
- Break down counts by status, mapped/unmapped, and total
- Keep the response compact (no requirement details transferred)

**Non-Goals:**
- Aggregation across multiple control files
- Filtering or querying within the stats
- Caching or performance optimization (control files are small enough for on-demand computation)

## Decisions

### 1. Synchronous implementation (no async)

The `ControlDiscovery` class and its methods (`get_control_details`, `_flatten_controls`) are synchronous. The new `get_control_stats` method follows the same pattern. The MCP handler calls it synchronously, consistent with other discovery tool handlers.

**Alternative**: Making it async would require converting `ControlDiscovery` internals, which is out of scope and unnecessary for file-based reads.

### 2. New `ControlStats` Pydantic model in `models/control.py`

A dedicated model provides type safety, serialization via `model_dump`, and self-documenting fields. Placed alongside existing control models (`ControlFile`, `ControlRuleIndex`).

**Alternative**: Returning a plain dict — rejected because it bypasses the project's consistent use of Pydantic models and loses validation/documentation benefits.

### 3. Module-level convenience function

Following the pattern established by `get_control_rule_index` in `core/discovery/controls.py`, a module-level function wraps the class method. This keeps the MCP handler code simple (single import, single call).

### 4. MCP tool handler placement

The handler goes in `server/handlers/tools.py` alongside `get_control_details`, using the same lazy-import pattern. The tool definition follows the existing schema structure in the `TOOLS` list.

## Risks / Trade-offs

- **Counting logic duplication** — The concept of "mapped" (has rules) vs "unmapped" (no rules) is defined here and could drift from other tools. → Mitigation: Uses the same `_flatten_controls` method as `get_control_rule_index`, keeping the data source consistent.
- **Status values** — The canonical statuses are defined in the upstream ComplianceAsCode control schema (`shared/schemas/control.json`): `automated`, `documentation`, `does not meet`, `inherently met`, `manual`, `not applicable`, `partial`, `pending`, `planned`, `supported`. The `by_status` dict only includes statuses actually present in the control file (no zero-count padding). Requirements without a status are counted as having no status (key: requirements with `status` field unset are excluded from `by_status` but still counted in `total`).
- **No async** — Synchronous file reads could block the event loop for very large control files. → Mitigation: Control files in practice are small (hundreds of requirements, not thousands). This matches existing discovery tool behavior.
