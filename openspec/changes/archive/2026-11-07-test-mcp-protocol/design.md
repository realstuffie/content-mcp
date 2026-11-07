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

### Resource template discovery

resources/list included URIs such as cac://products/{product_id} as
concrete resources. The SDK escaped their braces, and clients could
not discover their parameters through resources/templates/list.

Keep the six collection URIs in resources/list and register the six
parameterized descriptors as resource templates. A session test checks
both discovery responses and their MIME types.

### Rendered-rule resource paths

The rendered-rule resource route accepted four or more path segments
and ignored everything after the rule ID. A URI ending in /extra
returned the same rule as the valid URI.

Require exactly four segments for a rendered-rule resource. A session
test checks that the extra segment is rejected and the client can
still send another request.

### Resource error codes

Resource routing raised ValueError for both invalid URIs and missing
content. The SDK returned the same generic error for those cases and
for YAML parse failures, so clients could not distinguish them.

Use distinct ValueError subclasses for invalid routes and missing
resources. Map them to JSON-RPC codes -32602 and -32002, and map other
read failures to -32603. Missing-resource errors include the URI.
Session tests check each code and verify recovery after a failed read.

## Verification

Each implemented fix has a regression test through an MCP session.
