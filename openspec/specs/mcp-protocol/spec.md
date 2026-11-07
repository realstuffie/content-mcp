## ADDED Requirements

### Requirement: SDK resource URI conversion

The server SHALL convert the SDK's resource URI objects to strings
before calling its resource handlers.

#### Scenario: SDK resource URI conversion

- **WHEN** a client reads cac://products and cac://products/rhel9 through MCP
- **THEN** both reads return the product data without a URI conversion error

### Requirement: Resource timestamp serialization

Resource handlers SHALL serialize model values in JSON mode. Known
modification and build timestamps SHALL be ISO 8601 strings.

#### Scenario: Resource timestamp serialization

- **WHEN** a client reads rule details and datastream metadata with known timestamps
- **THEN** both responses contain JSON whose timestamps parse as ISO 8601 values

### Requirement: Resource content MIME type

The server SHALL return JSON resource contents with application/json
and preserve the requested resource URI in the response.

#### Scenario: Resource content MIME type

- **WHEN** a client reads any supported resource route
- **THEN** the response preserves its URI and declares application/json

### Requirement: Resource template discovery

The server SHALL list the six concrete collection URIs through
resources/list and the six parameterized URIs through resources/templates/list.

#### Scenario: Resource template discovery

- **WHEN** a client lists resources and resource templates
- **THEN** concrete URIs contain no placeholders and parameterized descriptors use uriTemplate

### Requirement: Rendered-rule resource paths

A rendered-rule resource URI SHALL contain exactly four route segments.
The server SHALL reject segments after the rule ID.

#### Scenario: Rendered-rule resource paths

- **WHEN** a client adds /extra after a rendered-rule ID
- **THEN** the read fails and the same session still accepts a valid request

### Requirement: Resource error codes

The server SHALL return -32602 for invalid resource routes, -32002 for
missing resources and -32603 for other read failures. Missing-resource
errors SHALL include the URI in their data.

#### Scenario: Resource error codes

- **WHEN** a client requests an invalid URI, missing object or unparseable resource
- **THEN** the error code identifies the failure and a later request in the session succeeds
