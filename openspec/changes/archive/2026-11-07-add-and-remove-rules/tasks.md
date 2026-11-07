## 1. Modes

- [x] 1.1 Read the current rules from the text, in block or flow style
- [x] 1.2 Add and remove by editing only the affected items; rewrite flow lists and empty results
- [x] 1.3 Leave the status alone in add and remove modes unless given; keep `automated` as the replace default
- [x] 1.4 Report the final rules and what was added and removed; write nothing when nothing changes

## 2. Tool

- [x] 2.1 Add `mode` to the tool schema and describe the status default per mode
- [x] 2.2 Show the final rules, additions and removals, or that nothing changed

## 3. Verification

- [x] 3.1 Unit tests for each mode, comments, flow lists, unchanged requests, status, and invalid modes
- [x] 3.2 Integration test adding a rule to an `srg_gpos` requirement with a commented list
