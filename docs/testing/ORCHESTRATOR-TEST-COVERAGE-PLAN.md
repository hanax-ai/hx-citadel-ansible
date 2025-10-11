# Orchestrator Component Testing Coverage Plan

**Phase 2 Sprint 2.2**: TASK-032 - Write Unit Tests (Orchestrator Components)

This document outlines the testing strategy for all orchestrator components (~30 Python modules).

---

## Executive Summary

**Total Components**: 30 Python modules across 10 orchestrator roles
**Current Test Coverage**: ~5% (common_types module only)
**Target Coverage**: 80%+ for critical paths, 60%+ overall
**Estimated Effort**: 12-16 hours (remaining ~60% of TASK-032)

---

## Component Inventory by Role

### 1. orchestrator_fastapi (4 modules) - **CRITICAL**
Core FastAPI application and health endpoints.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `main.py.j2` | ~150 | Medium | **P0** | App startup, lifespan events, router registration |
| `api/health.py.j2` | ~157 | Low | **P0** | Health endpoints (basic, detailed, readiness, liveness) |
| `config/settings.py.j2` | ~80 | Low | **P1** | Configuration loading, env var parsing |
| `utils/logging_config.py.j2` | ~60 | Low | **P2** | Logging setup, formatters |

**Test Priority**: P0 (must have)
- Health check endpoints return correct status codes
- App startup/shutdown lifecycle works correctly
- Configuration loads from environment variables
- Logging configuration is valid

**Mock Requirements**:
- PostgreSQL connection
- Redis connection
- Qdrant client
- Ollama API
- Worker pool

---

### 2. orchestrator_qdrant (2 modules) - **CRITICAL**
Vector database operations and embeddings.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `services/embeddings.py.j2` | ~117 | Medium | **P0** | Embedding generation (single, batch), health checks |
| `services/qdrant_client.py.j2` | ~200 | High | **P0** | Vector search, storage, collection management |

**Test Priority**: P0 (must have)
- Embedding generation works (single text)
- Batch embedding generation with concurrency
- Ollama health check handles errors
- Qdrant client connection pooling
- Vector search query execution
- Vector storage with metadata

**Mock Requirements**:
- httpx.AsyncClient for Ollama API
- Qdrant Python client
- Ollama embedding API responses

**Critical Test Cases**:
```python
# Embeddings
test_get_embedding_success()
test_get_embedding_ollama_unavailable()
test_get_embeddings_batch_concurrent()
test_check_ollama_health_success()
test_check_ollama_health_timeout()

# Qdrant Client
test_search_vectors_with_filters()
test_store_vector_with_metadata()
test_create_collection_if_not_exists()
test_connection_retry_logic()
```

---

### 3. orchestrator_workers (5 modules) - **CRITICAL**
Async worker pool and job management.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `workers/worker_pool.py.j2` | ~286 | **Very High** | **P0** | Worker lifecycle, graceful shutdown, error handling |
| `services/job_tracker.py.j2` | ~150 | High | **P0** | Job status tracking, progress updates |
| `services/event_bus.py.j2` | ~100 | Medium | **P1** | Event emission, Redis Streams integration |
| `api/jobs.py.j2` | ~120 | Medium | **P1** | Job status API endpoints |
| `workers/lightrag_processor.py.j2` | ~180 | High | **P0** | Chunk processing, LightRAG integration |

**Test Priority**: P0 (must have)
- Worker pool starts with correct pool size
- Workers consume tasks from Redis Streams
- Graceful shutdown on SIGTERM/SIGINT
- Max tasks per worker restart logic
- Job status tracking (pending → processing → completed)
- Job progress updates (0-100%)
- Error handling and retry logic
- Event bus emits events correctly

**Mock Requirements**:
- Redis Streams client (XREADGROUP, XACK, XDEL)
- LightRAG processor
- Event bus
- Asyncio tasks and signals

**Critical Test Cases**:
```python
# Worker Pool
test_worker_pool_start_creates_n_workers()
test_worker_loop_processes_task_from_stream()
test_worker_graceful_shutdown_on_sigterm()
test_worker_restart_after_max_tasks()
test_worker_error_handling_does_not_ack()
test_worker_pool_health_check()

# Job Tracker
test_create_job_returns_job_id()
test_update_job_progress_clamps_0_100()
test_update_job_status_completed()
test_update_job_status_failed_with_error()
test_get_job_status_not_found()

# Event Bus
test_emit_event_to_redis_stream()
test_emit_event_handles_redis_unavailable()
```

---

### 4. orchestrator_lightrag (3 modules) - **HIGH**
LightRAG integration for document processing and querying.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `services/lightrag_service.py.j2` | ~200 | High | **P0** | LightRAG initialization, query, ingestion |
| `api/query.py.j2` | ~100 | Medium | **P1** | Query endpoint, mode validation |
| `api/ingestion.py.j2` | ~120 | Medium | **P1** | Ingestion endpoint, chunk processing |

**Test Priority**: P0-P1
- LightRAG service initialization
- Query execution (naive, local, global, hybrid modes)
- Document ingestion with chunking
- Error handling for invalid modes
- Health check for LightRAG engine

**Mock Requirements**:
- LightRAG library (query, insert methods)
- Qdrant client
- Embedding service

**Critical Test Cases**:
```python
test_lightrag_query_naive_mode()
test_lightrag_query_hybrid_mode()
test_lightrag_ingest_document_chunks()
test_lightrag_invalid_mode_validation()
test_lightrag_health_check()
```

---

### 5. orchestrator_langgraph (4 modules) - **MEDIUM**
Workflow orchestration with state graphs.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `workflow_manager.py.j2` | ~150 | High | **P1** | Workflow state management, transitions |
| `workflows/query_workflow.py.j2` | ~120 | Medium | **P1** | Query workflow graph |
| `workflows/ingestion_workflow.py.j2` | ~140 | Medium | **P1** | Ingestion workflow graph |
| `workflows/__init__.py.j2` | ~20 | Low | **P2** | Workflow exports |

**Test Priority**: P1 (should have)
- Workflow state transitions
- Query workflow execution
- Ingestion workflow execution
- Error handling in workflow nodes

**Mock Requirements**:
- LangGraph state graph
- LightRAG service
- Qdrant client

---

### 6. orchestrator_pydantic_ai (4 modules) - **MEDIUM**
Agent-based AI coordination.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `services/agent_manager.py.j2` | ~100 | Medium | **P1** | Agent lifecycle, coordination |
| `agents/query_router.py.j2` | ~80 | Medium | **P2** | Query routing logic |
| `agents/web_crawl_coordinator.py.j2` | ~90 | Medium | **P2** | Web crawl coordination |
| `agents/doc_process_coordinator.py.j2` | ~85 | Medium | **P2** | Document processing coordination |

**Test Priority**: P1-P2 (nice to have)
- Agent initialization
- Query routing based on intent
- Coordination logic

---

### 7. orchestrator_postgresql (3 modules) - **MEDIUM**
Database connection and models.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `database/connection.py.j2` | ~80 | Medium | **P1** | Connection pooling, health checks |
| `database/models.py.j2` | ~150 | Low | **P1** | SQLAlchemy ORM models |
| `database/migrations/env.py.j2` | ~60 | Low | **P2** | Alembic migration config |

**Test Priority**: P1 (should have)
- Database connection pooling
- Connection health checks
- ORM model definitions

**Mock Requirements**:
- SQLAlchemy engine
- PostgreSQL connection

---

### 8. orchestrator_redis (2 modules) - **MEDIUM**
Redis Streams and event handling.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `services/redis_streams.py.j2` | ~120 | Medium | **P1** | Redis Streams client, consumer groups |
| `api/events.py.j2` | ~80 | Low | **P2** | Event API endpoints |

**Test Priority**: P1 (should have)
- Redis Streams client connection
- Consumer group creation
- Stream reading (XREADGROUP)

---

### 9. orchestrator_copilotkit (2 modules) - **LOW**
Real-time collaboration adapter.

| Component | Lines | Complexity | Priority | Test Strategy |
|-----------|-------|------------|----------|---------------|
| `services/copilotkit_adapter.py.j2` | ~100 | Medium | **P2** | WebSocket handling, state sync |
| `api/copilotkit.py.j2` | ~70 | Low | **P2** | CopilotKit API endpoints |

**Test Priority**: P2 (nice to have)
- WebSocket connection handling
- State synchronization

---

### 10. orchestrator_base_setup (0 modules)
No Python components (only setup tasks).

---

## Testing Strategy by Priority

### P0: Critical Path (Must Have) - **80%+ Coverage Target**
**Effort**: 8-10 hours

Components:
- `orchestrator_fastapi/api/health.py.j2` (4 endpoints)
- `orchestrator_qdrant/services/embeddings.py.j2` (3 functions)
- `orchestrator_qdrant/services/qdrant_client.py.j2` (6 functions)
- `orchestrator_workers/workers/worker_pool.py.j2` (5 functions)
- `orchestrator_workers/services/job_tracker.py.j2` (5 functions)
- `orchestrator_lightrag/services/lightrag_service.py.j2` (4 functions)

**Total**: ~27 functions

**Test Files to Create**:
1. `tests/unit/test_orchestrator_health.py` (15 tests)
2. `tests/unit/test_orchestrator_embeddings.py` (12 tests)
3. `tests/unit/test_orchestrator_qdrant_client.py` (18 tests)
4. `tests/unit/test_orchestrator_worker_pool.py` (25 tests)
5. `tests/unit/test_orchestrator_job_tracker.py` (15 tests)
6. `tests/unit/test_orchestrator_lightrag.py` (18 tests)

**Total P0 Tests**: ~103 tests

---

### P1: Important (Should Have) - **60%+ Coverage Target**
**Effort**: 3-4 hours

Components:
- `orchestrator_fastapi/config/settings.py.j2`
- `orchestrator_workers/services/event_bus.py.j2`
- `orchestrator_workers/api/jobs.py.j2`
- `orchestrator_lightrag/api/query.py.j2`
- `orchestrator_lightrag/api/ingestion.py.j2`
- `orchestrator_langgraph/workflow_manager.py.j2`
- `orchestrator_pydantic_ai/services/agent_manager.py.j2`
- `orchestrator_postgresql/database/connection.py.j2`
- `orchestrator_redis/services/redis_streams.py.j2`

**Total**: ~15 functions

**Test Files to Create**:
1. `tests/unit/test_orchestrator_config.py` (8 tests)
2. `tests/unit/test_orchestrator_event_bus.py` (10 tests)
3. `tests/unit/test_orchestrator_jobs_api.py` (12 tests)
4. `tests/unit/test_orchestrator_lightrag_api.py` (15 tests)
5. `tests/unit/test_orchestrator_workflows.py` (12 tests)
6. `tests/unit/test_orchestrator_agents.py` (10 tests)
7. `tests/unit/test_orchestrator_database.py` (8 tests)
8. `tests/unit/test_orchestrator_redis.py` (10 tests)

**Total P1 Tests**: ~85 tests

---

### P2: Nice to Have (Optional) - **40%+ Coverage Target**
**Effort**: 1-2 hours

Components:
- `orchestrator_fastapi/utils/logging_config.py.j2`
- `orchestrator_pydantic_ai/agents/*` (3 agent modules)
- `orchestrator_copilotkit/*` (2 modules)
- `orchestrator_redis/api/events.py.j2`

**Total P2 Tests**: ~30 tests

---

## Testing Patterns and Mocking Strategy

### 1. Async Testing Pattern
All orchestrator components use async/await, so use pytest-asyncio:

```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_async_function():
    """Test async function behavior"""
    # Arrange
    mock_client = AsyncMock()
    mock_client.post.return_value.json.return_value = {"embedding": [0.1, 0.2]}

    # Act
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await get_embedding("test text")

    # Assert
    assert len(result) > 0
    mock_client.post.assert_called_once()
```

### 2. External Service Mocking

**Ollama API Mock**:
```python
@pytest.fixture
def mock_ollama_response():
    return {
        "embedding": [0.1] * 1024,  # 1024-dimensional vector
        "model": "mxbai-embed-large"
    }

@pytest.fixture
def mock_ollama_client(mock_ollama_response):
    mock = AsyncMock()
    mock.post.return_value.json.return_value = mock_ollama_response
    mock.post.return_value.raise_for_status = MagicMock()
    return mock
```

**Qdrant Client Mock**:
```python
@pytest.fixture
def mock_qdrant_client():
    mock = MagicMock()
    mock.search.return_value = [
        {"id": "1", "score": 0.95, "payload": {"text": "result 1"}},
        {"id": "2", "score": 0.87, "payload": {"text": "result 2"}}
    ]
    return mock
```

**Redis Streams Mock**:
```python
@pytest.fixture
def mock_redis_streams():
    mock = AsyncMock()
    mock.xreadgroup.return_value = [
        ("stream_name", [
            (b"msg-1", {b"job_id": b"job-123", b"chunk": b"chunk data"})
        ])
    ]
    mock.xack.return_value = 1
    mock.xdel.return_value = 1
    return mock
```

### 3. Worker Pool Testing Pattern

**Testing Async Workers**:
```python
@pytest.mark.asyncio
async def test_worker_pool_start():
    """Test worker pool starts correct number of workers"""
    pool = WorkerPool(pool_size=4)

    with patch.object(pool, '_worker_loop', new_callable=AsyncMock):
        await pool.start()

        assert pool.running is True
        assert len(pool.workers) == 4
        assert all(isinstance(w, asyncio.Task) for w in pool.workers)
```

**Testing Graceful Shutdown**:
```python
@pytest.mark.asyncio
async def test_worker_pool_graceful_shutdown():
    """Test worker pool stops gracefully"""
    pool = WorkerPool(pool_size=2)

    # Start pool with mocked worker loop
    async def mock_worker_loop(worker_id):
        await asyncio.sleep(0.1)  # Simulate work

    with patch.object(pool, '_worker_loop', side_effect=mock_worker_loop):
        await pool.start()
        await asyncio.sleep(0.05)  # Let workers start

        # Stop pool
        await pool.stop()

        assert pool.running is False
        assert all(w.done() for w in pool.workers)
```

### 4. Health Check Testing Pattern

```python
@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test basic health check returns 200"""
    response = await health_check()

    assert response.status == "healthy"
    assert response.version is not None
    assert response.uptime_seconds >= 0

@pytest.mark.asyncio
async def test_health_detailed_all_services_up():
    """Test detailed health when all services operational"""
    with patch("services.qdrant_client.check_qdrant_health") as mock_qdrant, \
         patch("services.embeddings.check_ollama_health") as mock_ollama:

        mock_qdrant.return_value = {"status": "up", "latency_ms": 5}
        mock_ollama.return_value = {"status": "up", "latency_ms": 10}

        response = await health_detailed()

        assert response.overall_status == "healthy"
        assert response.components["qdrant"]["status"] == "up"
        assert response.components["ollama"]["status"] == "up"
```

---

## Test Execution Plan

### Phase 1: P0 Tests (8-10 hours)
**Week 1 - Days 1-2**

1. **Health & Config** (2 hours)
   - Create `test_orchestrator_health.py`
   - Create `test_orchestrator_config.py`
   - 23 tests total

2. **Embeddings & Qdrant** (3 hours)
   - Create `test_orchestrator_embeddings.py`
   - Create `test_orchestrator_qdrant_client.py`
   - 30 tests total

3. **Workers & Jobs** (3-4 hours)
   - Create `test_orchestrator_worker_pool.py`
   - Create `test_orchestrator_job_tracker.py`
   - 40 tests total

4. **LightRAG** (2 hours)
   - Create `test_orchestrator_lightrag.py`
   - 18 tests total

**Deliverable**: ~111 P0 tests, 80%+ coverage on critical path

### Phase 2: P1 Tests (3-4 hours)
**Week 1 - Day 3**

1. **Event Bus & Jobs API** (1.5 hours)
   - Create `test_orchestrator_event_bus.py`
   - Create `test_orchestrator_jobs_api.py`
   - 22 tests total

2. **LightRAG API & Workflows** (1.5 hours)
   - Create `test_orchestrator_lightrag_api.py`
   - Create `test_orchestrator_workflows.py`
   - 27 tests total

3. **Agents, Database, Redis** (1-2 hours)
   - Create `test_orchestrator_agents.py`
   - Create `test_orchestrator_database.py`
   - Create `test_orchestrator_redis.py`
   - 28 tests total

**Deliverable**: ~77 P1 tests, 60%+ coverage on important components

### Phase 3: P2 Tests (1-2 hours) - **OPTIONAL**
**Week 1 - Day 3 (if time permits)**

1. **Logging & Agents**
   - Create remaining P2 tests
   - ~30 tests total

---

## Test Infrastructure Requirements

### Dependencies (add to `requirements-dev.txt`):
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.25.2
```

### Conftest Extensions:
```python
# tests/unit/conftest.py additions

@pytest.fixture
def mock_ollama_client():
    """Mock Ollama API client"""
    mock = AsyncMock()
    mock.post.return_value.json.return_value = {
        "embedding": [0.1] * 1024
    }
    return mock

@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    mock = MagicMock()
    mock.search.return_value = []
    return mock

@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    mock = AsyncMock()
    mock.xreadgroup.return_value = []
    return mock

@pytest.fixture
def mock_worker_pool():
    """Mock worker pool"""
    mock = MagicMock()
    mock.pool_size = 4
    mock.workers = []
    mock.running = True
    return mock
```

---

## Coverage Metrics

### Coverage Goals by Component Type:

| Component Type | Target Coverage | Priority |
|----------------|-----------------|----------|
| Health Endpoints | 90%+ | P0 |
| Worker Pool | 80%+ | P0 |
| Embedding Service | 85%+ | P0 |
| Qdrant Client | 80%+ | P0 |
| Job Tracker | 85%+ | P0 |
| LightRAG Service | 75%+ | P0 |
| Event Bus | 70%+ | P1 |
| API Endpoints | 70%+ | P1 |
| Workflows | 60%+ | P1 |
| Agents | 50%+ | P2 |
| Config/Utils | 50%+ | P2 |

### Running Coverage Reports:
```bash
# Run all orchestrator tests with coverage
pytest tests/unit/test_orchestrator_*.py --cov=roles/orchestrator_*/templates --cov-report=html

# Coverage report by component
pytest tests/unit/test_orchestrator_worker_pool.py --cov=roles/orchestrator_workers/templates/workers --cov-report=term-missing

# Generate HTML coverage report
pytest tests/unit/ --cov=roles --cov-report=html:htmlcov
open htmlcov/index.html
```

---

## Success Criteria

### TASK-032 Complete When:

1. **P0 Tests Complete** (Must Have)
   - ✅ ~103 P0 tests written and passing
   - ✅ 80%+ coverage on critical path components
   - ✅ All health endpoints tested
   - ✅ Worker pool lifecycle tested
   - ✅ Embeddings service tested
   - ✅ Job tracker tested

2. **P1 Tests Complete** (Should Have)
   - ✅ ~85 P1 tests written and passing
   - ✅ 60%+ coverage on important components
   - ✅ Event bus tested
   - ✅ LightRAG API tested

3. **Documentation Complete**
   - ✅ Test README updated with orchestrator testing
   - ✅ Coverage report generated
   - ✅ Testing patterns documented

4. **CI/CD Ready**
   - ✅ All tests run in < 30 seconds
   - ✅ No flaky tests
   - ✅ Proper async test isolation

### Overall TASK-032 Metrics:
- **Common Types**: 53 tests ✅ (COMPLETE)
- **Orchestrator P0**: ~103 tests (target)
- **Orchestrator P1**: ~85 tests (target)
- **Total**: ~241 tests
- **Overall Coverage**: 70%+ (target)

---

## Related Tasks

- **TASK-032**: Write Unit Tests (this task)
- **TASK-033**: Write Integration Tests (tests across components)
- **TASK-034**: Create Load Test Scripts (performance testing)
- **TASK-036**: Configure Code Coverage (coverage thresholds, badges)
- **TASK-038**: Run Full Test Suite (end-to-end validation)

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Start with P0 tests** (health, embeddings, workers)
3. **Iterate based on coverage metrics**
4. **Document test patterns** in README
5. **Integrate with CI/CD** (TASK-035)

---

**Document Version**: 1.0
**Created**: October 11, 2025
**Task**: TASK-032 - Write Unit Tests (Orchestrator Components)
**Sprint**: Phase 2 Sprint 2.2 - Automated Testing & CI/CD
