# Integration Tests

Integration tests that validate component interactions across the HX-Citadel Shield.

## Test Files

- **test_mcp_server_health.py** - MCP server health check integration
  - Tests `/health` endpoint
  - Validates circuit breaker metrics
  - Verifies service availability

- **test-mcp-tools.py** - MCP tools integration tests
  - Tests all 7 MCP tools end-to-end
  - Validates orchestrator integration
  - Tests async job tracking

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
| MCP Tools | 7 | 🔄 In Progress |

## Adding New Tests

1. Create test file: `test_<component>_<feature>.py`
2. Use `@pytest.mark.integration` marker
3. Import fixtures from conftest.py
4. Use FQDN URLs (not IPs)
5. Set appropriate timeouts
6. Document in this README
