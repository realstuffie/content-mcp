## 1. Parameters

- [x] 1.1 Parse each section of `template_reference.md` into a description and parameters
- [x] 1.2 Scan the template blocks of rules, with Jinja2 dropped, and cache the result per repository
- [x] 1.3 Combine documented and used parameters, with required flags, types, defaults and usage counts
- [x] 1.4 Return supported languages and an example from a real rule
- [x] 1.5 Describe templates in `list_templates`
- [x] 1.6 Remove the CSV readers and the invented fallback

## 2. Models and tool

- [x] 2.1 Add `used_by_rules` to `TemplateParameter`, and `supported_languages`, `used_by_rules` and `example_rule` to `TemplateSchema`
- [x] 2.2 Describe the sources and `name@product` overrides in the tool description

## 3. Verification

- [x] 3.1 Unit tests for each case
- [x] 3.2 Integration tests against content at `f09d243`, including that every templated rule is read
- [x] 3.3 Compare all 65 templates before and after
