## Why

Every control tool that takes a product checks that the product exists by listing products, which parses all 40 `product.yml` files. The MCP server makes a new discovery object for each tool call, so this happened on every call: about 50 ms of each `get_requirement_file_path`, `list_controls` or `get_control_details` call at `f09d243`. `get_requirement_file_path` also expanded the whole control file with Jinja2, though it only needs its `controls_dir` line.

## What Changes

- Reuse the product list between calls, and rebuild it when a `product.yml` is added, removed or modified. Callers get their own copy.
- Read `controls_dir` from the control file's text in `get_requirement_file_path` and `update_requirement_rules`, in a shared `controls_dir_setting`.

## Capabilities

No capability changes. Results are the same; calls are faster.

## Impact

- **Affected code**: `core/discovery/products.py`, `core/discovery/controls.py`, `core/scaffolding/control_updater.py`.
- **Results** at `f09d243`, median of 10 calls after the first, each with a new discovery object as the server makes them:

| Call | Before | After |
|---|---|---|
| `get_requirement_file_path("nist_800_53", "ac-2", product="rhel9")` | 58 ms | 1 ms |
| `get_requirement_file_path("cis_ubuntu2204", "5.4.3.3", product="ubuntu2204")` | 66 ms | 1 ms |
| `list_controls(product="rhel9")` | 55 ms | 1 ms |
| `get_control_details("anssi", product="rhel9")` | 89 ms | 39 ms |

  `get_control_details` still parses the whole policy. All 19392 requirements are still located, and the requirement counts of all 70 policies still match the build.
