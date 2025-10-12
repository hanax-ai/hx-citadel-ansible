# HX-Citadel Shield Test Suite

**Phase 2 Sprint 2.2**: Automated Testing (TASK-031)

## Overview

Comprehensive test suite for the HX-Citadel Shield production readiness project, covering unit tests, integration tests, and load tests.

---

## Directory Structure

```text
tests/
├── README.md                    # This file
├── __init__.py                  # Test package init
├── conftest.py                  # Shared pytest fixtures
│
├── unit/                        # Unit tests (fast, isolated)
│   ├── __init__.py
│   └── test_common_types.py     # Common types module tests
│
├── integration/                 # Integration tests (slower, end-to-end)
│   ├── __init__.py
│   └── test_mcp_server_health.py  # MCP server integration tests
│
├── load/                        # Load and performance tests
│   ├── __init__.py
│   └── locustfile.py            # Locust load test scenarios
│
├── fixtures/                    # Test data and fixtures
│   └── __init__.py
│
├── utils/                       # Test utilities
│   ├── __init__.py
│   └── helpers.py               # Helper functions
│
└── reports/                     # Test reports (generated)
    ├── test-report.html         # HTML test report
    ├── coverage.xml             # Coverage XML report
    └── pytest.log               # Test execution logs
```

---

## Quick Start

### Install Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run in parallel
pytest -n auto

# Run with verbose output
pytest -v
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests only
pytest -m integration

# MCP server tests
pytest -m mcp

# Slow tests (skip for quick validation)
pytest -m "not slow"

# Fast tests only
pytest -m fast
```

### Run Tests for Specific Components

```bash
# Common types tests
pytest tests/unit/test_common_types.py

# MCP server health tests
pytest tests/integration/test_mcp_server_health.py

# Specific test
pytest tests/unit/test_common_types.py::TestEnumerations::test_job_status_enum_values
```

---

## Test Categories

### Unit Tests

**Location**: `tests/unit/`

**Characteristics**:
- Fast execution (< 1s per test)
- No external dependencies
- Test individual functions/classes in isolation
- Use mocks for external services

**Markers**: `@pytest.mark.unit`, `@pytest.mark.fast`

**Examples**:
- Type definitions validation
- Utility function tests
- Template structure tests

### Integration Tests

**Location**: `tests/integration/`

**Characteristics**:
- Slower execution (1-30s per test)
- Test interactions between components
- May require running services
- Test end-to-end workflows

**Markers**: `@pytest.mark.integration`, `@pytest.mark.slow`

**Examples**:
- MCP server health checks
- Orchestrator API calls
- Database operations
- Circuit breaker behavior

### Load Tests

**Location**: `tests/load/`

**Tool**: Locust

**Characteristics**:
- Performance and stress testing
- Concurrent user simulation
- Resource utilization monitoring

**Examples**:
- Circuit breaker under load
- Concurrent MCP tool calls
- Job queue stress tests

---

## Configuration

### pytest.ini

Main pytest configuration file at project root. Defines:
- Test discovery patterns
- Coverage settings
- Markers
- Logging configuration

### conftest.py

Shared fixtures for all tests:
- **HTTP clients**: `async_client`, `mcp_client`, `orchestrator_client`
- **Mock fixtures**: `mock_http`, `mock_orchestrator_response`
- **Configuration**: `test_config`, `project_root`
- **Test data**: `sample_text`, `sample_query`, `sample_metadata`

---

## Available Fixtures

### HTTP Clients

```python
async def test_example(async_client: httpx.AsyncClient):
    response = await async_client.get("http://example.com")
    assert response.status_code == 200
```

### Service-Specific Clients

```python
async def test_mcp(mcp_client: httpx.AsyncClient):
    # Pre-configured for MCP server
    response = await mcp_client.get("/sse")

async def test_orchestrator(orchestrator_client: httpx.AsyncClient):
    # Pre-configured for orchestrator
    response = await orchestrator_client.get("/healthz")
```

### Mocking HTTP Requests

```python
def test_with_mock(mock_http: respx.MockRouter):
    mock_http.get("http://example.com").respond(json={"status": "ok"})
    # Your test code here
```

### Test Data

```python
def test_with_data(sample_text: str, sample_metadata: Dict[str, Any]):
    # Use pre-defined test data
    assert len(sample_text) > 0
    assert "source" in sample_metadata
```

---

## Test Markers

Use pytest markers to organize and run tests selectively:

| Marker | Description | Usage |
|--------|-------------|-------|
| `unit` | Unit tests | `pytest -m unit` |
| `integration` | Integration tests | `pytest -m integration` |
| `slow` | Slow-running tests | `pytest -m "not slow"` |
| `fast` | Fast tests | `pytest -m fast` |
| `mcp` | MCP server tests | `pytest -m mcp` |
| `orchestrator` | Orchestrator tests | `pytest -m orchestrator` |
| `ansible` | Ansible playbook tests | `pytest -m ansible` |
| `circuit_breaker` | Circuit breaker tests | `pytest -m circuit_breaker` |
| `smoke` | Smoke tests | `pytest -m smoke` |

---

## Coverage Reports

### Generate Coverage Reports

```bash
# HTML report (interactive)
pytest --cov=tests --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=tests --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=tests --cov-report=xml
```

### Coverage Targets

- **Overall**: 80%+ coverage
- **Critical components**: 90%+ coverage
- **New code**: 100% coverage

---

## Writing New Tests

### Unit Test Template

```python
import pytest

@pytest.mark.unit
@pytest.mark.fast
class TestMyComponent:
    """Test MyComponent functionality"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        result = my_function()
        assert result == expected_value

    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            my_function(invalid_input)
```

### Integration Test Template

```python
import pytest
import httpx

@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_flow(async_client: httpx.AsyncClient):
    """Test end-to-end flow"""
    response = await async_client.get("http://service/endpoint")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

---

## Best Practices

### 1. Test Naming

- **Files**: `test_*.py` or `*_test.py`
- **Classes**: `Test*`
- **Functions**: `test_*`
- **Be descriptive**: `test_circuit_breaker_opens_after_5_failures`

### 2. Test Organization

- One test file per module
- Group related tests in classes
- Use markers for categorization

### 3. Assertions

- Use descriptive assertion messages
- Test one concept per test
- Use pytest's rich assertion introspection

### 4. Fixtures

- Use fixtures for setup/teardown
- Scope fixtures appropriately (function, class, module, session)
- Keep fixtures focused and reusable

### 5. Mocking

- Mock external dependencies
- Use `respx` for HTTP mocking
- Use `pytest-mock` for general mocking

### 6. Async Tests

- Mark async tests with `@pytest.mark.asyncio`
- Use `async def` for test functions
- Use async fixtures for async setup

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Every push to `main`, `feature/**`, `develop`
- Every pull request to `main` or `develop`
- Manual workflow dispatch

### Workflow Features

See `.github/workflows/test.yml` for the CI/CD test automation configuration.

The workflow runs:
- **Unit tests** on Python 3.12 with parallel execution
- **Coverage reporting** with Codecov integration
- **Test report artifacts** (HTML reports, coverage reports, logs)
- **Integration tests** (currently disabled until test infrastructure is ready)

### Workflow Artifacts

After each test run, the following artifacts are available:
- `test-report`: HTML test report with detailed results
- `coverage-report`: HTML coverage report and XML coverage data
- All artifacts are retained for 30 days

## Pre-commit Hooks

**Phase 2 Sprint 2.2**: TASK-037 (Pre-commit Hooks)

Pre-commit hooks automatically check code quality before each commit, catching issues early and ensuring consistent code standards.

### Setup

Install pre-commit hooks once per repository clone:

```bash
# Install pre-commit package (already in requirements-dev.txt)
pip install pre-commit

# Install git hooks
pre-commit install

# Verify installation
pre-commit --version
```

### Configured Hooks

The `.pre-commit-config.yaml` file configures the following hooks:

#### 1. Ruff Linter (auto-fix)
- **Purpose**: Catches code style issues, unused imports, and common bugs
- **Auto-fixes**: Yes (when possible)
- **Speed**: Fast (< 1s for most files)

#### 2. Ruff Formatter
- **Purpose**: Formats Python code consistently (replaces Black)
- **Auto-fixes**: Yes
- **Speed**: Fast (< 1s for most files)

#### 3. Mypy Type Checker
- **Purpose**: Validates type hints and catches type errors
- **Auto-fixes**: No (manual fixes required)
- **Scope**: Excludes tests/ and scripts/ directories
- **Speed**: Moderate (2-5s)

#### 4. FQDN Policy Enforcer
- **Purpose**: Ensures no localhost/127.0.0.1 in configuration files
- **Auto-fixes**: No (manual fixes required)
- **Scope**: All files
- **Speed**: Fast (< 1s)

#### 5. Fast Unit Tests (on push only)
- **Purpose**: Runs fast unit tests before pushing
- **Auto-fixes**: No (fix failing tests manually)
- **Scope**: Unit tests marked with `@pytest.mark.fast`
- **Speed**: Fast (1-3s)

### Usage

Hooks run automatically on `git commit` and `git push`:

```bash
# Normal commit - hooks run automatically
git add myfile.py
git commit -m "feat: add new feature"

# Hooks will run and may:
# - Auto-fix formatting/linting issues
# - Fail if type errors or test failures are found
# - Block commit until issues are resolved
```

### Manual Execution

Run hooks manually without committing:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run mypy --all-files

# Run hooks on staged files only
pre-commit run

# Run hooks on specific files
pre-commit run --files myfile.py
```

### Skipping Hooks

In rare cases, you may need to skip hooks (not recommended):

```bash
# Skip all hooks for one commit
git commit --no-verify -m "emergency fix"

# Skip specific hook (set SKIP environment variable)
SKIP=mypy git commit -m "commit without type checking"
```

### Troubleshooting

#### Hook Installation Failed

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Clear cache and reinstall
pre-commit clean
pre-commit install --install-hooks
```

#### Hooks Running Slowly

```bash
# Update hooks to latest versions
pre-commit autoupdate

# Skip slow hooks during development
SKIP=mypy,pytest-fast git commit -m "wip"
```

#### Type Checking Errors

```bash
# Run mypy manually to see full output
mypy --ignore-missing-imports --show-error-codes myfile.py

# Fix type errors or add type: ignore comments
result: Any = some_function()  # type: ignore[misc]
```

### Best Practices

1. **Run hooks before committing**: Use `pre-commit run --all-files` to catch issues early
2. **Don't skip hooks**: They exist to maintain code quality
3. **Fix issues, don't bypass**: Address the root cause rather than skipping hooks
4. **Update regularly**: Run `pre-commit autoupdate` monthly to get latest versions

---


---

## Troubleshooting

### Tests Fail to Discover

```bash
# Check pytest can find tests
pytest --collect-only

# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Import Errors

```bash
# Install in development mode
pip install -e .

# Or add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Slow Tests

```bash
# Show slowest tests
pytest --durations=10

# Skip slow tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

### Coverage Issues

```bash
# Debug coverage
pytest --cov=tests --cov-report=term-missing -v

# Generate detailed HTML report
pytest --cov=tests --cov-report=html
```

---

## Resources

- **Pytest Documentation**: [https://docs.pytest.org/](https://docs.pytest.org/)
- **pytest-asyncio**: [https://pytest-asyncio.readthedocs.io/](https://pytest-asyncio.readthedocs.io/)
- **pytest-cov**: [https://pytest-cov.readthedocs.io/](https://pytest-cov.readthedocs.io/)
- **respx**: [https://lundberg.github.io/respx/](https://lundberg.github.io/respx/)
- **Locust**: [https://docs.locust.io/](https://docs.locust.io/)

---

## Contributing

When adding new tests:

1. Follow the existing structure
2. Use appropriate markers
3. Add docstrings
4. Update this README if adding new categories
5. Ensure all tests pass before committing

---

**Test Suite Status**: ✅ **FRAMEWORK READY**
**Coverage Target**: 80%+
**Integration**: CI/CD via GitHub Actions

🧪 **Keep tests fast, focused, and reliable!**
