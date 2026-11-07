## 1. Product rule sets

- [x] 1.1 Find a product's rule directories from `benchmark_root` and `additional_content_directories`
- [x] 1.2 Collect the rules there, without `documentation_complete: false`, reading each shared directory once
- [x] 1.3 Keep only those rules in `ProfileRuleResolver`, before `filter_rules`

## 2. Verification

- [x] 2.1 Unit tests for product rule sets, additional directories, unknown products, the directory cache, and the resolver
- [x] 2.2 Integration test that `ocp4` no longer counts `audit_access_failed`
- [x] 2.3 Check that no profile selects a rule outside its product directly, and measure selections and index build time
