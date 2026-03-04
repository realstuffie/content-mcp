## ADDED Requirements

### Requirement: TemplateSchema includes documentation field
The `TemplateSchema` Pydantic model SHALL include an optional `documentation` field of type `str | None` that contains the template's reference documentation extracted from the content repo.

#### Scenario: Template has documentation in reference file
- **WHEN** `get_template_schema` is called with a template name that has an entry in `docs/templates/template_reference.md`
- **THEN** the returned `TemplateSchema` SHALL have its `documentation` field populated with the full markdown content of that template's section (from the `#### <template_name>` heading to the next `####` heading, exclusive)

#### Scenario: Template has no documentation in reference file
- **WHEN** `get_template_schema` is called with a template name that has no entry in `docs/templates/template_reference.md`
- **THEN** the returned `TemplateSchema` SHALL have its `documentation` field set to `None`

#### Scenario: Reference file does not exist
- **WHEN** `get_template_schema` is called and the file `docs/templates/template_reference.md` does not exist in the content repo
- **THEN** the returned `TemplateSchema` SHALL have its `documentation` field set to `None`

### Requirement: Documentation extraction parses by heading
The system SHALL extract per-template documentation by locating the `#### <template_name>` heading in `docs/templates/template_reference.md` and collecting all content until the next `####` heading or end of file.

#### Scenario: Extract section for a known template
- **WHEN** the reference file contains a section headed `#### sshd_lineinfile`
- **THEN** the extracted documentation SHALL include the description, parameter list, and language list from that section

#### Scenario: Template name is case-sensitive
- **WHEN** the reference file contains `#### sshd_lineinfile` and the query is for `SSHD_LINEINFILE`
- **THEN** the documentation field SHALL be `None` (no case-insensitive matching)

### Requirement: Documentation field validation
The `documentation` field on `TemplateSchema` SHALL be validated as a Pydantic `str | None` field with a default of `None`. It SHALL NOT break serialization via `model_dump(mode="json")`.

#### Scenario: Serialization includes documentation
- **WHEN** a `TemplateSchema` with a populated `documentation` field is serialized via `model_dump(mode="json")`
- **THEN** the output dictionary SHALL contain a `"documentation"` key with the string value

#### Scenario: Serialization with None documentation
- **WHEN** a `TemplateSchema` with `documentation=None` is serialized via `model_dump(mode="json")`
- **THEN** the output dictionary SHALL contain `"documentation": null` (or omit it per Pydantic defaults)
