## MODIFIED Requirements

### Requirement: Discover controls from multiple directories

The `ControlDiscovery` class SHALL scan both the global `controls/` directory and product-specific `products/<product>/controls/` directories when listing or resolving control files. An internal `_get_controls_dirs(product: str | None)` method SHALL return an ordered list of directories:
1. `<repo>/controls/` (always included first)
2. If `product` is specified: validate that the product exists, then append `<repo>/products/<product>/controls/` (if it exists)
3. If `product` is `None`: enumerate all known products and append existing `<repo>/products/<product>/controls/` directories (sorted alphabetically)

A known product SHALL be a directory under `<repo>/products/` that has a `product.yml`. The check SHALL list directories without reading each `product.yml`, and SHALL read the directories on every call. When `product` is specified but not known, the method SHALL raise a `ValueError` with a descriptive message.

#### Scenario: Product specified with product controls directory

- **WHEN** `_get_controls_dirs(product="rhel9")` is called and `rhel9` is a known product and `products/rhel9/controls/` exists
- **THEN** the result SHALL be `[<repo>/controls/, <repo>/products/rhel9/controls/]`

#### Scenario: Product specified without product controls directory

- **WHEN** `_get_controls_dirs(product="fedora")` is called and `fedora` is a known product but `products/fedora/controls/` does not exist
- **THEN** the result SHALL be `[<repo>/controls/]`

#### Scenario: Invalid product raises error

- **WHEN** `_get_controls_dirs(product="nonexistent")` is called and `nonexistent` is not a known product
- **THEN** a `ValueError` SHALL be raised with a message indicating the product is not recognized

#### Scenario: No product specified discovers all product controls

- **WHEN** `_get_controls_dirs(product=None)` is called and known products `rhel8` and `rhel9` both have `controls/` directories
- **THEN** the result SHALL be `[<repo>/controls/, <repo>/products/rhel8/controls/, <repo>/products/rhel9/controls/]`
