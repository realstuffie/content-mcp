## ADDED Requirements

### Requirement: Find rules where the build does
Rule discovery and template discovery SHALL read rules from the directories the content build uses: the `benchmark_root` of each `products/*/product.yml`, relative to the product directory. A root inside another root SHALL be read once, and a root outside the content repository SHALL be ignored. When no product names a benchmark root, `linux_os` and `applications` SHALL be used.

#### Scenario: Product with its own rule directory
- **WHEN** `products/firefox/product.yml` has `benchmark_root: "./guide"`
- **THEN** rules under `products/firefox/guide` are found by `search_rules`, `get_rule_details` and `get_rule_product_availability`

#### Scenario: Shared rule directory
- **WHEN** 37 products have `benchmark_root: "../../linux_os/guide"`
- **THEN** `linux_os/guide` is read once
