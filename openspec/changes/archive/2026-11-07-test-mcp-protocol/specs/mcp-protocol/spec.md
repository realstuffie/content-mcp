## ADDED Requirements

### Requirement: Resource discovery

The server SHALL return concrete collection URIs through `resources/list` and
parameterized URI templates through `resources/templates/list`.

#### Scenario: Discover parameterized resources

- **WHEN** a client lists resources and resource templates
- **THEN** the six concrete collection URIs contain no template placeholders
- **AND** the six parameterized descriptors have `uriTemplate` fields and
  `application/json` MIME types

### Requirement: Resource serialization

The server SHALL accept the SDK's URI objects and return JSON resource content
with `application/json`. Model timestamps SHALL use ISO 8601 strings.

#### Scenario: Read a rule and a built datastream

- **WHEN** a client reads rule details and datastream metadata through MCP
- **THEN** both responses contain valid JSON and preserve their resource URIs
- **AND** modification and build timestamps parse as ISO 8601 values
- **AND** Unicode text survives the response unchanged

### Requirement: Resource errors

The server SHALL reject invalid resource routes with JSON-RPC code `-32602`,
missing resources with `-32002`, and other read failures with `-32603`.

#### Scenario: Missing resource

- **WHEN** a client reads a valid URI for a missing product, rule, template, or profile
- **THEN** the server returns `-32002` and includes the URI in the error data
- **AND** the client can send another request through the same session

#### Scenario: Extra path segment

- **WHEN** a rendered-rule URI has a segment after its rule ID
- **THEN** the server returns `-32602`

#### Scenario: Content fails to parse

- **WHEN** a product resource exists but its YAML fails to parse
- **THEN** the server returns `-32603`
- **AND** the session remains usable

### Requirement: Tool error reporting

Tool lookup failures and execution exceptions SHALL reach the MCP SDK's error
handling so the tool result has `isError: true`. A completed validation call
SHALL remain successful even when it reports invalid content.

#### Scenario: Invalid arguments or failed lookup

- **WHEN** a client omits a required argument, supplies the wrong type or enum,
  or requests a missing object through a detail tool
- **THEN** the tool response has `isError: true` and describes the failure
- **AND** a subsequent valid call succeeds in the same session

#### Scenario: Invalid content submitted for validation

- **WHEN** a client submits invalid rule YAML to `validate_rule_yaml`
- **THEN** the result reports `valid: false` with validation errors
- **AND** `isError` is false

#### Scenario: Partial discovery result

- **WHEN** one product fails to parse and another product loads
- **THEN** `list_products` returns the loaded product and a parse warning
- **AND** `isError` is false

### Requirement: Session tests

The test suite SHALL exercise initialization, capabilities, discovery, all 25
reading and validation tools, every resource route, and concurrent request
responses through SDK sessions. Rule generation and requirement updates SHALL
remain outside this suite's scope.

#### Scenario: Concurrent requests

- **WHEN** a client sends product, control-statistics, and rule-detail requests concurrently
- **THEN** each request receives its own expected result

### Requirement: Stdio lifecycle test

When a real content checkout is available, the test suite SHALL launch the CLI
and exchange newline-delimited JSON-RPC through stdin and stdout. The test SHALL
bound reply waits and clean up a failed subprocess.

#### Scenario: Initialize, call, and shut down

- **WHEN** the client initializes, lists tools, calls a tool, sends invalid
  arguments and an unknown method, then closes stdin
- **THEN** replies preserve request IDs and distinguish results from errors
- **AND** stdout contains only JSON-RPC messages
- **AND** the server exits with code zero after EOF

#### Scenario: No real content checkout

- **WHEN** the test suite cannot find a real content checkout
- **THEN** the stdio subprocess case skips
- **AND** the temporary-repository session cases still run
