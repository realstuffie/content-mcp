## Read the hidden field

Use the profile's `hidden` field rather than its filename. Hidden profiles can
have other names, and a file named `default.profile` can be selectable.
Summaries and details expose a boolean `hidden` field.

Match ComplianceAsCode's loader and serializer. Its YAML loader preserves
boolean scalars as text, and `Profile.to_xml_element` tests the value's
truthiness. Even `hidden: false` is hidden in that build. The parser treats YAML
boolean values as nonempty strings for this check. Absent, null, empty, and
numeric zero values remain false. Integration tests compare these cases with
`ssg.entities.profile_base.Profile.from_yaml`.

## Separate selectable memberships from benchmark rules

The default profile keeps otherwise unselected rules in the benchmark. Removing
its rules from the existing reverse index would make those rules disappear
from product searches. Instead, the index stores selectable memberships and
hidden rule sets separately. Product searches use both; availability returns
only selectable profile names.

A selectable profile can extend a hidden parent. Detail lookup still reads the
parent, so inherited rules belong to the selectable child. Hidden profiles
remain available through explicit detail reads and `include_hidden=true`.
The collection resource and product profile IDs use the default visible list.

## Cache both results

The shared index now stores the hidden rule sets alongside memberships. Both
use the existing profile and control file signature. A new discovery instance
must retain hidden-only search results when it reuses that cache, and a changed
hidden flag must rebuild it. Unit tests cover both cases.

## Verification

The real-content test finds five selectable Ubuntu 24.04 profiles and six with
hidden profiles included. Product details match the selectable list. Hidden
default names do not appear in rule availability, and Ubuntu 22.04 searches
still find all 639 rules. Eight flag values match the real SSG profile loader.

The test suite also covers hidden parents, visible files named default,
non-default hidden files, cache reuse and invalidation, and MCP calls.

All 516 tests pass against content at `f09d243`. The 48 warnings come from
Jinja2 escape sequences in the content checkout's macros. Overall coverage
remains 80%. Formatting, Ruff, mypy, and whitespace checks pass.
