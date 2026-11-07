## Why

Profile discovery listed every `.profile` file as available for scans. Hidden
default profiles contribute otherwise unselected rules to the benchmark but
do not become XCCDF profiles. The server counted them alongside selectable
profiles and reported them as rule memberships. Ubuntu 24.04 listed six
profiles where five are selectable.

## What changes

- Parse `hidden` and return it in profile summaries and details.
- Omit hidden profiles from normal lists and product profile IDs. Add
  `include_hidden` to the Python and MCP list tools for explicit inspection.
- Keep explicit hidden-profile detail reads and inheritance working.
- Keep hidden profiles' rules in product searches, while excluding their
  names from selectable-profile memberships.
- Cache the hidden rule sets alongside selectable memberships.
- Compare visibility with ComplianceAsCode's actual profile loader and test
  the listing, search, inheritance, cache, and MCP behavior.

## Capabilities

### New capabilities

- `profile-visibility`: distinguish selectable profiles from hidden profiles.

### Modified capabilities

- `rule-product-availability`: omit hidden profile memberships while preserving
  their benchmark rules in product-filtered searches.

## Impact

At content commit `f09d243`, listings contain 291 selectable profiles instead of
all 321 source profiles. The other 30 remain available with `include_hidden`.
The selectable-profile count for `accounts_umask_interactive_users` is 10
products instead of 11. Ubuntu 22.04 rule search still returns 639 rules.
