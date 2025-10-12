# Test Suite - Issues & Action Items Backlog

**Created**: October 12, 2025  
**Source**: tests_assessment.md comprehensive review  
**Assessment Rating**: 7.5/10 (Strong framework, partial implementation)  
**Status**: Backlog for test suite improvements  
**Priority Matrix**: 🔴 Critical | 🟡 High | 🟠 Medium | 🔵 Low

---

## Executive Summary

**Current State**:
- ✅ Excellent pytest framework (9/10)
- ✅ Comprehensive unit tests (53+ tests, 5,665 LOC)
- ⚠️ No CI/CD automation (0/10)
- ⚠️ Load tests planned but not implemented (3/10)
- ⚠️ Integration tests limited (5/10)

**Goal**: Achieve 9/10 overall test maturity with full CI/CD integration

---

## Critical Issues 🔴

### 1. Missing CI/CD Test Workflow ❌

**Issue**: No automated test execution in GitHub Actions

**Impact**: Critical  
**Effort**: Low (2 hours)  
**Priority**: 🔴 Critical

**Details**:
- Tests exist but don't run automatically
- No CI/CD integration blocks automation pipeline
- Pull requests don't have automated test validation
- Regression risks not caught before merge

**Recommended Solution**:

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [ main, feature/**, develop ]
    paths:
      - 'tests/**'
      - 'roles/**/*.py.j2'
      - 'pytest.ini'
      - 'requirements-dev.txt'
  pull_request:
    branches: [ main, develop ]

jobs:
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
          cache-dependency-path: 'requirements-dev.txt'
          
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
          
      - name: Run unit tests with coverage
        run: |
          pytest tests/unit/ -v \
            --cov=tests \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term-missing \
            -n auto \
            --durations=10
            
      - name: Upload coverage to Codecov
        if: false  # Enable when Codecov configured
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-report
          path: reports/
          retention-days: 30
          
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    if: false  # Enable when services accessible in CI
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v -m integration
```

**Acceptance Criteria**:
- [ ] Workflow file created
- [ ] Tests run on push to main/feature branches
- [ ] Tests run on pull requests
- [ ] Coverage report generated
- [ ] Test artifacts uploaded
- [ ] Workflow passes with current tests

**Estimated Time**: 2 hours  
**Assigned**: Unassigned  
**Target**: **Next Sprint (IMMEDIATE)**  
**Blocked**: No

---

### 2. Missing Dependencies in requirements-dev.txt 📦

**Issue**: Several testing packages used in code but not declared in requirements

**Impact**: High (tests may fail in clean environments)  
**Effort**: Very Low (15 minutes)  
**Priority**: 🔴 Critical

**Missing Packages**:

```python
# Load Testing
locust>=2.20.0

# HTTP Testing (for integration tests)
httpx>=0.27.0
respx>=0.21.0

# pytest Plugins (already used in pytest.ini)
pytest-html>=4.1.0
pytest-timeout>=2.2.0

# Optional but recommended
pytest-sugar>=1.0.0  # Better output formatting
```

**Current Issues**:
- `pytest.ini` references `--html` but `pytest-html` not in requirements
- Integration tests import `httpx` and `respx` but packages missing
- Load test plan references `locust` but not installed
- `pytest-timeout` configured but package not declared

**Recommended Solution**:

Add to `requirements-dev.txt`:

```txt
# === Testing Framework ===
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
pytest-xdist>=3.5.0
pytest-mock>=3.12.0
pytest-html>=4.1.0        # NEW
pytest-timeout>=2.2.0      # NEW
pytest-sugar>=1.0.0        # NEW (optional)

# === Load Testing ===
locust>=2.20.0             # NEW

# === HTTP Testing ===
httpx>=0.27.0              # NEW
respx>=0.21.0              # NEW

# === Code Quality ===
# (rest stays the same)
```

**Acceptance Criteria**:
- [ ] All packages added to requirements-dev.txt
- [ ] `pip install -r requirements-dev.txt` succeeds
- [ ] All tests run without import errors
- [ ] No missing module warnings

**Estimated Time**: 15 minutes  
**Assigned**: Unassigned  
**Target**: **Next Sprint (IMMEDIATE)**  
**Blocked**: No

---

### 3. Pytest Coverage Configuration Error 🐛

**Issue**: `pytest.ini` has incorrect coverage path

**Impact**: Medium  
**Effort**: Very Low (10 minutes)  
**Priority**: 🔴 Critical

**Current Configuration** (Line 120 in pytest.ini):
```ini
--cov=roles
```

**Problem**:
- `roles/` contains Ansible YAML/Jinja2, not Python modules
- Coverage tool cannot analyze non-Python files
- Inaccurate coverage reports

**Recommended Fix**:

Update `pytest.ini`:

```ini
# Change from:
--cov=roles

# To:
--cov=tests
# OR point to actual Python modules if they exist:
--cov=src
```

**If Python modules exist elsewhere**, use:
```ini
--cov=src --cov=lib --cov=tests
```

**Acceptance Criteria**:
- [ ] Coverage command runs without errors
- [ ] Coverage report shows accurate percentages
- [ ] HTML report generates correctly

**Estimated Time**: 10 minutes  
**Assigned**: Unassigned  
**Target**: **Next Sprint (IMMEDIATE)**  
**Blocked**: No

---

## High Priority Issues 🟡

### 4. Load Tests Not Implemented ⚡

**Issue**: Comprehensive plan exists in `load_test_plan.md` but no code implementation

**Impact**: High (production readiness validation)  
**Effort**: High (1-2 days)  
**Priority**: 🟠 High

**Planned Scenarios** (5 total):

1. **Normal Load Test** (100 users, 60s)
2. **Stress Test** (500 users, 300s)
3. **Spike Test** (0→1000 users rapid)
4. **Endurance Test** (100 users, 3600s)
5. **Concurrent Connections** (SSE testing)

**Files to Create**:

```
tests/load/
├── locustfiles/
│   ├── mcp_server.py
│   ├── orchestrator_api.py
│   ├── redis_streams.py
│   └── qdrant_operations.py
├── run_load_tests.sh
└── load_test_config.yaml
```

**Implementation Template** (from assessment):

```python
# tests/load/locustfiles/mcp_server.py
from locust import HttpUser, task, between
import json

class MCPServerUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        """Test /health endpoint"""
        self.client.get("/health")
    
    @task(1)
    def sse_endpoint(self):
        """Test SSE endpoint availability"""
        self.client.get("/sse")
```

**Acceptance Criteria**:
- [ ] All 5 scenarios implemented
- [ ] Load test runner script created
- [ ] Tests can run against dev environment
- [ ] Results documented
- [ ] Performance baselines established

**Estimated Time**: 1-2 days  
**Assigned**: Unassigned  
**Target**: This month  
**Blocked**: No (but requires `locust` package from Issue #2)

---

### 5. Integration Tests Incomplete 🔗

**Issue**: Only 2 integration test files, several tests skipped

**Impact**: Medium (limited E2E validation)  
**Effort**: High (2-3 days)  
**Priority**: 🟡 High

**Current State**:
- `test_mcp_server_health.py` - Basic health checks
- `test_mcp_tools.py` - Tool integration (many tests skipped)

**Missing Integration Tests** (documented but not coded):

From test documentation (`tests/docs/TEST-*.md`):

1. **TEST-004**: Web Crawling Operations
   - HTTP client integration
   - URL processing
   - Content extraction

2. **TEST-005**: Document Processing  
   - File format handling
   - Text extraction
   - Document conversion

3. **TEST-009**: Qdrant Operations
   - Collection management
   - Vector operations
   - Search functionality

4. **TEST-011**: LightRAG End-to-End
   - Full pipeline testing
   - RAG workflow validation
   - Multi-component integration

**Also Missing**:
- Orchestrator API integration tests
- Database operation tests
- Redis streams integration tests
- MCP tools full suite tests

**Recommended Approach**:

1. **Phase 1**: Implement TEST-009 (Qdrant) - most critical
2. **Phase 2**: Implement TEST-004 (Web Crawling)
3. **Phase 3**: Implement TEST-005 (Document Processing)
4. **Phase 4**: Implement TEST-011 (LightRAG E2E)

**Template** (from documented tests):

```python
# tests/integration/test_qdrant_operations.py
import pytest
from qdrant_client import QdrantClient

@pytest.fixture
def qdrant_client():
    """Qdrant client fixture"""
    return QdrantClient(url="http://hx-vectordb-server.dev-test.hana-x.ai:6333")

@pytest.mark.integration
@pytest.mark.qdrant
def test_create_collection(qdrant_client):
    """Test collection creation"""
    # Implementation from TEST-009.md
    pass
```

**Acceptance Criteria**:
- [ ] All 4 documented test scenarios implemented
- [ ] Tests can run when services available
- [ ] Tests properly marked with `@pytest.mark.integration`
- [ ] Clear skip messages when services unavailable
- [ ] Documentation matches implementation

**Estimated Time**: 2-3 days  
**Assigned**: Unassigned  
**Target**: This month  
**Blocked**: Partially (requires services running)

---

## Medium Priority Issues 🟠

### 6. Pre-commit Hooks for Tests 🪝

**Issue**: No pre-commit configuration to run tests before commits

**Impact**: Medium  
**Effort**: Low (30 minutes)  
**Priority**: 🟠 Medium

**Recommended Addition** to `.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: pytest-check
        name: Run pytest unit tests
        entry: pytest tests/unit/ -v --maxfail=3
        language: system
        pass_filenames: false
        stages: [commit]
```

**Note**: Only run fast unit tests in pre-commit (not slow integration/load tests)

**Estimated Time**: 30 minutes  
**Target**: Next sprint  
**Blocked**: No

---

### 7. Test Documentation Sync 📚

**Issue**: Test documentation (TEST-*.md) describes tests that don't exist in code

**Impact**: Medium (documentation drift)  
**Effort**: Low (1 hour)  
**Priority**: 🟠 Medium

**Gaps**:
- TEST-004-web-crawling.md documented, no test file
- TEST-005-document-processing.md documented, no test file
- TEST-009-qdrant-operations.md documented, no test file
- TEST-011-lightrag-e2e.md documented, no test file

**Options**:
1. **Implement the tests** (see Issue #5)
2. **Update docs** to reflect "planned" status
3. **Remove docs** for unimplemented tests (not recommended)

**Recommended**: Label docs as "Test Plan" until implemented

**Estimated Time**: 1 hour (documentation updates)  
**Target**: With Issue #5  
**Blocked**: No

---

### 8. Test Environment Automation 🐳

**Issue**: No automated test environment setup

**Impact**: Medium  
**Effort**: High (2-3 days)  
**Priority**: 🟠 Medium

**Current Process**:
- Manual service setup required
- Integration tests depend on live services
- No isolated test environment

**Recommended Solution**:

Create `tests/docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: test_password
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
```

**Acceptance Criteria**:
- [ ] Docker compose file created
- [ ] Services start/stop scripts
- [ ] Integration tests run against Docker services
- [ ] Teardown cleans up containers

**Estimated Time**: 2-3 days  
**Target**: Next month  
**Blocked**: No

---

### 9. Performance Benchmarking 📈

**Issue**: No baseline performance metrics or regression testing

**Impact**: Medium  
**Effort**: Medium (2 days)  
**Priority**: 🟠 Medium

**Recommended**:
- Establish baseline test execution times
- Add `pytest-benchmark` for performance tests
- Track metrics over time
- Alert on performance regressions

**Estimated Time**: 2 days  
**Target**: Q1 2026  
**Blocked**: No

---

## Low Priority Issues 🔵

### 10. Test Coverage Target 🎯

**Issue**: No defined coverage target percentage

**Impact**: Low  
**Effort**: Ongoing  
**Priority**: 🔵 Low

**Current Coverage**: Unknown (coverage config broken - Issue #3)

**Recommended Target**: 80%+ for critical modules

**Estimated Time**: Ongoing  
**Target**: Q1 2026  
**Blocked**: Issue #3 (coverage config)

---

## Completed Items ✅

1. ✅ **Pytest Framework Setup** - Excellent configuration
2. ✅ **Unit Test Implementation** - 53+ tests, comprehensive
3. ✅ **Fixture Architecture** - Well-designed hierarchy
4. ✅ **Test Markers** - 13 markers for organization
5. ✅ **Async Support** - Properly configured
6. ✅ **Parallel Execution** - `-n auto` working
7. ✅ **Test Documentation** - Good READMEs and plans

---

## Issue Summary

| Priority | Open | Blocked | Total |
|----------|------|---------|-------|
| 🔴 Critical | 3 | 0 | 3 |
| 🟡 High | 2 | 1 | 2 |
| 🟠 Medium | 4 | 0 | 4 |
| 🔵 Low | 1 | 0 | 1 |
| **Total** | **10** | **1** | **10** |

---

## Sprint Planning

### Sprint 1: Critical Fixes (1 week)

**Immediate Actions** (3-4 hours total):

1. 🔴 Create CI/CD test workflow (2 hours)
   - File: `.github/workflows/test.yml`
   - Enable automated testing

2. 🔴 Fix dependencies (15 minutes)
   - Add missing packages to `requirements-dev.txt`
   - Test installation

3. 🔴 Fix pytest coverage config (10 minutes)
   - Update `pytest.ini` coverage path
   - Verify coverage reports

4. 🟠 Add pre-commit hooks (30 minutes)
   - Configure test execution in `.pre-commit-config.yaml`

**Outcome**: Automated testing in CI/CD ✅

---

### Sprint 2: Integration & Load Tests (2 weeks)

**Phase 1: Load Tests** (1-2 days):

1. 🟡 Implement load test scenarios (Issue #4)
   - Create 5 locustfiles
   - Add load test runner script
   - Document performance baselines

**Phase 2: Integration Tests** (2-3 days):

2. 🟡 Implement TEST-009 (Qdrant operations)
3. 🟡 Implement TEST-004 (Web crawling)
4. 🟡 Implement TEST-005 (Document processing)
5. 🟡 Implement TEST-011 (LightRAG E2E)

**Outcome**: Full test coverage across all test types ✅

---

### Sprint 3: Infrastructure & Optimization (1 week)

**Environment** (2-3 days):

1. 🟠 Create Docker test environment (Issue #8)
   - Docker compose for services
   - Automated setup/teardown

**Monitoring** (2 days):

2. 🟠 Add performance benchmarking (Issue #9)
   - Baseline metrics
   - Regression detection

**Documentation** (1 hour):

3. 🟠 Sync test documentation (Issue #7)
   - Mark plans vs implementations
   - Update test docs

**Outcome**: Production-grade test infrastructure ✅

---

## Quick Reference

### Run Tests Locally

```bash
# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ -v --cov=tests --cov-report=html

# Fast tests only
pytest -m fast -v

# Specific test file
pytest tests/unit/test_common_types_response_models.py -v

# In parallel
pytest tests/unit/ -n auto
```

### Check Test Status

```bash
# Collect all tests
pytest --collect-only

# Show markers
pytest --markers

# Show fixtures
pytest --fixtures

# Dry run
pytest --collect-only -q
```

### Installation

```bash
# Install all test dependencies
pip install -r requirements-dev.txt

# Verify installation
pytest --version
locust --version  # After Issue #2 fixed
```

---

## Metrics & Goals

### Current Metrics
- **Test Files**: 20+ files
- **Test Lines**: 5,665+ LOC
- **Unit Tests**: 53+ tests
- **Integration Tests**: ~5 tests (many skipped)
- **Load Tests**: 0 (not implemented)
- **Execution Time**: ~4 seconds (unit tests only)
- **Coverage**: Unknown (config broken)

### Target Metrics (After Backlog Completion)
- **Test Files**: 35+ files (+15)
- **All Tests**: 100+ tests
- **Coverage**: 80%+ for critical modules
- **CI/CD**: 100% automated
- **Load Tests**: 5 scenarios implemented
- **Integration Tests**: 20+ tests
- **Execution Time**: <30 seconds (all tests)

---

## Dependencies

### Issue Dependencies

- Issue #4 (Load Tests) → **Requires** Issue #2 (locust package)
- Issue #5 (Integration) → **Requires** Issue #8 (test environment)
- Issue #10 (Coverage Target) → **Requires** Issue #3 (coverage config fix)

### External Dependencies

- Services must be running for integration tests
- Docker required for Issue #8
- GitHub Actions runner for Issue #1

---

## Notes

- All action items extracted from tests_assessment.md
- Assessment rating: 7.5/10 (can reach 9/10 after Sprint 1-2)
- Focus on CI/CD first (Issue #1) - enables everything else
- Load tests important for production readiness validation

---

**Backlog Owner**: QA/DevOps Team  
**Last Updated**: October 12, 2025  
**Review Frequency**: After each sprint or when test suite changes  
**Next Review**: After CI/CD workflow implementation

