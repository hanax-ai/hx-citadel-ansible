# Integration Tests

Integration tests that validate component interactions across the HX-Citadel Shield.

## Test Files

- **test_mcp_server_health.py** - MCP server health check integration
  - Tests `/health` endpoint
  - Validates circuit breaker metrics
  - Verifies service availability

- **test_mcp_tools.py** - MCP tools basic integration tests
  - Tests all 7 MCP tools end-to-end (basic scenarios)
  - Validates orchestrator integration
  - Tests async job tracking

- **test_web_crawling_e2e.py** - Web crawling E2E tests (TEST-004)
  - 5 comprehensive test scenarios
  - Tests crawl_web tool with various URLs and error cases
  - Circuit breaker protection validation

- **test_doc_processing_e2e.py** - Document processing E2E tests (TEST-005)
  - 6 comprehensive test scenarios
  - Tests ingest_doc tool with PDF, TXT, MD files
  - Error handling for missing/invalid files

- **test_qdrant_operations_e2e.py** - Qdrant operations E2E tests (TEST-009)
  - 7 comprehensive test scenarios
  - Tests qdrant_store and qdrant_find tools
  - Embedding generation and metadata handling

- **test_lightrag_e2e.py** - LightRAG E2E tests (TEST-011)
  - 8 comprehensive test scenarios
  - Tests all 4 retrieval modes (local, global, hybrid, naive)
  - Context retrieval and response generation

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_mcp_server_health.py -v

# Run with markers
pytest tests/integration/ -m integration -v
```

## Requirements

Integration tests require:
- Running services (orchestrator, MCP server, Qdrant, Redis, PostgreSQL)
- Network access to service endpoints
- Longer timeouts than unit tests (30s default)

## Configuration

Integration test configuration is in `conftest.py`:
- Service URLs (FQDN format)
- Timeout settings
- Test data fixtures

## Test Coverage

| Component | Tests | Status |
|-----------|-------|--------|
| MCP Server Health | 1 | ✅ |
| MCP Tools (Basic) | 7 | ✅ |
| Web Crawling E2E | 5 | ✅ |
| Document Processing E2E | 6 | ✅ |
| Qdrant Operations E2E | 7 | ✅ |
| LightRAG E2E | 8 | ✅ |
| **Total** | **34** | **✅** |

## Adding New Tests

1. Create test file: `test_<component>_<feature>.py`
2. Use `@pytest.mark.integration` marker
3. Import fixtures from conftest.py
4. Use FQDN URLs (not IPs)
5. Set appropriate timeouts
6. Document in this README
