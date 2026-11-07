## Why

CI never tested against real ComplianceAsCode content. The test job had no content checkout, so every integration test was skipped, and the bugs fixed since (nested requirements, untitled requirements, profile parsing, control selections, Jinja2 in rules and requirement files) were invisible to it. CI also stopped at Python 3.12 while the server runs on 3.13 and 3.14, and mypy ran with `continue-on-error`, so type errors, including two real bugs, piled up unnoticed.

A clean install also couldn't load ComplianceAsCode's `ssg` modules, because they import `jinja2`, which wasn't a dependency.

## What Changes

- Check out a pinned ComplianceAsCode/content commit in the test job, so the integration tests run.
- Add a weekly "Content drift" workflow that runs the integration tests against content master.
- Test Python 3.11 to 3.14.
- Make mypy blocking.
- Allow running CI by hand (`workflow_dispatch`).
- Add `jinja2` to the dependencies.

## Non-goals

- Building content (`build_product`) in CI. Tests that need build artifacts still skip.
- Automating bumps of the pinned content commit.

## Capabilities

No capability changes. This changes how the existing behavior is tested.

## Impact

- **Affected files**: `.github/workflows/ci.yml`, `.github/workflows/content-drift.yml` (new), `pyproject.toml`, `CLAUDE.md`.
- **Results**: in a local run of the CI steps from a clean install, 313 tests pass, with 0 skipped, against the pinned commit. Before, the 50 integration tests were skipped. Coverage rises from about 58% to 68%. The integration tests also pass against content master as of `bb706dd` (2026-11-06).
- **Cost**: each test job takes about 3 minutes longer, for 4 Python versions.
