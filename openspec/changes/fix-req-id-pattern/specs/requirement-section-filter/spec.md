## MODIFIED Requirements

### Requirement: Filtered response when requirement_id is provided
When `requirement_id` is provided, the tool SHALL return the same `ParsedDocument` JSON structure with `sections` filtered to contain only the section whose title or content matches the requirement ID. When the matched section has empty content due to flat-heading document structure, the tool SHALL collect following sibling sections that belong to the same requirement and include their content in the returned section. The boundary-detection pattern used to identify the next requirement heading SHALL match requirement IDs preceded by markdown formatting characters (such as `*`, `>`, `)`, `]`, `#`) in addition to whitespace or start-of-string.

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

#### Scenario: CIS flat-heading with HTML spans and bold markers stops at next requirement
- **WHEN** `parse_policy_document` is called with `requirement_id="5.3.2.5"` on a CIS document where headings contain `<span>` tags and `**` bold markers before dotted numbers (e.g., `<span id="page-601-0"></span>**5.3.3 Configure PAM Arguments**`)
- **THEN** the response `sections` array SHALL contain exactly one entry for requirement 5.3.2.5
- **AND** the entry's `content` SHALL NOT include content from the next requirement (5.3.3)

#### Scenario: Boundary pattern matches requirement ID after bold markers
- **WHEN** the boundary-detection pattern is applied to a heading title `<span id="page-601-0"></span>**5.3.3 Configure PAM Arguments**`
- **THEN** the pattern SHALL match the requirement ID `5.3.3`

#### Scenario: Boundary pattern matches requirement ID after italic marker
- **WHEN** the boundary-detection pattern is applied to a heading title `*5.3.2.5 Ensure pam_unix*`
- **THEN** the pattern SHALL match the requirement ID `5.3.2.5`
