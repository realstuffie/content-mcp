## 1. Lookup

- [x] 1.1 Add `find_requirement_file`, searching the named file, the control file, and the rest of the directory
- [x] 1.2 Use it in `get_requirement_file_path`, keeping the predicted path for new requirements
- [x] 1.3 Use it in `update_requirement_rules`, and name the products for per-product policies

## 2. Verification

- [x] 2.1 Unit tests for family files, a requirement in the control file of a directory policy, a directory without `controls_dir`, and the per-product error
- [x] 2.2 Integration tests updating NIST `ac-2` and `cis_ocp_200` `1.2.11` on copies of real content, loaded with ComplianceAsCode's `ControlsManager`
- [x] 2.3 Look up every requirement ComplianceAsCode loads, before and after
