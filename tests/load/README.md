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
