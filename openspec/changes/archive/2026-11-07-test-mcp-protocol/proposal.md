## Why

The SDK passes AnyUrl objects to resource handlers. The server passed
them straight to urlparse, which tried to call decode on them and failed.
Direct handler tests used strings and missed the failure.

Rule details and datastream metadata contain Python datetimes. Resource
handlers used model_dump without JSON mode, so json.dumps failed on
last_modified and build_time even though direct discovery calls worked.

## What changes

Convert the URI to a string at the server boundary. A regression test
now reads the product collection and a product through an MCP session.

Dump resource models in JSON mode before encoding them. Session tests
read all 12 resource routes, parse the timestamps and preserve Unicode
text. Shared fixtures provide a temporary product, rule and build.

## Capabilities

- `mcp-protocol`: the implemented resource and tool protocol behavior.

## Scope

Rule generation and file-editing behavior are outside this change.
