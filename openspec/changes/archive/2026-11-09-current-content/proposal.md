## Why

The file-state check from the previous change still let stale content through:

- `ssg.jinja` keeps one Jinja2 environment for the process. Its loader treats a
  compiled template as current while the file's mtime is unchanged. A rule
  rewritten with its old mtime and size was noticed by the profile index, but
  the rebuild expanded the old contents. Rule and control reads outside the
  index had the same problem.
- The environment compiles `shared/macros` once and keeps the variables of the
  expansion that made it. A changed macro or product file never reached it.
- A rewrite with the same size within one clock tick of the last check can keep
  mtime, ctime and size.
- The product list and the template usage map were cached to save 55 to 65 ms
  and 0.7 s. Each cache needs its own invalidation, which is more to get wrong
  than the time saved.

## What changes

- Expand rules and control files through `expand_yaml()`, which turns off the
  `ssg.jinja` template cache and drops the environment when a macro file, a
  `product.yml` or a `product_properties` file changes.
- Hash files changed in the last five seconds, and keep hashing them in later
  checks. Hash every file where ctime is a creation time.
- Watch `shared/macros` for the profile index.
- Remove the product list and template usage caches. Control tools check a
  product name against the product directories, without reading every
  `product.yml`, which keeps them at about 1 ms.

## Capabilities

### Modified capabilities

- `rule-product-availability`: hash recent files and watch macros.
- `jinja2-rule-expansion`: expansions read current files.
- `template-parameters`: read rule files on each call.
- `per-product-control-discovery`: check product names against directories.

## Scope

The profile index is the only result kept between tool calls. Results for
different products can still differ from the build, because the one
environment renders macros with the variables of the product that made it.
The next change addresses that.
