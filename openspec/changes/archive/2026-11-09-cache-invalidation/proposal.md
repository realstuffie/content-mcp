## Why

The shared profile index is reused while its signature matches. The signature
was the number of profile and control files and their newest modification
time. That missed two kinds of change:

- Inputs outside the signature. Building the index also reads each `rule.yml`
  (`documentation_complete`, and the attributes `filter_rules` tests),
  `product.yml` (rule directories) and `product_properties` (Jinja2 variables).
  Changing a rule's `platform` left a stale OpenShift profile membership until
  the server restarted.
- Changes hidden by the newest time. With files at times 100 and 200, moving the
  first to 150 kept the signature at `(2, 200)`, and the next call reused the
  old index.

The template usage map behind `get_template_schema` used the same count and
newest-time signature over rule files.

## What changes

- Add `content_state`, which records each input file's path, `st_mtime_ns`,
  `st_ctime_ns` and size, and lists rule directories down to each rule.
- Check the profile index against profiles, control files, every `rule.yml`
  under the rule directories product files name, `product.yml` files and
  `product_properties`.
- Check the template usage map against rule files and `product.yml` files.
- Add `configured_rule_roots`, which returns each named rule directory, whether
  it exists or not.
- Take the state before a build, so a file that changes during it is noticed on
  the next call.

## Capabilities

### Modified capabilities

- `rule-product-availability`: rebuild the shared index when any input changes.
- `template-parameters`: refresh the rule scan the same way.

## Scope

Only cache invalidation changes. The index and the template map are built as
before. Restarting the server still clears both caches.
