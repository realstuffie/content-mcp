## Why

`validate_rule_yaml` required `documentation_complete`, so it reported 9 OpenShift rules at `f09d243` as invalid. The content build doesn't require the field: a rule without it is complete. The validator also didn't say what the field does. The build leaves a rule out, outside Debug builds, only when the value's text is exactly `false`, because ComplianceAsCode's YAML loader keeps booleans as text. A rule written with `documentation_complete: False` is still built, which is easy to get wrong.

## What Changes

- Stop requiring `documentation_complete`.
- Warn when it is `false`, quoted or not, that the build leaves the rule out, and when it is another spelling such as `False`, `no` or `yes`, what the build makes of it. These warnings don't make a rule invalid.
- Stop putting `documentation_complete` back after Jinja2 expansion, since nothing requires it now.

## Capabilities

### New Capabilities

- `rule-validation`: `documentation_complete` is checked as the build reads it.

## Impact

- **Affected code**: `core/scaffolding/validators.py`.
- **Results** at `f09d243`: invalid rules go from 9 of 2566 to 0. For `true`, `false`, `'false'`, `"false"`, `False`, `FALSE`, `no`, `off`, `yes`, `True` and no line at all, the validator says the rule is left out exactly when ComplianceAsCode's loader raises `DocumentationNotComplete`.
