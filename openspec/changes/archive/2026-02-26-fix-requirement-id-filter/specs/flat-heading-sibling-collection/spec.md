## ADDED Requirements

### Requirement: Sibling sections collected for flat-heading documents
When `_find_section_by_requirement_id()` matches a section by title and the document uses flat headings (sibling sections at the same level), the function SHALL collect all following sibling sections until it encounters a sibling whose title matches a requirement ID pattern. The collected siblings' titles and content SHALL be concatenated into the matched section's `content` field, formatted as `## {title}\n\n{content}` blocks.

#### Scenario: CIS benchmark with flat level-1 headings
- **WHEN** `parse_policy_document` is called with `requirement_id="5.3.2.5"` on a CIS RHEL 9 benchmark markdown where the requirement heading and its body parts (Profile Applicability, Description, Rationale, Audit, Remediation) are all level-1 headings
- **THEN** the returned section's `content` SHALL include the text from Description, Rationale, Audit, and Remediation sections
- **AND** the returned section's `title` SHALL contain "5.3.2.5"

#### Scenario: Collection stops at next requirement ID
- **WHEN** `parse_policy_document` is called with `requirement_id="5.3.2.5"` on a CIS benchmark where section "5.3.3.1" follows the body parts of "5.3.2.5"
- **THEN** the returned section's `content` SHALL NOT include any text from the "5.3.3.1" section or beyond

### Requirement: Requirement ID pattern detection
The function SHALL use a regex pattern to identify headings that represent new requirement IDs. The pattern SHALL match dotted numeric identifiers with at least 3 components (e.g., `1.2.3`, `5.3.2.5`) and ANSSI R-code identifiers (e.g., `R1`, `R34`).

#### Scenario: Dotted numeric ID detected as requirement
- **WHEN** a sibling section has title containing "1.1.1.1 Ensure cramfs..."
- **THEN** it SHALL be recognized as a new requirement and stop sibling collection

#### Scenario: R-code ID detected as requirement
- **WHEN** a sibling section has title containing "R34 - Disable service accounts"
- **THEN** it SHALL be recognized as a new requirement and stop sibling collection

#### Scenario: Body heading not detected as requirement
- **WHEN** a sibling section has title "**Description:**" or "**Rationale:**" or "**Audit:**"
- **THEN** it SHALL NOT be recognized as a requirement ID and SHALL be included in sibling collection

### Requirement: New DocumentSection created without mutation
When sibling content is collected, the function SHALL create a new `DocumentSection` instance with the combined content rather than mutating the original section object.

#### Scenario: Original section unchanged
- **WHEN** sibling collection produces combined content
- **THEN** a new `DocumentSection` SHALL be returned with the original section's `id`, `title`, `level`, `subsections`, and `parent_id` preserved
- **AND** the original section object in the parsed sections list SHALL remain unmodified
