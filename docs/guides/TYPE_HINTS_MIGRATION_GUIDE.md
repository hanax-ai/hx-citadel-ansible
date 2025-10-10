# Type Hints Migration Guide
## Adding Static Type Checking to Python Codebase

**Version**: 1.0  
**Date**: October 10, 2025  
**Status**: Implementation Guide  
**Related**: CODEBASE-ENHANCEMENT-RECOMMENDATIONS.md

---

## 📋 OVERVIEW

### What are Type Hints?

Type hints are Python annotations that specify the expected types of variables, function parameters, and return values. Introduced in Python 3.5 (PEP 484), they provide:

- **Static type checking** (via mypy, pyright)
- **IDE autocomplete** and IntelliSense
- **Self-documenting** code
- **Early error detection**
- **Better refactoring** support

### Current State vs. Target

**Current** (75% coverage):
```python
async def search(query, limit=10):
    result = await qdrant.search(query, limit)
    return result
```

**Target** (95%+ coverage):
```python
async def search(
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search vectors in Qdrant.
    
    Args:
        query: Search query text
        limit: Maximum results to return
        
    Returns:
        Dictionary containing search results
    """
    result = await qdrant.search(query, limit)
    return result
```

---

## 🎯 BENEFITS

### 1. Catch Errors Early

**Without Type Hints**:
```python
def process_user(user):
    return user.name.upper()

# Runtime error (user is None)
process_user(None)  # ❌ AttributeError: 'NoneType' object has no attribute 'name'
```

**With Type Hints**:
```python
def process_user(user: Optional[User]) -> str:
    if user is None:
        return "Unknown"
    return user.name.upper()

# mypy catches error before running
process_user(None)  # ✅ Works correctly
```

### 2. Better IDE Support

**Without Type Hints**:
```python
result = search("test")
result.  # ❌ No autocomplete - IDE doesn't know type
```

**With Type Hints**:
```python
result: Dict[str, Any] = search("test")
result.  # ✅ Autocomplete shows: keys(), values(), items(), get(), ...
```

### 3. Self-Documenting

**Without Type Hints**:
```python
def create_job(data, priority, callback):
    # What type is data? Dict? Object? String?
    # Is priority an int? String?
    # What should callback accept? Return?
    pass
```

**With Type Hints**:
```python
def create_job(
    data: Dict[str, Any],
    priority: int,
    callback: Callable[[str], None]
) -> str:
    # Clear! data is a dict, priority is int, callback takes str returns None
    pass
```

---

## 🛠️ IMPLEMENTATION PLAN

### Phase 1: Setup (1 hour)

#### Install Type Checking Tools

```bash
# Add to requirements.txt
mypy==1.7.0
types-redis==4.6.0
types-requests==2.31.0

# Install
pip install mypy types-redis types-requests
```

#### Create mypy Configuration

```ini
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Start permissive
check_untyped_defs = True

# Gradually enable stricter checks
# disallow_untyped_defs = True
# disallow_incomplete_defs = True
# disallow_untyped_calls = True

# Ignore missing imports for third-party libraries
[mypy-crawl4ai.*]
ignore_missing_imports = True

[mypy-docling.*]
ignore_missing_imports = True

[mypy-qdrant_client.*]
ignore_missing_imports = True

[mypy-fastmcp.*]
ignore_missing_imports = True
```

#### Add Pre-Commit Hook (Optional)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-redis, types-requests]
        args: [--config-file=mypy.ini]
```

### Phase 2: Common Types Import (30 minutes)

Create a types module for commonly used types:

```python
# roles/common/files/types.py
"""Common type definitions for Shield MCP."""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Callable,
    Tuple,
    TypeVar,
    Protocol,
    Literal
)
from datetime import datetime

# Common type aliases
JSON = Dict[str, Any]
Headers = Dict[str, str]
QueryParams = Dict[str, Union[str, int, bool]]

# Job status types
JobStatus = Literal["queued", "processing", "completed", "failed"]

# Result types
class SearchResult(TypedDict):
    """Type for search results."""
    query: str
    results: List[Dict[str, Any]]
    total: int
    took_ms: float

class JobInfo(TypedDict):
    """Type for job information."""
    job_id: str
    status: JobStatus
    progress: int
    created_at: str
    result: Optional[Dict[str, Any]]

# Generic type variables
T = TypeVar('T')
ResponseT = TypeVar('ResponseT', bound=Dict[str, Any])
```

### Phase 3: Function Signatures (1-2 days)

#### Priority Files

1. **MCP Server** (`shield_mcp_server.py.j2`)
2. **Orchestrator Main** (`main.py.j2`)
3. **API Endpoints** (FastAPI routes)
4. **Core Services** (LightRAG, workers, event bus)
5. **Agents** (Coordinator agents)

#### Migration Pattern

**Before**:
```python
async def crawl_web(url, max_pages=10):
    result = await crawl(url, max_pages)
    return result
```

**After**:
```python
from typing import Dict, Any

async def crawl_web(
    url: str,
    max_pages: int = 10
) -> Dict[str, Any]:
    """
    Crawl a website.
    
    Args:
        url: Starting URL
        max_pages: Maximum pages to crawl
        
    Returns:
        Crawl results with job_id
    """
    result: Dict[str, Any] = await crawl(url, max_pages)
    return result
```

### Phase 4: Class Annotations (1 day)

```python
# Before
class Worker:
    def __init__(self, redis_client, queue_name):
        self.redis = redis_client
        self.queue = queue_name
        self.running = False

# After
from redis.asyncio import Redis

class Worker:
    """Async worker for processing jobs."""
    
    redis: Redis
    queue: str
    running: bool
    
    def __init__(
        self,
        redis_client: Redis,
        queue_name: str
    ) -> None:
        self.redis = redis_client
        self.queue = queue_name
        self.running = False
```

### Phase 5: Complex Types (1 day)

#### Generic Types

```python
from typing import TypeVar, Generic, List

T = TypeVar('T')

class JobQueue(Generic[T]):
    """Generic job queue."""
    
    def __init__(self) -> None:
        self._items: List[T] = []
    
    def enqueue(self, item: T) -> None:
        self._items.append(item)
    
    def dequeue(self) -> Optional[T]:
        return self._items.pop(0) if self._items else None
```

#### Protocols (Duck Typing)

```python
from typing import Protocol

class Searchable(Protocol):
    """Protocol for searchable objects."""
    
    async def search(
        self,
        query: str,
        limit: int
    ) -> Dict[str, Any]: ...

# Any class with matching search() method satisfies protocol
def perform_search(
    engine: Searchable,
    query: str
) -> Dict[str, Any]:
    return await engine.search(query, 10)
```

#### Callback Types

```python
from typing import Callable, Awaitable

EventCallback = Callable[[str, Dict[str, Any]], Awaitable[None]]

class EventBus:
    """Event bus with typed callbacks."""
    
    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventCallback]] = {}
    
    def subscribe(
        self,
        event: str,
        callback: EventCallback
    ) -> None:
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(callback)
    
    async def publish(
        self,
        event: str,
        data: Dict[str, Any]
    ) -> None:
        for callback in self._handlers.get(event, []):
            await callback(event, data)
```

---

## 📝 TYPE HINTS REFERENCE

### Basic Types

```python
# Primitives
name: str = "John"
age: int = 30
height: float = 5.9
is_active: bool = True

# Collections
items: list = [1, 2, 3]
items: List[int] = [1, 2, 3]  # Preferred - specifies element type
names: List[str] = ["Alice", "Bob"]
scores: Dict[str, int] = {"Alice": 95, "Bob": 87}
coords: Tuple[float, float] = (1.0, 2.0)
unique_ids: Set[str] = {"id1", "id2"}
```

### Optional Types

```python
from typing import Optional, Union

# Optional[T] is shorthand for Union[T, None]
def find_user(user_id: str) -> Optional[User]:
    """Returns User or None if not found."""
    return db.query(User).filter_by(id=user_id).first()

# Union for multiple types
def parse_value(value: Union[str, int, float]) -> float:
    """Accept string, int, or float, return float."""
    return float(value)
```

### Function Types

```python
from typing import Callable

# Simple function
def apply(
    value: int,
    func: Callable[[int], int]
) -> int:
    return func(value)

# Async function
async def map_async(
    items: List[str],
    func: Callable[[str], Awaitable[int]]
) -> List[int]:
    return [await func(item) for item in items]
```

### Generic Types

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []
    
    def add(self, item: T) -> None:
        self._items.append(item)
    
    def get(self, index: int) -> T:
        return self._items[index]

# Usage
numbers: Container[int] = Container()
numbers.add(42)

strings: Container[str] = Container()
strings.add("hello")
```

### TypedDict

```python
from typing import TypedDict

class JobConfig(TypedDict):
    """Configuration for a job."""
    job_id: str
    priority: int
    max_retries: int
    timeout: float

# Usage
config: JobConfig = {
    "job_id": "abc123",
    "priority": 1,
    "max_retries": 3,
    "timeout": 30.0
}

# mypy checks keys and types
config["invalid_key"] = "value"  # ❌ Error: invalid key
config["priority"] = "high"       # ❌ Error: wrong type
```

### Literal Types

```python
from typing import Literal

JobStatus = Literal["queued", "processing", "completed", "failed"]

def update_job_status(
    job_id: str,
    status: JobStatus
) -> None:
    """Update job status with only valid values."""
    redis.hset(f"job:{job_id}", "status", status)

# Usage
update_job_status("job1", "completed")  # ✅ OK
update_job_status("job1", "running")    # ❌ Error: not a valid literal
```

### Async Types

```python
from typing import Awaitable, AsyncIterator

async def fetch_data(url: str) -> Dict[str, Any]:
    """Return type is coroutine -> Dict."""
    response = await http_client.get(url)
    return response.json()

async def stream_events() -> AsyncIterator[Dict[str, Any]]:
    """Async generator."""
    while True:
        event = await get_next_event()
        yield event

# Function that takes async callable
async def retry_async(
    func: Callable[[], Awaitable[T]],
    max_attempts: int = 3
) -> T:
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception:
            if attempt == max_attempts - 1:
                raise
```

---

## 🎯 FILE-BY-FILE MIGRATION

### File 1: MCP Server

**File**: `roles/fastmcp_server/templates/shield_mcp_server.py.j2`

```python
from typing import Dict, Any, List, Optional
import httpx
from fastmcp import FastMCP

mcp = FastMCP("Shield MCP")

@mcp.tool()
async def crawl_web(
    url: str,
    allow_domains: Optional[List[str]] = None,
    max_pages: int = 10
) -> Dict[str, Any]:
    """
    Crawl a website asynchronously.
    
    Args:
        url: Starting URL to crawl
        allow_domains: Allowed domains (None = same domain only)
        max_pages: Maximum pages to crawl
        
    Returns:
        Job information with job_id for tracking
    """
    try:
        response: httpx.Response = await call_orchestrator_api(
            "/ingest-async",
            {
                "source_type": "web_crawl",
                "source_uri": url,
                "metadata": {
                    "allow_domains": allow_domains or [],
                    "max_pages": max_pages
                }
            }
        )
        
        result: Dict[str, Any] = response.json()
        
        return {
            "status": "queued",
            "job_id": result["job_id"],
            "message": f"Crawling {url} queued",
            "track_url": f"/jobs/{result['job_id']}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def call_orchestrator_api(
    endpoint: str,
    data: Dict[str, Any]
) -> httpx.Response:
    """
    Call orchestrator API endpoint.
    
    Args:
        endpoint: API endpoint path
        data: Request payload
        
    Returns:
        HTTP response
        
    Raises:
        httpx.HTTPError: On request failure
    """
    url: str = f"{ORCHESTRATOR_URL}{endpoint}"
    response: httpx.Response = await http_client.post(url, json=data)
    response.raise_for_status()
    return response
```

### File 2: Orchestrator Main

**File**: `roles/orchestrator_fastapi/templates/main.py.j2`

```python
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid

app: FastAPI = FastAPI(title="Shield Orchestrator")

class IngestRequest(BaseModel):
    """Request model for ingestion."""
    source_type: str
    source_uri: str
    metadata: Optional[Dict[str, Any]] = None

class JobResponse(BaseModel):
    """Response model for job creation."""
    job_id: str
    status: str
    message: str

@app.post("/ingest-async", response_model=JobResponse)
async def ingest_async(
    request: IngestRequest,
    background_tasks: BackgroundTasks
) -> JobResponse:
    """
    Queue an ingestion job.
    
    Args:
        request: Ingestion request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Job information with job_id
    """
    job_id: str = str(uuid.uuid4())
    
    # Queue job
    await redis.xadd(
        "ingest_jobs",
        {
            "job_id": job_id,
            "source_type": request.source_type,
            "source_uri": request.source_uri,
            "metadata": json.dumps(request.metadata or {})
        }
    )
    
    return JobResponse(
        job_id=job_id,
        status="queued",
        message="Job queued for processing"
    )
```

### File 3: Worker Pool

**File**: `roles/orchestrator_workers/templates/workers/worker_pool.py.j2`

```python
from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio
from redis.asyncio import Redis

JobHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

class Worker:
    """Async worker for processing jobs."""
    
    def __init__(
        self,
        redis_client: Redis,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        handler: JobHandler
    ) -> None:
        self.redis: Redis = redis_client
        self.stream: str = stream_name
        self.group: str = consumer_group
        self.consumer: str = consumer_name
        self.handler: JobHandler = handler
        self.running: bool = False
    
    async def start(self) -> None:
        """Start processing jobs."""
        self.running = True
        
        while self.running:
            try:
                messages: List[Tuple[bytes, List[Tuple[bytes, Dict[bytes, bytes]]]]] = \
                    await self.redis.xreadgroup(
                        self.group,
                        self.consumer,
                        {self.stream: ">"},
                        count=1,
                        block=5000
                    )
                
                for stream, message_list in messages:
                    for message_id, job_data in message_list:
                        await self._process_message(message_id, job_data)
                        
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
    
    async def _process_message(
        self,
        message_id: bytes,
        job_data: Dict[bytes, bytes]
    ) -> None:
        """Process a single message."""
        try:
            # Decode job data
            decoded_data: Dict[str, Any] = {
                k.decode(): v.decode()
                for k, v in job_data.items()
            }
            
            # Process job
            result: Dict[str, Any] = await self.handler(decoded_data)
            
            # ACK message
            await self.redis.xack(self.stream, self.group, message_id)
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
```

---

## 🧪 TESTING TYPE HINTS

### Run mypy

```bash
# Check all files
mypy roles/ --config-file=mypy.ini

# Check specific file
mypy roles/fastmcp_server/templates/shield_mcp_server.py.j2

# Generate HTML report
mypy roles/ --html-report mypy-report/
```

### Common mypy Errors

#### Error: Missing type annotation

```python
# ❌ Error
def process(data):
    return data["key"]

# ✅ Fix
def process(data: Dict[str, Any]) -> Any:
    return data["key"]
```

#### Error: Incompatible types

```python
# ❌ Error
def get_count() -> int:
    return "10"  # Error: str not compatible with int

# ✅ Fix
def get_count() -> int:
    return 10
```

#### Error: Missing return statement

```python
# ❌ Error
def find_user(user_id: str) -> User:
    user = db.query(User).filter_by(id=user_id).first()
    # Missing return for None case

# ✅ Fix
def find_user(user_id: str) -> Optional[User]:
    return db.query(User).filter_by(id=user_id).first()
```

---

## ✅ BEST PRACTICES

### 1. Start with Function Signatures

```python
# Priority order:
# 1. Public API functions (most important)
# 2. Internal service functions
# 3. Helper functions
# 4. Private functions
```

### 2. Use Type Aliases

```python
# Instead of repeating complex types
JobData = Dict[str, Union[str, int, List[str]]]

def process_job(data: JobData) -> None:
    pass

def queue_job(data: JobData) -> str:
    pass
```

### 3. Prefer Specific Types

```python
# ❌ Too generic
def search(query: Any) -> Any:
    pass

# ✅ Specific
def search(query: str) -> Dict[str, Any]:
    pass
```

### 4. Document Complex Types

```python
class JobConfig(TypedDict):
    """
    Configuration for a job.
    
    Attributes:
        job_id: Unique job identifier
        priority: Job priority (1-10, higher = more important)
        max_retries: Maximum retry attempts
        timeout: Timeout in seconds
    """
    job_id: str
    priority: int
    max_retries: int
    timeout: float
```

### 5. Use # type: ignore Sparingly

```python
# Only when absolutely necessary
result = third_party_lib.complex_function()  # type: ignore[attr-defined]

# Add explanation
result = legacy_code()  # type: ignore  # TODO: Fix after refactoring
```

---

## 📚 RESOURCES

### Official Documentation

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [mypy Documentation](https://mypy.readthedocs.io/)

### Tools

- **mypy**: Static type checker
- **pyright**: Microsoft's type checker (faster)
- **pyre**: Facebook's type checker
- **MonkeyType**: Automatic type hint generation

### Cheat Sheets

- [mypy Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Python Type Checking Guide](https://realpython.com/python-type-checking/)

---

**Document Status**: ✅ **READY FOR IMPLEMENTATION**  
**Last Updated**: October 10, 2025  
**Next Review**: After Phase 2 completion

