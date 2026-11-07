## Context

ComplianceAsCode has no machine-readable list of template parameters. The reference documents them in Markdown, each template's `template.py` reads them from a `data` dict, and rules set them in their `template` block. The reference is the only source of descriptions, but it is incomplete: at `f09d243`, 16 template directories have no section, two sections list no parameters, and 43 parameters that rules set are not documented.

## Decisions

### Combine the reference with real rule usage

The reference gives names and descriptions. The rules show what is actually used: how often each parameter is set, the value types, and parameters the reference leaves out. Together they cover 59 of the 65 templates, against 49 with the reference alone.

`template.py` was the other candidate. It shows which keys a template reads, but not which are required, and pulling key names out of Python code means pattern-matching `data["x"]`, `data.get("x")` and helper calls, which is fragile.

### Read only the template block of each rule

Loading every rule with Jinja2 expansion, as `RuleDiscovery` does, takes several seconds per pass. The scan instead cuts out each rule's `template:` block with a regular expression and parses it as YAML. Jinja2 statements are dropped, so a rule that sets a parameter in either branch of an `{{% if %}}` counts once, and expressions become a placeholder. All 1740 templated rules at `f09d243` read this way.

The result is cached per content repository and keyed on the rule files' count and newest modification time, like the profile index.

### Required means "a rule needs to set it"

The reference rarely says that a parameter is required. A documented parameter counts as required unless its description says "optional" or mentions a default, or some rule using the template leaves it out. That second check catches pairs like `sshd_lineinfile`'s `value` and `xccdf_variable`, where rules set one or the other. A parameter only rules set is required when every rule sets it. Each parameter also carries `used_by_rules`, so a caller can judge the evidence.

### Examples come from real rules

The example is the smallest `vars` block that sets every required parameter, preferring rules without Jinja2 or product overrides, so it can be copied as it is. The rule ID is returned with it.

### Drop the invented fallback

For a template with no `template.yml`, the old code returned a parameter called `parameter`, described as "Template-specific parameter". That reads as real data. A template with nothing documented and no rules now returns no parameters.
