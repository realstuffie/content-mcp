## One environment per set of variables

The key is the variables, sorted by name, as text. A product's variables are
the same on every call while its files are unchanged, so each product gets one
environment. Expansions without a product, and the fallback that keeps
`{{{ full_name }}}` as text, get their own.

Before each expansion, `expand_yaml()` sets `ssg.jinja`'s environment to the
one for the key, or to `None`, in which case `ssg.jinja` makes one from these
variables. Afterwards it turns the template cache off and keeps the
environment, dropping the least recently used beyond 16.

## Bytecode cache

Making an environment compiles every file in `shared/macros`, about 0.5 s.
`ssg.jinja` uses a `jinja2.FileSystemBytecodeCache` when the variables set
`jinja2_cache_enabled` to `"true"` and name `jinja2_cache_dir`. With it, each
environment after the first loads the compiled macros in about 13 ms. The
cache stores a hash of each template's source and compiles again when it
differs, so a changed file is never served from it. The directory is made with
`tempfile.mkdtemp()` and removed when the process exits. After building the
profile index it holds about 4 MB.

## Cost

| Measure | One environment | One per product |
|---|---|---|
| Profile index build | 12.8 s | 13.4 s |
| Environments made during the build | 1 | 8 |
| Memory per environment | | about 2 MB |
