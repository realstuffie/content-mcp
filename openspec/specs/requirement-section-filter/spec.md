### Requirement: Tool schema includes optional requirement_id parameter
The `parse_policy_document` MCP tool schema SHALL include an optional `requirement_id` parameter of type `string`. The parameter MUST NOT be listed in the `required` array.

#### Scenario: Tool schema exposes requirement_id
- **WHEN** the MCP server lists tool definitions
- **THEN** the `parse_policy_document` tool's `inputSchema.properties` SHALL contain a `requirement_id` field with `type: "string"` and a description indicating it filters sections by requirement ID

### Requirement: Filtered response when requirement_id is provided
When `requirement_id` is provided, the tool SHALL return the same `ParsedDocument` JSON structure with `sections` filtered to contain only the section whose title or content matches the requirement ID. When the matched section has empty content due to flat-heading document structure, the tool SHALL collect following sibling sections that belong to the same requirement and include their content in the returned section.

#### Scenario: Match found in section title (ANSSI R-code)
- **WHEN** `parse_policy_document` is called with `requirement_id="R34"` on an ANSSI document containing a section titled "R34 M I Disabling the service accounts"
- **THEN** the response `sections` array SHALL contain exactly one entry with that section (including its subsections)

#### Scenario: Match found in section title (CIS dotted number)
- **WHEN** `parse_policy_document` is called with `requirement_id="1.1.1.1"` on a CIS document containing a section titled "1.1.1.1 Ensure cramfs kernel module..."
- **THEN** the response `sections` array SHALL contain exactly one entry for that section with its subsections

#### Scenario: Match found in section content (STIG ID)
- **WHEN** `parse_policy_document` is called with `requirement_id="RHEL-09-171011"` on a STIG document where the ID appears in section body text but not the title
- **THEN** the response `sections` array SHALL contain exactly one entry for the section containing that ID in its content

#### Scenario: CIS flat-heading document returns body content
- **WHEN** `parse_policy_document` is called with `requirement_id="5.3.2.5"` on a CIS RHEL 9 benchmark with flat level-1 headings
- **THEN** the response `sections` array SHALL contain exactly one entry
- **AND** that entry's `content` SHALL include Description, Rationale, Audit, and Remediation text from the following sibling sections

### Requirement: Word-boundary matching prevents partial matches
The requirement ID matching SHALL use word-boundary-aware matching that prevents partial ID matches. Dots and word characters adjacent to the ID SHALL prevent a match.

#### Scenario: R3 does not match R34
- **WHEN** `parse_policy_document` is called with `requirement_id="R3"` on a document containing "R34" but no standalone "R3"
- **THEN** the response `sections` array SHALL be empty

#### Scenario: 1.1.1 does not match 1.1.1.1
- **WHEN** `parse_policy_document` is called with `requirement_id="1.1.1"` on a document containing "1.1.1.1" but no standalone "1.1.1"
- **THEN** the response `sections` array SHALL be empty

#### Scenario: Case-insensitive matching
- **WHEN** `parse_policy_document` is called with `requirement_id="rhel-09-171011"` on a document containing "RHEL-09-171011"
- **THEN** the response SHALL match the section (matching is case-insensitive)

### Requirement: No match returns empty sections with metadata
When `requirement_id` is provided but no matching section is found, the tool SHALL return the `ParsedDocument` with an empty `sections` array and a `requirement_not_found` key in `metadata`.

#### Scenario: Non-existent requirement ID
- **WHEN** `parse_policy_document` is called with `requirement_id="NONEXISTENT-999"` on any document
- **THEN** the response `sections` SHALL be an empty array
- **AND** the response `metadata` SHALL contain `"requirement_not_found": "NONEXISTENT-999"`

### Requirement: Unchanged behavior when requirement_id is omitted
When `requirement_id` is not provided, the tool SHALL return the full parsed document with all sections, identical to current behavior.

#### Scenario: No requirement_id parameter
- **WHEN** `parse_policy_document` is called without `requirement_id`
- **THEN** the response SHALL contain all parsed sections from the document (unchanged behavior)
