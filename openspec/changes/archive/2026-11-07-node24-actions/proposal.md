## Why

Every CI run warned that actions run on Node.js 20, which GitHub Actions is retiring. `actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4` and `codecov/codecov-action@v4` all declare `node20`.

## What Changes

- Move all three workflows to the current majors: `actions/checkout@v7`, `actions/setup-python@v7`, `actions/upload-artifact@v7` and `codecov/codecov-action@v7`. `pypa/gh-action-pypi-publish` is a Docker action and is unchanged.
- Rename the Codecov input `file` to `files`; v5 and later dropped `file`.

## Decisions

- **Latest majors, not the first Node 24 ones.** Each action's `action.yml` was read at every major tag. checkout runs on Node 24 from v5 and setup-python from v6; upload-artifact needs v6. Codecov v5 is a composite action that still calls `actions/github-script` v7.0.1, which is `node20`, so it would keep the warning; v6 and v7 call `github-script` v8, which is `node24`. The latest majors stay supported longest, and none of their breaking changes apply here: checkout v6 moved stored credentials out of `.git/config` and v7 refuses fork code under `pull_request_target`, which these workflows don't use; setup-python v7 changed only internals; upload-artifact v7 still zips by default.
- **Codecov stays optional.** Since v5, Codecov needs a token for uploads outside fork pull requests. The step keeps `fail_ci_if_error: false`, so without a `CODECOV_TOKEN` secret the upload fails quietly and CI is unaffected.

## Capabilities

No capability changes.

## Impact

- **Affected files**: `.github/workflows/ci.yml`, `.github/workflows/content-drift.yml`, `.github/workflows/release.yml`.
- All three workflows pass actionlint 1.7.12.
