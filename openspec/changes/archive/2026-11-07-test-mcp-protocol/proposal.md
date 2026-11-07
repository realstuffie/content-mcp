## Why

The SDK passes AnyUrl objects to resource handlers. The server passed
them straight to urlparse, which tried to call decode on them and failed.
Direct handler tests used strings and missed the failure.

## What changes

Convert the URI to a string at the server boundary. A regression test
now reads the product collection and a product through an MCP session.

## Capabilities

- `mcp-protocol`: the implemented resource and tool protocol behavior.

## Scope

Rule generation and file-editing behavior are outside this change.
