## Context

The updater edits control files as text, so it keeps Jinja2, comments, and formatting. It found a requirement's block by indentation and rewrote any `rules:` or `status:` line inside it. That works for flat files in one style and breaks on the styles real content uses.

## Decisions

### Keep editing text

A YAML round trip would know the structure, but control files contain Jinja2 that no YAML library parses, and a round trip would reformat files and drop comments. The edit stays text-based, limited to lines at the requirement's own key indentation. Those are the only lines that can be its own keys: nested requirements and block scalar text are indented deeper.

### Check every edit before writing

The text edit can still meet layouts nobody tested. Before writing, the updater parses the file before and after the edit, with Jinja2 expanded the way control discovery expands it, and compares. The file is written only when the target requirement's `rules` and `status` are the only difference. This also catches cases the rules above miss.

If the original file doesn't parse, there is nothing to compare against. The edit is written with a warning instead of being refused, because without the `ssg` modules a file with Jinja2 never parses, and refusing would block every update in that setup.

Alternatives considered:

- Write first and roll back on failure. A crash between the write and the check would leave a broken file.
- Check only that the edited file parses. That misses edits that parse but change other requirements, which is what the nested requirement bug did.

### Refuse Jinja2 conditionals in rules

Two `srg_gpos` requirements select rules per product inside `{{% if %}}` blocks. Replacing that list would drop the other products' rules, and there is no right place for new rules inside the conditionals. The updater refuses and asks for a manual edit. The same applies to a requirement with two `rules` or `status` keys, or one split by a Jinja2 statement at a lower indentation.

### Reject old status names

`not_applicable` and `partially_automated` could be mapped to `not applicable` and `partial`. They are rejected with the replacement in the error instead, to match `canonical-control-status`, which removed them, and so a caller learns the real names in one retry. The model, the updater, and the tool schema all take the statuses from one `ControlStatus` definition.
