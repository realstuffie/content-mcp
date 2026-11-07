## ADDED Requirements

### Requirement: Selectable profile listings

`list_profiles`, `cac://profiles`, and product profile ID lists SHALL omit hidden
profiles by default. The Python and MCP list tools SHALL accept `include_hidden`
with a default of false. Profile summaries and details SHALL expose `hidden`.

#### Scenario: Build-only default profile

- **WHEN** a product has five selectable profiles and one hidden default profile
- **THEN** its normal list and product profile IDs contain five entries
- **AND** `list_profiles` with `include_hidden=true` returns all six

#### Scenario: Visibility depends on the field

- **WHEN** a profile has a non-default name and its hidden field is true
- **THEN** normal listings omit it
- **AND** a profile named default with no hidden flag remains selectable

### Requirement: Build visibility semantics

The server SHALL interpret `hidden` the way ComplianceAsCode's YAML loader and
profile serializer do. Nonempty boolean scalar text SHALL be hidden, including
the text false. Absent, null, empty, and numeric zero values SHALL be visible.

#### Scenario: Compare with the build

- **WHEN** profiles use true, false, quoted false, yes, null, an empty string,
  zero, or one as their hidden values
- **THEN** the server's hidden result agrees with SSG's loaded profile

### Requirement: Explicit access and inheritance

Detail lookups SHALL accept hidden profiles. Selectable profiles SHALL retain
rules inherited from hidden parents.

#### Scenario: Hidden parent

- **WHEN** a selectable child extends a hidden parent
- **THEN** its resolved rules include the parent's rules
- **AND** rule availability names the child and omits the hidden parent

### Requirement: Hidden benchmark rules remain searchable

Product-filtered searches SHALL include rules contributed by hidden profiles.
The shared cache SHALL preserve those rule sets separately from selectable
profile memberships and rebuild them when a profile's hidden value changes.

#### Scenario: Reuse the shared index

- **WHEN** a second discovery instance reuses an index with hidden-only rules
- **THEN** those rules remain searchable for their product
- **AND** hidden profile names remain absent from rule availability

#### Scenario: Change visibility

- **WHEN** a hidden profile becomes selectable
- **THEN** a subsequent discovery call rebuilds the index
- **AND** the profile can appear in selectable lists and rule memberships
