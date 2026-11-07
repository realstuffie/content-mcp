## 1. Updater

- [x] 1.1 Take the key indentation from the `id` line
- [x] 1.2 Edit only the requirement's own `rules` and `status`, and insert missing keys before nested `controls`
- [x] 1.3 Replace every old rule, including those after a comment, and keep blank lines between requirements
- [x] 1.4 Refuse rules with Jinja2 conditionals, duplicate keys, and requirements split by Jinja2
- [x] 1.5 Parse before and after the edit, and write only when the rules and status are all that changed
- [x] 1.6 Accept the canonical statuses, and reject old names with the replacement

## 2. Model, schema and loader

- [x] 2.1 Add `ControlStatus` and `CONTROL_STATUSES`, and use them in the model and the tool schema
- [x] 2.2 Add `warnings` to `ControlUpdateResult` and show them in the tool output
- [x] 2.3 Move the Jinja2-aware loader into `load_control_yaml`

## 3. Verification

- [x] 3.1 Unit tests for each case above
- [x] 3.2 Integration tests on copies of `srg_gpos` and `pcidss_4`, loaded with ComplianceAsCode's `ControlsManager`, which fail on the previous code
- [x] 3.3 Rerun the write sweep against content at `f09d243`
