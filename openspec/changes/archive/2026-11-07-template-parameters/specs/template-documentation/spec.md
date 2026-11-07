## MODIFIED Requirements

### Requirement: Documentation extraction parses by heading
The system SHALL extract per-template documentation by locating the `#### <template_name>` heading in `docs/templates/template_reference.md` and collecting all content until the next heading of level 1 to 4 or end of file. Lines inside fenced code blocks SHALL NOT count as headings.
