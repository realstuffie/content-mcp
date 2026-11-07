## Context

Direct handler tests bypass the SDK's URI conversion, request validation, and
response serialization. They can pass while the same request fails over MCP.
The first live resource test exposed an `AnyUrl` conversion failure. The broader
suite added in this change exposed more failures in the same boundary code.

## Decisions

### Test sessions with temporary content

Use the SDK's connected memory streams to exchange MCP messages with
`ContentAgentServer`. Create a small repository with a product, profile, rule,
template, control policy, and build artifacts. The fixture includes timestamps
and Unicode text. It mocks SSG expansion with a YAML loader, so these tests check
protocol handling rather than duplicate the real-content expansion tests.

Enter and exit each SDK session inside the test task. AnyIO cancel scopes must
exit in the same task that entered them. An async generator fixture under
pytest-asyncio did not meet that condition.

### Test the stdio process separately

Launch the real CLI with the test interpreter and a detected content checkout.
Send newline-delimited JSON-RPC through pipes and check request IDs on replies.
Require clean stdout, startup logs in the log file, and a zero exit status after
stdin closes. Time out replies and kill a failed subprocess during cleanup.
This test skips when no real content checkout exists.

The installed SDK reports `-32602` for an unknown method because it rejects the
method while decoding its request union. The test accepts that code or `-32601`
and requires a JSON-RPC error followed by a successful ping. Unknown tool names
use the SDK's tool-error response. This change does not replace SDK dispatch.

### Return resource metadata through the SDK

Keep the existing resource handlers' string return values. At the server
boundary, convert `AnyUrl` to `str` and wrap the returned JSON in
`ReadResourceContents` with `application/json`. Use `model_dump(mode="json")`
before encoding model values. Plain model dumps retain Python datetimes, which
`json.dumps` cannot serialize.

Split the resource descriptors into six concrete collections and six templates.
Register a template-list handler. Keeping braces in concrete resource URIs
caused the SDK to encode them as `%7B` and `%7D`.

### Preserve error meaning

Resource routing raises distinct `ValueError` subclasses for invalid URIs and
missing resources. The server maps them to `-32602` and `-32002`. Other resource
read failures use `-32603`. Existing Python callers that catch `ValueError`
continue to work.

Tool lookup failures and execution exceptions raise `ValueError` through the
dispatcher. The SDK converts them to `CallToolResult` with `isError: true`.
Validators can still return `valid: false` in a successful tool result.
Discovery calls that return partial results with parse warnings also remain
successful. These cases have separate tests.

## Compatibility

Concrete resource reads and successful tool payloads keep their existing shapes.
Parameterized resource discovery moves to the MCP template endpoint. Direct
Python calls to the tool dispatcher now raise on failure, as its docstring
already specified. Three existing tests change to assert that behavior.

The suite uses MCP SDK 1.x. It does not claim full MCP conformance or SDK 2.x
compatibility. It does not test rule generation or file edits.

## References

- [MCP resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
- [MCP tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)

## Verification

The first 57 session cases produced 21 failures before the fixes and 36 passes.
The completed suite has 64 session cases and one stdio subprocess case. The
full test run against content commit `f09d24369249b7eae7e241bf82541bdf718e7661`
passed all 489 tests. The 47 warnings come from Jinja2 escape sequences in the
content checkout's macros.

Overall coverage rose from 72% to 80%. Resource-handler coverage is 93%, and
server coverage is 92%. Black, Ruff, mypy, and whitespace checks pass.

The local sandbox stalled the stdio subprocess's input pipe before the
initialization reply. The subprocess case and the full suite passed outside
that sandbox. Session cases passed inside it. The subprocess test uses a
deadline while it collects each line, so a partial reply cannot leave it
waiting without a timeout.
