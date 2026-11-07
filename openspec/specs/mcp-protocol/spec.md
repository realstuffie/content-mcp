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
