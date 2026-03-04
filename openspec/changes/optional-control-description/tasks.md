## 1. Model Changes

- [x] 1.1 Make `ControlRequirement.description` optional (`str | None`, default `None`) in `src/content_agent/models/control.py`
- [x] 1.2 Make `IndexedRequirement.description` optional (`str | None`, default `None`) in `src/content_agent/models/control.py`

## 2. Fix Downstream Description Access

- [x] 2.1 Guard `req.description` access at line 255 in `core/discovery/controls.py` (text search — skip or use `""` when `None`)
- [x] 2.2 Guard `req.description` access at line 536 in `core/discovery/controls.py` (tokenization for similarity — use `""` when `None`)
- [x] 2.3 Populate `IndexedRequirement.description` with `req.description or ""` at line 546 in `core/discovery/controls.py`

## 3. Verification

- [x] 3.1 Update or add unit tests for `ControlRequirement` with and without `description`
- [x] 3.2 Run `pytest` and verify all tests pass
- [x] 3.3 Run `mypy src/` and verify no type errors from the change
- [x] 3.4 Run `black --check src/ tests/ && ruff check src/ tests/` and verify lint passes
