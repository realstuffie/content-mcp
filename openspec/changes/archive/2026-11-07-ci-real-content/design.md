## Context

The integration tests need a ComplianceAsCode/content checkout, found through `CONTENT_REPO`. ComplianceAsCode/content changes daily, and the server reads its formats directly: control files, requirement files, profiles, `rule.yml` files with Jinja2, `product.yml` and `product_properties`. A format change there can break the server without any change here.

## Goals / Non-Goals

**Goals:**
- Run the integration tests in CI against real content.
- A red CI run on a push or pull request should mean the change broke something.
- Find out when content changes a format the server reads, even in weeks with no changes here.

**Non-Goals:**
- Testing tools that need build artifacts, which would mean running the content build in CI.

## Decisions

### 1. Pinned content commit for CI, plus a separate drift workflow against master

**Choice:** The test job checks out the content commit in `CONTENT_REF` in `ci.yml`. A separate "Content drift" workflow runs the integration tests against content master every Monday and on demand. It doesn't block anything.

**Rationale:** Results on pushes and pull requests depend only on the change being tested. Format changes in content still show up within a week, as a failing drift run instead of as unrelated failures on someone's pull request. When the drift workflow passes, bumping `CONTENT_REF` to the commit it prints is a one-line change. When it fails, the fix and the bump go in one pull request.

**Alternative considered:** Test against content master in the main job. It catches format changes on the next run, but a pull request can fail because content changed, and the failure looks like the pull request's fault.

**Alternative considered:** Pin a content commit without a drift workflow. Results are stable, but nothing says when the pin falls behind or when content breaks the server, and these bugs went unnoticed for months.

### 2. Shallow checkout with actions/checkout

**Choice:** Check out content with `actions/checkout`, `fetch-depth: 1`, into `cac-content` in the workspace.

**Rationale:** The integration tests need only the files at one commit. A shallow checkout takes a few seconds and about 155 MB. `actions/checkout` handles the pinned commit and authentication without extra scripting. The checkout sits outside `src/` and `tests/`, so black, ruff and pytest don't look at it.

### 3. Python 3.11 to 3.14

**Choice:** Test every version from the minimum in `requires-python` to the newest release.

**Rationale:** Installs on different Python versions can get different dependencies. An install on 3.13 got `mcp` 2.x, which crashed the server on startup, while one on 3.14 got 1.30. Testing only 3.11 and 3.12 would miss failures like that.

### 4. Blocking mypy

**Choice:** Remove `continue-on-error` from the mypy step.

**Rationale:** mypy is now clean. While it was non-blocking, its errors included two real bugs: the server failing to start with `mcp` 2.x, and `temperature` breaking every AI request with `anthropic` 2.x.

## Risks / Trade-offs

- **The pin falls behind if nobody bumps it.** The drift workflow shows when the pin is stale, but bumping it is manual.
- **Integration tests cost CI time.** About 3 minutes per Python version.
- **Scheduled workflows on forks** only run while the fork has Actions enabled, and GitHub disables schedules on repositories with no activity for 60 days.
