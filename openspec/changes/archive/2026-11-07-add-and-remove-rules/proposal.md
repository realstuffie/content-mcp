## Why

`update_requirement_rules` could only replace a requirement's rules. To add one rule, an agent had to send the whole list back, and a list it hadn't read in full lost rules without a word: the result didn't say what was removed. Replacing also rewrote the list, dropping comments such as the section headings in the `srg_gpos` files, and always set the status, `automated` unless told otherwise.

## What Changes

- Add `mode`: `replace` (the default, as before), `add` or `remove`. Add appends the rules not already there, after the current ones; remove deletes the given ones. Both edit only the affected list items, so comments in the list stay.
- In add and remove modes, the status is left as it is unless given. Replace still defaults to `automated`, so existing callers behave the same.
- Report the rules after the update, and the rules added and removed, in every mode.
- When nothing would change, write nothing and report the requirement as unchanged.

## Decisions

- **Replace stays the default.** Changing it would silently change what existing callers do.
- **Text edits, not rewrites, for add and remove.** The list's other lines, comments included, are kept. An inline list such as `rules: [a]` is rewritten as a block list, since there is no item line to insert after.
- **The same check before writing.** The edited file is parsed and compared with the original as before, now expecting the rules the mode produces and the status only when one is given.

## Capabilities

### Modified Capabilities

- `requirement-rules-update`: add and remove modes, the status default per mode, and the rule changes in the result.

## Impact

- **Affected code**: `core/scaffolding/control_updater.py`, `models/control.py`, `server/handlers/tools.py`.
- **Results** at `f09d243`: adding a rule to `srg_gpos` `SRG-OS-000480-GPOS-00227`, whose list has a `# file permissions` heading, keeps the heading and appends the rule; the file loads in ComplianceAsCode's `ControlsManager` with the old rules followed by the new one.
