# Type Checking Guide
## HX-Citadel Shield - Mypy Configuration

**Phase 2 - Sprint 2.1**: Type Hints Migration
**Task**: TASK-022 - Setup Mypy
**Date**: October 11, 2025
**Status**: ✅ Complete

---

## Overview

This project uses **Mypy** for static type checking to ensure code quality and catch type-related bugs before deployment.

**Target**: 95%+ type hint coverage across all Python code

---

## Quick Start

### 1. Install Development Dependencies

```bash
# Install mypy and type stubs
pip install -r requirements-dev.txt
```

### 2. Run Type Checking

Since this is an Ansible project that generates Python code via Jinja2 templates, type checking is done on deployed code:

```bash
# Option A: Check rendered Python files on a deployment server
ssh hx-mcp1-server "cd /opt/hx-citadel-shield && mypy ."
ssh hx-orchestrator-server "cd /opt/hx-citadel-shield && mypy ."

# Option B: Use the type-check script (renders templates locally)
./scripts/type-check.sh

# Option C: Check specific modules
mypy roles/fastmcp_server/templates/shield_mcp_server.py.j2  # Requires rendered version
```

---

## Configuration

### mypy.ini Structure

The `mypy.ini` file at the project root contains:

1. **Strict Mode Configuration**
   - `warn_return_any = True`
   - `warn_redundant_casts = True`
   - `strict_equality = True`
   - `disallow_any_generics = True`

2. **Gradual Typing**
   - `disallow_untyped_defs = False` (initially)
   - Will be set to `True` after all type hints are added

3. **Module Ignores**
   - Third-party libraries without type stubs: `fastmcp`, `crawl4ai`, `docling`, `pybreaker`, `lightrag`
   - Well-typed libraries: `pydantic`, `fastapi`, `httpx` (strict mode enabled)

4. **Exclusions**
   - `tech_kb/` - Reference material, not production code
   - `.git/`, `.venv/`, `build/`, `dist/` - Standard exclusions

---

## Type Checking Strategy

### Phase 2 Sprint 2.1 Tasks

| Task | Module | Type Hints Target | Mypy Strict |
|------|--------|-------------------|-------------|
| TASK-023 | `common_types` | 100% | ✅ Yes |
| TASK-024 | MCP Server | 95%+ | ⏳ After completion |
| TASK-025 | Orchestrator Main | 95%+ | ⏳ After completion |
| TASK-026 | Orchestrator Core | 95%+ | ⏳ After completion |
| TASK-027 | Agents | 95%+ | ⏳ After completion |
| TASK-028 | API Endpoints | 95%+ | ⏳ After completion |

### Progressive Strictness

1. **Phase 1** (Current): Lenient configuration
   - `disallow_untyped_defs = False`
   - Warnings only for most issues

2. **Phase 2** (After TASK-024 through TASK-028): Enable strict mode
   - `disallow_untyped_defs = True`
   - All functions must have type hints

3. **Phase 3** (Production): Full strict mode
   - `strict = True` (global)
   - Zero tolerance for type violations

---

## Type Stubs Required

The following type stub packages are installed via `requirements-dev.txt`:

```python
# Well-typed libraries (no stubs needed)
pydantic>=2.0.0          # Excellent typing
fastapi>=0.115.0         # Excellent typing
httpx>=0.25.0            # Excellent typing

# Libraries with type stubs
types-redis>=4.6.0
types-requests>=2.31.0
types-python-dateutil>=2.8.19
sqlalchemy[mypy]>=2.0.0  # Includes mypy plugin

# Libraries without stubs (ignore_missing_imports = True)
fastmcp                  # No official stubs
crawl4ai                 # No official stubs
docling                  # No official stubs
pybreaker                # No official stubs
lightrag                 # Custom AI library
```

---

## Common Type Hints Patterns

### 1. Function Signatures

```python
from typing import Optional, List, Dict, Any

async def crawl_web(
    url: str,
    max_pages: int = 10,
    allowed_domains: Optional[List[str]] = None,
    max_depth: int = 2
) -> Dict[str, Any]:
    """Type hints for async functions"""
    pass
```

### 2. Pydantic Models (Recommended)

```python
from pydantic import BaseModel, Field

class CrawlRequest(BaseModel):
    url: str = Field(..., description="Starting URL")
    max_pages: int = Field(10, gt=0, le=100)
    allowed_domains: Optional[List[str]] = None
    max_depth: int = Field(2, ge=1, le=5)
```

### 3. Type Aliases (common_types module)

```python
from typing import TypeAlias, Dict, Any

# Job status response
JobStatus: TypeAlias = Dict[str, Any]

# MCP tool response
MCPResponse: TypeAlias = Dict[str, Any]

# Health check status
HealthStatus: TypeAlias = Dict[str, str]
```

### 4. Generic Types

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class JobTracker(Generic[T]):
    def get_job(self, job_id: str) -> T:
        ...
```

---

## Running Mypy

### Basic Usage

```bash
# Check all Python files in current directory
mypy .

# Check specific file
mypy shield_mcp_server.py

# Check with verbose output
mypy --verbose .

# Generate HTML report
mypy --html-report ./mypy-report .
```

### CI/CD Integration (TASK-030)

Mypy will be added to the GitHub Actions workflow:

```yaml
- name: Type Check with Mypy
  run: |
    pip install -r requirements-dev.txt
    mypy --config-file mypy.ini .
```

---

## Troubleshooting

### Issue: "Cannot find module X"

**Solution**: Add to `mypy.ini`:

```ini
[mypy-X.*]
ignore_missing_imports = True
```

### Issue: "Incompatible types in assignment"

**Solution**: Check variable types, use `cast()` if needed:

```python
from typing import cast

value: str = cast(str, some_dict.get("key"))
```

### Issue: "Need type annotation for variable"

**Solution**: Add explicit type annotation:

```python
# Bad
results = []

# Good
results: List[Dict[str, Any]] = []
```

### Issue: "Function is missing a return type annotation"

**Solution**: Add return type hint:

```python
# Bad
async def get_job_status(job_id):
    ...

# Good
async def get_job_status(job_id: str) -> Dict[str, Any]:
    ...
```

---

## Best Practices

### 1. Use Pydantic Models for Complex Types

```python
# Instead of Dict[str, Any]
class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
```

### 2. Avoid `Any` When Possible

```python
# Bad
def process_data(data: Any) -> Any:
    ...

# Good
def process_data(data: Dict[str, str]) -> List[str]:
    ...
```

### 3. Use Type Aliases for Readability

```python
# Bad
def get_job(job_id: str) -> Dict[str, Union[str, int, None, List[str]]]:
    ...

# Good
from common_types import JobStatus

def get_job(job_id: str) -> JobStatus:
    ...
```

### 4. Document Complex Types

```python
from typing import TypedDict

class CrawlResult(TypedDict):
    """Type-safe dictionary for crawl results"""
    url: str
    content: str
    links: List[str]
    metadata: Dict[str, Any]
```

---

## Progress Tracking

### Coverage Metrics (Target: 95%)

| Module | Functions | Typed | Coverage | Status |
|--------|-----------|-------|----------|--------|
| MCP Server | ~15 | 0 | 0% | ⏸️ TASK-024 |
| Orchestrator Main | ~20 | 0 | 0% | ⏸️ TASK-025 |
| Orchestrator Core | ~25 | 0 | 0% | ⏸️ TASK-026 |
| Agents | ~10 | 0 | 0% | ⏸️ TASK-027 |
| API Endpoints | ~15 | 0 | 0% | ⏸️ TASK-028 |
| **TOTAL** | **~85** | **0** | **0%** | **In Progress** |

---

## References

- **Mypy Documentation**: https://mypy.readthedocs.io/
- **Pydantic Type Hints**: https://docs.pydantic.dev/latest/concepts/types/
- **Python Typing Module**: https://docs.python.org/3/library/typing.html
- **SQLAlchemy Mypy Plugin**: https://docs.sqlalchemy.org/en/20/orm/extensions/mypy.html

---

**Last Updated**: October 11, 2025
**Status**: ✅ TASK-022 Complete
**Next**: TASK-023 - Create Common Types Module
