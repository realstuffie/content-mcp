## MODIFIED Requirements

### Requirement: Flatten nested control structures

#### Scenario: Directory named after the control file
- **WHEN** a control file sets no `controls_dir` and a directory with the same name exists next to it, such as `controls/cis_ocp/` next to `controls/cis_ocp.yml`
- **THEN** the requirements from the `.yml` files in that directory are loaded, as ComplianceAsCode loads them
- **AND** files whose names start with a dot are skipped

#### Scenario: Requirements in both the control file and its directory
- **WHEN** a control file has its own `controls` list and a requirement directory, like `srg_gpos`
- **THEN** the requirements from both are loaded, the control file's first
