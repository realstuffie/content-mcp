## Why

The test suite called resource and tool handlers directly. Those calls missed
failures at the MCP boundary. A live resource read failed because the SDK passed
an `AnyUrl` object to code that expected a string. Further session tests found
incorrect resource discovery, MIME types, timestamp serialization, and error
reporting.

## What changes

- Add tests that exchange MCP messages through SDK sessions. Exercise all 25
  reading and validation tools against a temporary repository.
- Add a subprocess test for the actual stdio entry point against a real content
  checkout. Check initialization, replies, stdout, and shutdown at EOF.
- Convert resource URIs to strings at the server boundary. Return JSON resource
  contents with `application/json` and serialize model timestamps as JSON values.
- List parameterized resources through `resources/templates/list`. Keep concrete
  collection URIs in `resources/list`.
- Reject extra segments in rendered-rule resource paths.
- Return tool execution failures with `isError: true`. Distinguish resource
  lookup failures, invalid routes, and parse failures with JSON-RPC error codes.
- Document the protocol behavior and test commands.

## Capabilities

### New capabilities

- `mcp-protocol`: resource discovery and serialization, error reporting, SDK
  session tests, and stdio lifecycle tests.

## Scope

Rule generation and requirement updates are outside the new test suite's scope.
The shared tool dispatcher now lets the SDK flag exceptions from any tool.
Failed requirement-update results also raise through that dispatcher. Their
file-editing behavior does not change.

The existing `product: null` issue in `list_unmapped_requirements` is separate
from protocol handling and remains open.

## Impact

Clients must use `resources/templates/list` to discover parameterized URIs.
Existing concrete resource URIs and tool success payloads stay the same.
Direct Python callers of `handle_tool_call` now receive `ValueError` on execution
failures instead of a list containing error text. The MCP SDK converts these
exceptions to tool results with `isError: true`.
