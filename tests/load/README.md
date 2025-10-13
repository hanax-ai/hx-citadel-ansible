# Load and Performance Tests

Load testing and performance benchmarking for HX-Citadel Shield.

## Test Plans

- **load_test_plan.md** - Comprehensive load testing strategy
  - Circuit breaker load scenarios
  - MCP server throughput testing
  - Worker pool stress testing
  - Database connection pooling tests

## Load Testing Tools

We use **Locust** for load testing (see `requirements-dev.txt`).

## Running Load Tests

```bash
# Install load testing dependencies
pip install -r requirements-dev.txt

# Run load tests (when locustfiles are created)
locust -f tests/load/locustfiles/mcp_server.py --host=http://hx-mcp1-server:8081
```

## Test Scenarios

### 1. Circuit Breaker Load Test
- Validate fast-fail under load
- Test circuit state transitions
- Measure recovery time

### 2. MCP Server Throughput
- Test concurrent tool executions
- Measure response times
- Identify bottlenecks

### 3. Worker Pool Stress Test
- Test with 1000+ concurrent jobs
- Validate graceful degradation
- Monitor memory usage

### 4. Database Connection Pooling
- Test connection limits
- Validate connection reuse
- Monitor connection leak

## Metrics to Collect

- Requests per second (RPS)
- Average response time
- 95th/99th percentile latency
- Error rate
- Resource utilization (CPU, memory)

## Creating Locustfiles

Locustfiles should be placed in `tests/load/locustfiles/`:

```python
from locust import HttpUser, task, between

class MCPServerUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        self.client.get("/health")
```

## Next Steps

1. Create `locustfiles/` directory
2. Implement load test scenarios from load_test_plan.md
3. Document baseline performance metrics
4. Set up automated load testing in CI/CD

---

## Implementation Complete ✅

Load test framework is now fully implemented with 4 Locustfiles and 7 scenarios.

### Locustfiles

1. **mcp_server.py** - MCP Server endpoints
   - Tests all 7 MCP tools (crawl_web, ingest_doc, qdrant_store, qdrant_find, lightrag_query, get_job_status, health_check)
   - Task weights based on expected usage patterns
   - Realistic wait times (1-3 seconds)

2. **orchestrator_api.py** - Orchestrator API
   - Health checks
   - Job status lookups
   - Job listing

3. **qdrant_operations.py** - Qdrant vector database
   - Health checks
   - Collection listing
   - Vector search operations

4. **circuit_breaker.py** - Circuit breaker scenarios
   - Normal load testing
   - High load with failures
   - Circuit breaker state monitoring

### Running Load Tests

#### Quick Start

```bash
# Run normal load test (100 users, 60s)
./tests/load/run_load_tests.sh normal

# Run stress test (500 users, 300s)
./tests/load/run_load_tests.sh stress

# Run all scenarios
./tests/load/run_load_tests.sh all
```

#### Available Scenarios

1. **normal** - Baseline (100 users, 60s)
2. **stress** - High load (500 users, 300s)
3. **spike** - Rapid increase (1000 users, 120s)
4. **endurance** - Long-running (100 users, 3600s)
5. **circuit** - Circuit breaker (50 users, 180s)
6. **orchestrator** - Orchestrator API (50 users, 60s)
7. **qdrant** - Qdrant operations (100 users, 60s)

#### Manual Locust Usage

```bash
# Run with web UI
locust -f tests/load/locustfiles/mcp_server.py --host=http://hx-mcp1-server:8081

# Run headless
locust -f tests/load/locustfiles/mcp_server.py \
  --host=http://hx-mcp1-server:8081 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --headless \
  --html=results/report.html

# Override server URL
MCP_SERVER_URL=http://localhost:8081 locust -f tests/load/locustfiles/mcp_server.py
```

### Understanding Results

After running tests, check the results directory:

```bash
tests/load/results/
├── normal_load_report.html    # HTML report with charts
├── normal_load_stats.csv      # Request statistics
├── normal_load_failures.csv   # Failure details
└── normal_load.log           # Execution log
```

Key metrics to review:
- **RPS (Requests Per Second)** - Throughput
- **Response Time** - Latency percentiles (p50, p95, p99)
- **Failure Rate** - Error percentage
- **Users** - Concurrent users over time

### Performance Targets

See `load_test_config.yaml` for expected performance targets:
- Health check: p95 < 500ms
- LightRAG query: p95 < 5s
- Qdrant find: p95 < 2s
- Circuit breaker fast-fail: < 100ms

### Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'locust'`
**Fix**: `pip install -r requirements-dev.txt`

**Issue**: Connection refused
**Fix**: Ensure target services are running and accessible

**Issue**: High failure rate
**Fix**: Check service health, increase wait times, or reduce user count

### CI/CD Integration

Load tests are currently manual. To integrate into CI:

```yaml
# .github/workflows/load-test.yml (future)
- name: Run load tests
  run: |
    ./tests/load/run_load_tests.sh normal
    # Upload results as artifacts
```

## References

- GitHub Issues: #10, #28
- Load test plan: load_test_plan.md
- Sprint: 2.2 TASK-034
