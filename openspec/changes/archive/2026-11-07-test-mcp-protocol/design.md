## Decisions

### SDK resource URI conversion

The SDK passes AnyUrl objects to resource handlers. The server passed
them straight to urlparse, which tried to call decode on them and failed.
Direct handler tests used strings and missed the failure.

Convert the URI to a string at the server boundary. A regression test
now reads the product collection and a product through an MCP session.

### Resource timestamp serialization

Rule details and datastream metadata contain Python datetimes. Resource
handlers used model_dump without JSON mode, so json.dumps failed on
last_modified and build_time even though direct discovery calls worked.

Dump resource models in JSON mode before encoding them. Session tests
read all 12 resource routes, parse the timestamps and preserve Unicode
text. Shared fixtures provide a temporary product, rule and build.

### Resource content MIME type

Resource descriptors advertised application/json, but reads returned
plain strings. The SDK wrapped those strings as text/plain, so the
content metadata disagreed with the resource listing.

Wrap resource text in ReadResourceContents with application/json. The
session tests now check the URI, MIME type and JSON content of all
12 resource routes.

## Verification

Each implemented fix has a regression test through an MCP session.
