## 1. Loading

- [x] 1.1 Add `requirements_directory` and `requirement_files`, following ComplianceAsCode's `Policy` loader
- [x] 1.2 Read requirement directories in `parse_control_file` whether or not `controls_dir` is set

## 2. Verification

- [x] 2.1 Unit tests for a directory without `controls_dir`, dotfiles, and requirements in both places
- [x] 2.2 Integration tests comparing `cis_ocp`, `srg_ctr` and `base_sle16` with ComplianceAsCode's `ControlsManager`, and the `ocp4` CIS profile's selections
- [x] 2.3 Compare the requirement counts of all 70 policies with the build
