## MODIFIED Requirements

### Requirement: Resolve directory-based requirement path

The tool SHALL return the file that defines the requirement when the policy has a requirement directory: the one its `controls_dir` names, or the directory named after the control file. A file named after the requirement SHALL be tried first, then the control file, then every other `.yml` file in the directory, since one file can hold several requirements. The resolved path SHALL be relative to the control file's parent directory (which may be in `controls/` or `products/<product>/controls/`).

#### Scenario: Requirement in a family file

- **WHEN** `get_requirement_file_path(control_id="nist_800_53", requirement_id="ac-2", product="rhel9")` is called and `ac-2` is defined in `products/rhel9/controls/nist_800_53/ac.yml`
- **THEN** the tool returns `RequirementFilePath` with `format="directory"`, `file_path` pointing to `ac.yml`, and `exists=True`

#### Scenario: Requirement in the control file of a directory-based policy

- **WHEN** `srg_gpos` defines `Variables` in `controls/srg_gpos.yml` and its other requirements in `controls/srg_gpos/`
- **THEN** the tool returns `format="inline"` and the path of `controls/srg_gpos.yml`

#### Scenario: Directory named after the control file

- **WHEN** `controls/cis_ocp_200.yml` sets no `controls_dir` and `1.2.11` is defined in `controls/cis_ocp_200/section-1.yml`
- **THEN** the tool returns the path of `section-1.yml`
