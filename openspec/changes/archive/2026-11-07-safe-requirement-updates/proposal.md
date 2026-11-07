## Why

`update_requirement_rules` broke the files it edited and still reported success. Exercising it on copies of real content at `f09d243` showed four problems:

- It assumed a requirement's keys start two columns after the dash. The `srg_gpos` requirement files use `-   id:`, with keys four columns in, so the new `status` and `rules` landed at the wrong indentation. The file no longer parsed, and the server dropped the requirement (203 to 202).
- It edited every `rules` and `status` line between the requirement and the next one at its level, including those of nested requirements. Updating `pcidss_4` requirement `1.2` rewrote the rules and statuses of its nested requirements at the wrong indentation, and the file no longer loaded.
- It offered `partially_automated` and `not_applicable`, which ComplianceAsCode rejects. The `canonical-control-status` change had already removed them from the model, so the server could no longer read a file after writing one of them, and neither could the content build.
- A comment inside a rules list stopped it from removing the old rules, so the ones after the comment stayed.

## What Changes

- Take the requirement's key indentation from its `id` line.
- Edit only the requirement's own `rules` and `status` keys. Insert a missing key before the requirement's nested `controls` list, if it has one.
- Accept the 10 ComplianceAsCode statuses, from the same definition the model uses. Reject the old names with the status to use instead.
- Parse the file before and after the edit, and write it only when the requirement's rules and status are all that changed.
- Refuse requirements whose rules use Jinja2 conditionals.
- Keep blank lines between requirements, and add `warnings` to `ControlUpdateResult`.

## Non-goals

- Files that hold several requirements, like the NIST 800-53 family files. The tool still looks for a file named after the requirement.
- Adding or removing single rules. The tool still replaces the list.

## Capabilities

### Modified Capabilities

- `requirement-rules-update`: only the requirement's own keys change, edits are checked before writing, and statuses match ComplianceAsCode.

## Impact

- **Affected code**: `core/scaffolding/control_updater.py`, `models/control.py`, `core/discovery/controls.py` (the Jinja2-aware loader becomes the module function `load_control_yaml`), `server/handlers/tools.py`.
- **Results**: on copies of `f09d243`, updates to an `srg_gpos` requirement file and to `pcidss_4` requirement `1.2` load in ComplianceAsCode's `ControlsManager`, with the nested requirements unchanged. The three new integration tests fail on the previous code. The two `srg_gpos` requirements whose rules use Jinja2 conditionals are refused.
