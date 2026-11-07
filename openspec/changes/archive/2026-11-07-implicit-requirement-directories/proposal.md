## Why

ComplianceAsCode reads a policy's requirements from the directory its control file names in `controls_dir`, and, when the file names none, from the directory named after the control file. The server only followed `controls_dir`. Five policies keep their requirements in such a directory without setting it, and the server saw none of their requirements at `f09d243`: `cis_ocp` (137 in the build), `cis_ocp_190` (134), `cis_ocp_200` (134), `srg_ctr` (173) and `base_sle16` (22).

Profiles that select them lost those rules too. The OpenShift CIS profiles resolved to 2 rules instead of 199.

## What Changes

- Find a policy's requirement directory the way ComplianceAsCode does, in `requirements_directory`, and read its `.yml` files, skipping dotfiles, in `requirement_files`.
- Keep the control file's own requirements ahead of the directory's.

## Capabilities

### Modified Capabilities

- `control-rule-index`: requirements are read from a directory named after the control file when it sets no `controls_dir`.

## Impact

- **Affected code**: `core/discovery/controls.py`.
- **Results** at `f09d243`: of the 70 policies ComplianceAsCode loads, the server's requirement counts now match the build's for all 70, against 65 before. Rule selections across all profiles go from 71232 to 73568. The `ocp4` CIS 2.0 profile resolves to the same 199 rules as `cis_ocp_200:all` plus its two extra selections.
