## Why

`ssg.jinja` makes its environment from the variables of the first expansion
and compiles the macros against them. Macros read product variables from the
environment, not from the variables of each expansion. After the server
expanded a rhel9 rule, an ubuntu2204 rule's `describe_package_install()` said
`dnf install aide` instead of `apt-get install aide`. A fresh environment gives
the right command.

## What changes

- Keep one environment per set of variables, up to 16, and put the right one in
  `ssg.jinja` before each expansion.
- Make environments with `ssg.jinja`'s bytecode cache in a temporary directory,
  so each one after the first takes about 13 ms instead of 0.5 s.
- Pass `ssg.jinja` a copy of the variables, so the caller's dict isn't changed.

## Capabilities

### Modified capabilities

- `jinja2-rule-expansion`: expand with the variables of the product being expanded.

## Scope

Profile memberships at content `f09d243` are the same before and after. The
change affects rendered text, such as descriptions and OCIL, for every product
but the first one expanded.
