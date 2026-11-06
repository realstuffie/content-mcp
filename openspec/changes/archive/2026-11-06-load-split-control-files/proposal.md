## Why

Control files that keep their requirements in a `controls_dir` subdirectory lost most or all of them. Each file in the subdirectory holds its requirements in a top-level `controls` list, but the loader read the whole file as a single requirement, so every NIST 800-53 family file failed validation. Requirement files also use Jinja2 such as `{{{ full_name }}}` in titles, which plain YAML can't parse. In current content 229 requirement files failed: all of `nist_800_53` and `iec_62443`, and all but one requirement of `srg_gpos`.

## What Changes

- Read every requirement in a requirement file's `controls` list. A file with a single requirement at the top level still works.
- Expand requirement files with Jinja2 like the build: with the product's variables when a product is given, and otherwise with an empty product name, no product families, and "The operating system" as `full_name`, the wording SRGs use where ComplianceAsCode substitutes the product name.
- Move product variable loading into `core/integration/product_variables.py`, shared by rules and controls.

## Non-goals

- `get_requirement_file_path` and `update_requirement_rules` still assume one requirement per file named after its ID, which doesn't hold for the NIST 800-53 family files.

## Capabilities

### Modified Capabilities

- `control-rule-index`: requirement files with a `controls` list or Jinja2 load.

## Impact

- **Affected code**: `core/discovery/controls.py`, `core/discovery/rules.py`, `core/integration/product_variables.py` (new).
- **Results**: requirement file parse errors drop from 229 to 0. `srg_gpos` goes from 1 to 203 requirements, `nist_800_53` from 0 to 1196, and `iec_62443` from 0 to 61. Profiles that select these controls, such as the opensuse16 STIG and the RHEL CUI profiles, now count 3056 more rule selections.
