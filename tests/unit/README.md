# Unit Tests - Common Types Module

This directory contains unit tests for the `common_types` module, organized following **SOLID principles** (specifically Single Responsibility Principle).

## Test Framework

**pytest** - Python testing framework with the following features:
- Test discovery via `test_*.py` naming convention
- Native Python `assert` statements
- Fixture-based setup/teardown
- Parametrized testing
- Test markers for categorization

## Test Structure

The test suite is organized into 7 modular files, each with a single responsibility:

### 1. `conftest.py` - Shared Configuration
- **Purpose**: pytest configuration and shared fixtures
- **Fixtures**: `roles_dir`, `project_root`, `temp_file`
- **Setup**: Adds `common_types` module to `sys.path` for imports

### 2. `test_common_types_enums.py` - Enumeration Tests (15 tests)
- **Purpose**: Test all enumeration types
- **Enums Tested**:
  - `JobStatusEnum` - Job status values (pending, processing, completed, failed, cancelled)
  - `HealthStatusEnum` - Health status values (healthy, degraded, unhealthy, unknown)
  - `CircuitBreakerStateEnum` - Circuit breaker states (closed, open, half_open)
  - `LightRAGModeEnum` - LightRAG modes (naive, local, global, hybrid)
  - `MCPResponseStatusEnum` - MCP response statuses (success, error, accepted)

### 3. `test_common_types_request_models.py` - Request Model Tests (18 tests)
- **Purpose**: Test Pydantic request validation models
- **Models Tested**:
  - `CrawlWebRequest` - URL validation, max_pages (1-100), max_depth (1-5)
  - `IngestDocRequest` - File path validation, document format validation
  - `QdrantFindRequest` - Query validation, top_k (1-100), collection name
  - `QdrantStoreRequest` - Points validation, collection name
  - `LightRAGQueryRequest` - Query validation, mode validation
  - `JobStatusRequest` - Job ID validation

### 4. `test_common_types_response_models.py` - Response Model Tests (5 tests)
- **Purpose**: Test Pydantic response models
- **Models Tested**:
  - `CrawlWebResponse` - HTTP 202 accepted, success, error responses
  - `IngestDocResponse` - Job status responses
  - `QdrantFindResponse` - Search results with scores
  - `LightRAGQueryResponse` - Query results with sources

### 5. `test_common_types_utility_functions.py` - Utility Function Tests (9 tests)
- **Purpose**: Test utility helper functions
- **Functions Tested**:
  - `create_error_response()` - Error response creation with optional fields
  - `create_job_status_response()` - Job status response creation, progress clamping (0-100)

### 6. `test_common_types_type_guards.py` - Type Guard Tests (3 tests)
- **Purpose**: Test runtime type checking functions
- **Functions Tested**:
  - `is_valid_job_status()` - Validates job status strings
  - `is_valid_health_status()` - Validates health status strings
  - `is_valid_lightrag_mode()` - Validates LightRAG mode strings

### 7. `test_common_types_constants.py` - Constants Tests (3 tests)
- **Purpose**: Test module constants and default values
- **Constants Tested**:
  - `SUPPORTED_DOCUMENT_FORMATS` - Document format list (.pdf, .docx, .txt, .md)
  - `DEFAULT_QDRANT_COLLECTION` - Default collection name
  - `DEFAULT_EMBEDDING_MODEL` - Default embedding model
  - `DEFAULT_MAX_PAGES` - Default max pages for crawling (10)
  - `DEFAULT_CIRCUIT_FAIL_MAX` - Default circuit breaker failure threshold (5)

### 8. `test_common_types_integration.py` - Integration Tests (2 tests)
- **Purpose**: Test cross-type integration scenarios
- **Scenarios Tested**:
  - Error responses in API responses (error response → crawl response)
  - Complete job status lifecycle (pending → processing → completed)
  - Request/response compatibility

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.unit` - Unit tests (isolated component testing)
- `@pytest.mark.fast` - Fast-running tests (< 1 second)

## Running Tests

### Run All Unit Tests
```bash
# From project root
python3 -m pytest tests/unit/ -v

# With detailed output
python3 -m pytest tests/unit/ -v --tb=short

# With coverage
python3 -m pytest tests/unit/ --cov=common_types --cov-report=term-missing
```

### Run Specific Test Files
```bash
# Enum tests only
python3 -m pytest tests/unit/test_common_types_enums.py -v

# Request model tests only
python3 -m pytest tests/unit/test_common_types_request_models.py -v

# Utility function tests only
python3 -m pytest tests/unit/test_common_types_utility_functions.py -v
```

### Run by Marker
```bash
# Run only unit tests
python3 -m pytest -m unit -v

# Run only fast tests
python3 -m pytest -m fast -v
```

### Run Specific Test Classes or Methods
```bash
# Run specific test class
python3 -m pytest tests/unit/test_common_types_enums.py::TestJobStatusEnum -v

# Run specific test method
python3 -m pytest tests/unit/test_common_types_enums.py::TestJobStatusEnum::test_all_values_present -v
```

## Test Coverage

**Current Coverage**: 53 tests covering `common_types` module

| Category | Tests | Coverage |
|----------|-------|----------|
| Enumerations | 15 | 100% (5 enums) |
| Request Models | 18 | 100% (6 models) |
| Response Models | 5 | 100% (4 models) |
| Utility Functions | 9 | 100% (2 functions) |
| Type Guards | 3 | 100% (3 functions) |
| Constants | 3 | 100% (5 constants) |
| Integration | 2 | Key scenarios |
| **Total** | **53** | **~95%** |

## Test Execution Performance

- **Execution Time**: ~0.40 seconds (all 53 tests)
- **Test Isolation**: Each test is independent and can run in any order
- **Fixture Scope**: Session-scoped for expensive setup, function-scoped for test isolation

## Design Principles

### SOLID Compliance
- **Single Responsibility**: Each test file tests one aspect of the module
- **Open/Closed**: Easy to extend with new test files without modifying existing ones
- **Interface Segregation**: Focused test classes test specific interfaces
- **Dependency Inversion**: Tests depend on abstractions (fixtures) not concrete implementations

### Test Organization
- **AAA Pattern**: Arrange, Act, Assert in each test method
- **Descriptive Names**: Test method names describe what is being tested
- **Class Grouping**: Related tests grouped into classes
- **Minimal Duplication**: Shared setup in fixtures and conftest.py

## Adding New Tests

### Adding Tests to Existing Files
```python
@pytest.mark.unit
@pytest.mark.fast
class TestNewFeature:
    """Test new feature description"""

    def test_specific_behavior(self):
        """Test that specific behavior works correctly"""
        # Arrange
        input_data = "test"

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_value
```

### Adding New Test Files
1. Create file: `test_common_types_<category>.py`
2. Add docstring describing single responsibility
3. Import from `common_types` module
4. Add pytest markers: `@pytest.mark.unit`, `@pytest.mark.fast`
5. Organize tests into classes with `Test*` prefix
6. Use fixtures from `conftest.py` if needed

## Deployment Testing

Tests are deployed to `hx-mcp1-server` for validation:

```bash
# Package tests
tar czf /tmp/modular_tests.tar.gz -C tests/unit \
  conftest.py \
  test_common_types_*.py

# Deploy to hx-mcp1-server
ansible hx-mcp1-server -i inventory/prod.ini -m ansible.builtin.copy \
  -a "src=/tmp/modular_tests.tar.gz dest=/tmp/modular_tests.tar.gz"

# Extract and run tests
ansible hx-mcp1-server -i inventory/prod.ini -m ansible.builtin.shell \
  -a "cd /tmp && tar xzf modular_tests.tar.gz && python3 -m pytest test_common_types_*.py -v"
```

## Related Documentation

- `docs/Delivery-Enhancements/TASK-TRACKER.md` - TASK-032 progress tracking
- `docs/Delivery-Enhancements/COMPREHENSIVE-IMPLEMENTATION-ROADMAP.md` - Sprint 2.2 plan
- `roles/fastmcp_server/templates/common_types.py.j2` - Module under test

## History

- **October 11, 2025**: Initial monolithic test file created (710 lines, 53 tests)
- **October 11, 2025**: Refactored to modular SOLID-compliant structure (7 files + conftest.py)
- **Commits**:
  - `f8f8f41` - Refactored to modular structure
  - `e7dc0a2` - Removed old monolithic file

## Contact

**Task**: TASK-032 - Write Unit Tests (Sprint 2.2: Automated Testing & CI/CD)
**Phase**: Phase 2 - Quality Improvements
**Status**: 40% Complete (common_types module done, MCP tools remaining)
