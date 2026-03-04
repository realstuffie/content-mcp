## 1. Model Changes

- [ ] 1.1 Make `ControlRequirement.description` optional (`str | None`, default `None`) in `src/content_agent/models/control.py`
- [ ] 1.2 Make `IndexedRequirement.description` optional (`str | None`, default `None`) in `src/content_agent/models/control.py`

## 2. Fix Downstream Description Access

- [ ] 2.1 Guard `req.description` access at line 255 in `core/discovery/controls.py` (text search — skip or use `""` when `None`)
- [ ] 2.2 Guard `req.description` access at line 536 in `core/discovery/controls.py` (tokenization for similarity — use `""` when `None`)
- [ ] 2.3 Populate `IndexedRequirement.description` with `req.description or ""` at line 546 in `core/discovery/controls.py`

## 3. Verification

- [ ] 3.1 Update or add unit tests for `ControlRequirement` with and without `description`
- [ ] 3.2 Run `pytest` and verify all tests pass
- [ ] 3.3 Run `mypy src/` and verify no type errors from the change
- [ ] 3.4 Run `black --check src/ tests/ && ruff check src/ tests/` and verify lint passes
