# Tests

## Overview

This directory contains unit and integration tests for the content-agent.

The MCP resource regression tests use SDK sessions and temporary content.
They run without a real content checkout.

```bash
pytest tests/integration/test_mcp_protocol.py -q
```

## Test Structure

```
tests/
├── conftest.py           # Pytest fixtures and configuration
├── unit/                 # Unit tests (fast, no external dependencies)
│   ├── test_models.py
│   ├── test_config.py
│   └── test_validators.py
└── integration/          # Integration tests (require content repo)
    ├── test_tools.py
    └── test_resources.py
```

## Running Tests

### Install Test Dependencies

```bash
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run Only Unit Tests

```bash
pytest tests/unit/
```

### Run Only Integration Tests

Integration tests require a ComplianceAsCode/content repository. They are
**automatically skipped** when no repo is detected, and **automatically run**
when one is found. Detection checks two locations in order:

1. `CONTENT_REPO` environment variable (explicit path)
2. `~/.content-agent/content` (default managed path)

```bash
# Option A: point to an existing clone
CONTENT_REPO=/path/to/content pytest tests/integration/

# Option B: clone to the default location (auto-detected)
git clone --depth 1 https://github.com/ComplianceAsCode/content.git ~/.content-agent/content
pytest tests/integration/
```

### Run with Coverage

```bash
pytest --cov=content_agent --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run Specific Test

```bash
# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestProductModels

# Run specific test method
pytest tests/unit/test_models.py::TestProductModels::test_product_summary_creation
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Debug Output

```bash
pytest -s  # Show print statements
pytest --log-cli-level=DEBUG  # Show debug logs
```

## Test Categories

### Unit Tests

**Fast, isolated tests** that don't require external dependencies:

- `test_models.py` - Data model validation and serialization
- `test_config.py` - Configuration loading and merging
- `test_validators.py` - YAML validation logic

These should always pass and run quickly.

### Integration Tests

**Slower tests** that require a ComplianceAsCode/content repository:

- `test_tools.py` - MCP tool handlers
- `test_resources.py` - MCP resource handlers

These use `@requires_content_repo` (a conditional `skipif` marker from
`conftest.py`) and are automatically skipped when no repo is detected.
To run them, make a content repo available:

```bash
git clone --depth 1 https://github.com/ComplianceAsCode/content.git ~/.content-agent/content
pytest tests/integration/
```

Or point to an existing clone:

```bash
CONTENT_REPO=/path/to/content pytest tests/integration/
```

## Writing Tests

### Unit Test Example

```python
import pytest
from content_agent.models import ProductSummary

def test_product_creation():
    """Test creating a ProductSummary."""
    product = ProductSummary(
        product_id="rhel9",
        name="RHEL 9",
        product_type="rhel"
    )

    assert product.product_id == "rhel9"
```

### Integration Test Example

```python
import pytest
from tests.conftest import requires_content_repo

@requires_content_repo
class TestWithContent:
    """Tests that need a real ComplianceAsCode/content repo."""

    @pytest.mark.asyncio
    async def test_something(self, real_content_repo):
        """Test with actual content. The real_content_repo fixture
        initializes settings and the content repository."""
        # Test code here
        pass
```

### Using Fixtures

```python
def test_with_temp_dir(temp_dir):
    """Test using temp_dir fixture from conftest.py."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test")
    assert test_file.exists()
```

## CI/CD

For continuous integration:

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: pytest tests/unit/ -v

- name: Run integration tests
  run: |
    git clone --depth 1 https://github.com/ComplianceAsCode/content.git /tmp/content
    CONTENT_REPO=/tmp/content pytest tests/integration/ -v
```

## Test Fixtures

Available fixtures (see `conftest.py`):

- `temp_dir` - Temporary directory (auto-cleaned)
- `sample_rule_yaml` - Sample rule.yml content
- `sample_product_yaml` - Sample product.yml content
- `sample_profile_content` - Sample profile content
- `mock_content_repo` - Mock content repository structure (for unit tests)
- `initialized_content_repo` - Mock repo with global state initialized (for unit tests)
- `real_content_repo` - Real ComplianceAsCode/content repo, session-scoped (for integration tests; requires `CONTENT_REPO` env var or `~/.content-agent/content`)

Additionally, `requires_content_repo` is a `skipif` marker importable from `tests.conftest` that skips tests when no real content repo is available.

## Coverage Goals

- Overall: > 80%
- Core modules: > 90%
- Models: 100%

Current coverage:
```bash
pytest --cov=content_agent --cov-report=term-missing
```

## Debugging Failed Tests

### Get More Information

```bash
# Verbose output
pytest -vv

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Stop on first failure
pytest -x
```

### Common Issues

1. **ModuleNotFoundError**
   - Solution: `pip install -e ".[dev]"`

2. **Integration tests skipped**
   - Check: `echo $CONTENT_REPO` or verify `~/.content-agent/content` exists
   - Solution: Set `CONTENT_REPO=/path/to/content` or clone to `~/.content-agent/content`

3. **Import errors**
   - Solution: Run tests from project root, not tests/

## Best Practices

1. **Keep tests fast** - Unit tests should run in milliseconds
2. **Test one thing** - Each test should verify one behavior
3. **Use descriptive names** - `test_validates_missing_title_field` not `test1`
4. **Clean up resources** - Use fixtures and context managers
5. **Mock external dependencies** - Don't rely on network/filesystem in unit tests
6. **Test error cases** - Not just happy paths
7. **Document complex tests** - Add docstrings explaining what's being tested

## Adding New Tests

When adding a new feature:

1. Write unit tests for the core logic
2. Write integration tests for the MCP handlers
3. Update coverage goals if needed
4. Run all tests before committing:
   ```bash
   pytest && echo "✓ All tests passed"
   ```
