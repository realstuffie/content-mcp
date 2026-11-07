## ADDED Requirements

### Requirement: Product type and version from the product ID
`list_products` and `get_product_details` SHALL report a product's `product_type` and `version` by splitting its ID the way ComplianceAsCode's `ssg.utils.parse_name` does: the name, then the version digits at the end. A product ID without trailing digits has that ID as its type and no version. `product.yml` has no field for either.

#### Scenario: Versioned product
- **WHEN** `get_product_details("ubuntu2404")` is called
- **THEN** `product_type` is `ubuntu` and `version` is `2404`

#### Scenario: Product without a version
- **WHEN** `get_product_details("fedora")` is called
- **THEN** `product_type` is `fedora` and `version` is null

### Requirement: Product CPE
`get_product_details` SHALL report as `cpe` the name of the first entry in the product's `cpes` list.

#### Scenario: RHEL 9
- **WHEN** `get_product_details("rhel9")` is called
- **THEN** `cpe` is `cpe:/o:redhat:enterprise_linux:9`
