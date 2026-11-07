## 1. Validator

- [x] 1.1 Remove `documentation_complete` from the required fields
- [x] 1.2 Warn about `false` and about other boolean spellings, reading the value's text as the build does
- [x] 1.3 Drop the field from the post-expansion restore

## 2. Verification

- [x] 2.1 Unit tests for a missing field, `true`, `false`, quoted `false`, and other spellings
- [x] 2.2 Compare the validator with ComplianceAsCode's loader for each spelling
- [x] 2.3 Integration test that every rule the build reads is valid
