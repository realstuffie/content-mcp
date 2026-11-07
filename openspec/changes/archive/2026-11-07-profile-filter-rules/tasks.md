## 1. Filtering

- [x] 1.1 Parse `filter_rules`, single line or continued, and add it to `ProfileDetails`
- [x] 1.2 Apply a rule filter in `ProfileRuleResolver` after `extends` and unselections
- [x] 1.3 Build the filter in `RuleDiscovery` from `ssg.utils.safe_eval_filter` and product-expanded rule attributes

## 2. Verification

- [x] 2.1 Unit tests for parsing, filtering, inherited rules, a parent's filter, and no filter function
- [x] 2.2 Integration tests for the OpenShift platform and node split, and against the build's own rule objects and filter
- [x] 2.3 Compare all 23 filtered profiles with the build's objects, and measure selections and index build time
