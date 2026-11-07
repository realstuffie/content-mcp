## MODIFIED Requirements

### Requirement: Product filter in rule search
When `search_rules` is called with a `product`, a rule SHALL match the product filter when any profile of that product selects it, as resolved by the reverse index, or when it has identifiers for that product.

Hidden profiles SHALL contribute their rules to product-filtered searches but
SHALL NOT appear in `products_in_profiles`. The shared cache SHALL preserve
both selectable-profile memberships and rules contributed by hidden profiles.

#### Scenario: Hidden profile contributes an otherwise unselected rule

- **WHEN** a hidden default profile selects a rule that no selectable profile selects
- **THEN** a rule search for that product includes it
- **AND** `products_in_profiles` does not claim that the hidden profile selects it for a scan

#### Scenario: Selectable profile extends a hidden profile

- **WHEN** a selectable profile inherits rules from a hidden profile
- **THEN** the inherited rules list the selectable child in `products_in_profiles`
- **AND** the hidden parent is omitted

#### Scenario: Rule selected only through a profile
- **WHEN** `search_rules` is called with `product="ubuntu2204"` and a rule has no `ubuntu2204` identifiers but a `ubuntu2204` profile selects it
- **THEN** the rule is included in the results
