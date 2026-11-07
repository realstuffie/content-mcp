## Why

`get_template_schema` returned no parameters for any of the 65 templates at `f09d243`. Every template has a `template.yml`, and the parser for it was a stub that returned an empty list. The fallbacks read per-template CSV files, a format ComplianceAsCode no longer uses, or made up a parameter called `parameter`. No template had a description or an example either. An agent writing a templated rule, as about two thirds of rules are, had only the raw reference text to go on.

## What Changes

- Read each template's parameters from its section of `docs/templates/template_reference.md`.
- Read the `vars` of every templated rule, to count how many rules set each parameter, find the YAML types they use, and list parameters the reference leaves out.
- Mark parameters required or optional from the reference text and from whether every rule sets them, and return documented defaults.
- Return the template's supported languages from `template.yml`, and the vars of a real rule as the example.
- Describe templates in `list_templates` and `get_template_schema` with the first paragraph of their section.
- End a template's documentation at the next heading of any level up to 4, outside code blocks, instead of only at the next `####`.
- Remove the CSV readers and the invented fallback parameter.

## Non-goals

- Platform templates (`platform_*`), which CPE definitions in `shared/applicability/` use rather than rules.
- Listing a parameter's allowed values. The reference states them in prose.
- Reading template parameters from `template.py`.

## Capabilities

### New Capabilities

- `template-parameters`: parameters, required flags, types, supported languages, examples, and descriptions for templates.

### Modified Capabilities

- `template-documentation`: a section ends at the next heading of level 1 to 4, outside code blocks.

## Impact

- **Affected code**: `core/discovery/templates.py`, `models/profile.py` (new fields on `TemplateParameter` and `TemplateSchema`; `example_usage` values are no longer only strings), `server/handlers/tools.py`.
- **Results** at `f09d243`: templates with parameters go from 0 to 59 of 65, with a description from 0 to 49, and with an example from 0 to 58. All 1740 templated rules are read. The 6 templates left without parameters are the 5 platform templates and `argument_in_file`, which is undocumented and unused.
- **Cost**: the first call scans the rule files in about 1 second. Later calls check the rule files' modification times, about 65 ms.
