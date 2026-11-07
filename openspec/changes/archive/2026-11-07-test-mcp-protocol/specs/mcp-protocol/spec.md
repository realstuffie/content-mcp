## ADDED Requirements

### Requirement: SDK resource URI conversion

The server SHALL convert the SDK's resource URI objects to strings
before calling its resource handlers.

#### Scenario: SDK resource URI conversion

- **WHEN** a client reads cac://products and cac://products/rhel9 through MCP
- **THEN** both reads return the product data without a URI conversion error
