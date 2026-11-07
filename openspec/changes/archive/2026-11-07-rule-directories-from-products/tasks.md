## 1. Rule directories

- [x] 1.1 Read `benchmark_root` from every product.yml, drop nested roots and roots outside the repository, and fall back to `linux_os` and `applications`
- [x] 1.2 Use the roots in `RuleDiscovery` and template discovery

## 2. Verification

- [x] 2.1 Unit tests for roots, nesting, outside roots, the fallback, and indexing a product rule
- [x] 2.2 Integration test that Firefox rules are found, against content at `f09d243`
- [x] 2.3 Load, detail and validate all 36 Firefox rules
