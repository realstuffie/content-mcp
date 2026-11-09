## Turn off the template cache

`AbsolutePathFileSystemLoader.get_source` returns an `uptodate` function that
compares only `os.path.getmtime`. Jinja2's environment reuses a compiled
template while that returns true. `expand_yaml()` sets the environment's
`cache` to `None` after each expansion, so every expansion compiles its file
again. The bytecode cache, when a product enables it, checks a hash of the
source, so it stays.

Compiling a rule takes about 1.3 ms more than reusing it. The cache holds 400
templates, and there are 2566 rules, so most expansions compiled anyway. The
profile index takes 12.8 s to build, against 12.4 s before.

## Drop the environment when its inputs change

`ssg.jinja` makes its environment on the first expansion: it compiles every
file in `shared/macros` into globals and adds that expansion's variables.
`expand_yaml()` records the state of the macro, `product.yml` and
`product_properties` files just before the environment is made. Before each
expansion it compares the state. If it changed, or the environment wasn't made
through `expand_yaml()`, it sets `ssg.jinja`'s environment to `None`, and
`ssg.jinja` makes a new one. Before October 2025, `ssg.jinja` kept the
environment on `_get_jinja_environment.env`, so both places are handled.

Making an environment takes about 0.5 s. The check takes about 0.4 ms per
expansion.

## Hash recent files

Linux takes file timestamps from a clock that ticks every few milliseconds,
unless a kernel from 6.13 on uses a finer one for a file someone has just
checked. A same-size rewrite in the tick of the last check can keep mtime,
ctime and size. Files whose mtime or ctime is within five seconds of the check
also get a SHA-256 hash, which covers that, FAT's 2-second steps, and a file
server's clock running behind. A later check hashes the same files again even
once they're older, so the comparison stays like for like.

On Windows, `st_ctime` is the creation time and doesn't change on a rewrite,
so every file is hashed there.

## Remove the small caches

`list_products()` reads every `product.yml`, about 55 to 65 ms. Control tools
used it only to check product names. They now list the product directories
instead, which takes well under 1 ms, so the product list needs no cache.
`get_template_schema` reads every rule's template block, about 0.7 s per call.
