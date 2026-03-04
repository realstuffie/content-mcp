## 1. Model

- [x] 1.1 Update `ControlRequirement.status` Literal in `src/content_agent/models/control.py` to use the 10 canonical statuses from `control.json`

## 2. Tests

- [x] 2.1 Update `tests/unit/test_control_stats.py` to use canonical status values (`partial` instead of `partially_automated`, `not applicable` instead of `not_applicable`)
- [x] 2.2 Check and update any other test files referencing old status values

## 3. Verification

- [x] 3.1 Run `pytest tests/unit/ -v` and confirm all tests pass
- [x] 3.2 Run `black --check src/ tests/` and `ruff check src/ tests/` to confirm compliance
