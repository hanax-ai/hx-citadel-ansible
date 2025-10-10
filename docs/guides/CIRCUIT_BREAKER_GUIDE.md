# Circuit Breaker Pattern Guide
## Resilience Pattern for External Service Calls

**Version**: 1.0  
**Date**: October 10, 2025  
**Status**: Implementation Guide  
**Related**: CODEBASE-ENHANCEMENT-RECOMMENDATIONS.md

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [The Solution](#the-solution)
4. [Implementation](#implementation)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 OVERVIEW

### What is a Circuit Breaker?

A **Circuit Breaker** is a design pattern that prevents an application from repeatedly trying to execute an operation that's likely to fail. It acts like an electrical circuit breaker:

- **Closed State**: Requests flow normally
- **Open State**: Requests fail immediately (fast-fail)
- **Half-Open State**: Test if service recovered

### Why Use Circuit Breakers?

**Without Circuit Breaker**:
```
Service Down → Request Timeout (30s) → Retry → Timeout (30s) → ...
Result: System unresponsive, resources exhausted
```

**With Circuit Breaker**:
```
Service Down → Circuit Opens → Fast Fail (< 1ms) → System Responsive
After 60s → Test Request → If Success: Close Circuit
```

### Benefits

| Benefit | Description |
|---------|-------------|
| **Fast-Fail** | No waiting for timeout (30s → < 1ms) |
| **Resource Protection** | Prevent thread/connection exhaustion |
| **Automatic Recovery** | Self-healing without manual intervention |
| **Cascading Prevention** | Stop failures from propagating |
| **Better UX** | Immediate error vs. long wait |
| **Observability** | Circuit state tracked in metrics |

---

## ❌ THE PROBLEM

### Scenario: Orchestrator Service Fails

```
┌──────────────┐                  ┌──────────────┐
│  MCP Server  │                  │ Orchestrator │
│              │                  │   (DOWN ❌)   │
└──────┬───────┘                  └──────────────┘
       │
       │ Request 1: /ingest
       ├────────────────────────────────────►
       │                                     ⏳ Wait 30 seconds
       │                                     ❌ Timeout
       │◄────────────────────────────────────┤
       │
       │ Request 2: /ingest
       ├────────────────────────────────────►
       │                                     ⏳ Wait 30 seconds
       │                                     ❌ Timeout
       │◄────────────────────────────────────┤
       │
       │ Request 3: /ingest
       ├────────────────────────────────────►
       │                                     ⏳ Wait 30 seconds
       │                                     ❌ Timeout
       │◄────────────────────────────────────┤
       │
       │ ... continues forever ...
       │
```

### Problems

1. **Resource Exhaustion**
   - Each request ties up a thread for 30s
   - With 100 requests/min: 50 threads blocked permanently
   - Server runs out of threads/connections
   - System becomes completely unresponsive

2. **Poor User Experience**
   - Users wait 30+ seconds for error
   - Multiple retries (each 30s)
   - Total wait time: 2-3 minutes

3. **Cascading Failures**
   - MCP server becomes unresponsive
   - LiteLLM gateway times out
   - Entire system fails

4. **No Self-Healing**
   - Even when orchestrator comes back up
   - Requests continue to fail (connection pool exhausted)
   - Requires manual restart

---

## ✅ THE SOLUTION

### Circuit Breaker State Machine

```
                     ┌─────────────────┐
                     │     CLOSED      │
                     │  (Normal flow)  │
                     └────────┬────────┘
                              │
                 Failures ≥ threshold (5)
                              │
                              ▼
                     ┌─────────────────┐
                     │      OPEN       │
          ┌─────────►│   (Fast-fail)   │◄─────────┐
          │          └────────┬────────┘          │
          │                   │                   │
          │     After recovery_timeout (60s)      │
          │                   │                   │
          │                   ▼                   │
          │          ┌─────────────────┐          │
          │          │   HALF-OPEN     │          │
  Test fails         │  (Test request) │    Test succeeds
          │          └────────┬────────┘          │
          │                   │                   │
          └───────────────────┴───────────────────┘
```

### State Descriptions

**CLOSED** (Normal Operation):
- Requests pass through normally
- Success: Continue
- Failure: Increment failure counter
- If failures ≥ threshold: Open circuit

**OPEN** (Fast-Fail):
- All requests fail immediately (< 1ms)
- Return error without calling service
- After recovery_timeout: Transition to HALF-OPEN
- Protects resources, maintains responsiveness

**HALF-OPEN** (Testing):
- Allow ONE test request through
- Success: Close circuit (recovered!)
- Failure: Re-open circuit (still broken)
- Prevents premature recovery

---

## 🛠️ IMPLEMENTATION

### Step 1: Install Circuit Breaker Library

```bash
# Add to requirements.txt
echo "circuitbreaker==1.4.0" >> roles/fastmcp_server/files/requirements.txt

# Install
pip install circuitbreaker
```

### Step 2: Import and Configure

```python
from circuitbreaker import circuit
import httpx
import logging

logger = logging.getLogger(__name__)

# Configuration
FAILURE_THRESHOLD = 5      # Open after 5 failures
RECOVERY_TIMEOUT = 60      # Try recovery after 60 seconds
EXPECTED_EXCEPTION = httpx.HTTPError  # Exceptions to count
```

### Step 3: Apply Circuit Breaker Decorator

```python
@circuit(
    failure_threshold=FAILURE_THRESHOLD,
    recovery_timeout=RECOVERY_TIMEOUT,
    expected_exception=EXPECTED_EXCEPTION
)
async def call_orchestrator_api(
    endpoint: str,
    data: dict
) -> dict:
    """
    Call orchestrator API with circuit breaker protection.
    
    Circuit opens after 5 consecutive failures.
    Stays open for 60 seconds (fast-fail).
    Automatically tests recovery after timeout.
    
    Args:
        endpoint: API endpoint (e.g., "/ingest-async")
        data: Request payload
    
    Returns:
        Response JSON
    
    Raises:
        httpx.HTTPError: On request failure
        CircuitBreakerError: When circuit is open
    """
    url = f"{ORCHESTRATOR_URL}{endpoint}"
    
    logger.debug(f"Calling orchestrator: {endpoint}")
    
    try:
        response = await http_client.post(url, json=data, timeout=30.0)
        response.raise_for_status()
        
        # Success - reset failure counter (implicit)
        logger.info(f"orchestrator_call_success", endpoint=endpoint)
        
        return response.json()
        
    except httpx.HTTPError as e:
        # Failure - increment counter (implicit)
        logger.error(
            f"orchestrator_call_failed",
            endpoint=endpoint,
            status_code=getattr(e.response, 'status_code', None),
            exc_info=True
        )
        raise
```

### Step 4: Handle Circuit Breaker Errors

```python
from circuitbreaker import CircuitBreakerError

@mcp.tool()
async def crawl_web(url: str) -> dict:
    """Crawl website with circuit breaker protection."""
    
    try:
        # Call protected function
        result = await call_orchestrator_api("/ingest-async", {
            "source_type": "web_crawl",
            "source_uri": url
        })
        
        return {
            "status": "queued",
            "job_id": result["job_id"]
        }
        
    except CircuitBreakerError:
        # Circuit is open - orchestrator is down
        logger.warning("circuit_breaker_open", service="orchestrator")
        
        return {
            "status": "error",
            "error": "service_unavailable",
            "message": "Orchestrator service is currently unavailable. Please try again in 1 minute.",
            "retry_after": 60
        }
        
    except httpx.HTTPError as e:
        # Request failed but circuit still closed
        logger.error("orchestrator_request_failed", error=str(e))
        
        return {
            "status": "error",
            "error": "request_failed",
            "message": str(e)
        }
```

### Step 5: Add Prometheus Metrics

```python
from prometheus_client import Gauge

# Circuit breaker state metric
circuit_breaker_state = Gauge(
    'shield_mcp_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

# Update circuit state
@circuit(failure_threshold=5, recovery_timeout=60, expected_exception=httpx.HTTPError)
async def call_orchestrator_api(endpoint: str, data: dict) -> dict:
    """Call with circuit breaker and metrics."""
    
    # Get circuit state
    circuit_state = call_orchestrator_api._circuit_breaker.current_state
    
    # Update metric
    if circuit_state == 'open':
        circuit_breaker_state.labels(service='orchestrator').set(1)
    elif circuit_state == 'half_open':
        circuit_breaker_state.labels(service='orchestrator').set(2)
    else:  # closed
        circuit_breaker_state.labels(service='orchestrator').set(0)
    
    # Make request
    response = await http_client.post(f"{ORCHESTRATOR_URL}{endpoint}", json=data)
    response.raise_for_status()
    
    return response.json()
```

---

## ⚙️ CONFIGURATION

### Tuning Parameters

```python
# Configuration guide
CONFIGURATIONS = {
    "aggressive": {
        "failure_threshold": 3,     # Open after 3 failures
        "recovery_timeout": 30,     # Test recovery after 30s
        "use_case": "Fast-changing services, quick recovery expected"
    },
    "balanced": {
        "failure_threshold": 5,     # Open after 5 failures
        "recovery_timeout": 60,     # Test recovery after 60s
        "use_case": "Default - good for most services"
    },
    "conservative": {
        "failure_threshold": 10,    # Open after 10 failures
        "recovery_timeout": 120,    # Test recovery after 120s
        "use_case": "Stable services, avoid false positives"
    }
}
```

### Environment-Based Configuration

```python
import os

# Load from environment
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": int(os.getenv("CB_FAILURE_THRESHOLD", "5")),
    "recovery_timeout": int(os.getenv("CB_RECOVERY_TIMEOUT", "60")),
    "expected_exception": httpx.HTTPError
}

@circuit(**CIRCUIT_BREAKER_CONFIG)
async def call_orchestrator_api(endpoint: str, data: dict) -> dict:
    """Call with environment-configured circuit breaker."""
    # Implementation...
```

### Ansible Template

```jinja2
{# roles/fastmcp_server/templates/shield_mcp_server.py.j2 #}

# Circuit breaker configuration
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": {{ circuit_breaker_failure_threshold | default(5) }},
    "recovery_timeout": {{ circuit_breaker_recovery_timeout | default(60) }},
    "expected_exception": httpx.HTTPError
}

@circuit(**CIRCUIT_BREAKER_CONFIG)
async def call_orchestrator_api(endpoint: str, data: dict) -> dict:
    """Call orchestrator with circuit breaker."""
    # Implementation...
```

```yaml
# group_vars/all/main.yml
circuit_breaker_failure_threshold: 5
circuit_breaker_recovery_timeout: 60
```

---

## 📊 MONITORING

### Prometheus Metrics

```python
from prometheus_client import Counter, Gauge, start_http_server

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'shield_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service', 'endpoint']
)

circuit_breaker_failures = Counter(
    'shield_circuit_breaker_failures_total',
    'Total failures tracked by circuit breaker',
    ['service', 'endpoint']
)

circuit_breaker_opens = Counter(
    'shield_circuit_breaker_opens_total',
    'Total times circuit breaker opened',
    ['service', 'endpoint']
)

circuit_breaker_recoveries = Counter(
    'shield_circuit_breaker_recoveries_total',
    'Total times circuit breaker recovered',
    ['service', 'endpoint']
)

# Track circuit events
def track_circuit_event(service: str, endpoint: str, event: str):
    """Track circuit breaker events."""
    
    if event == 'failure':
        circuit_breaker_failures.labels(service=service, endpoint=endpoint).inc()
    elif event == 'open':
        circuit_breaker_opens.labels(service=service, endpoint=endpoint).inc()
        circuit_breaker_state.labels(service=service, endpoint=endpoint).set(1)
    elif event == 'recovery':
        circuit_breaker_recoveries.labels(service=service, endpoint=endpoint).inc()
        circuit_breaker_state.labels(service=service, endpoint=endpoint).set(0)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Circuit Breaker Status",
    "panels": [
      {
        "title": "Circuit Breaker State",
        "targets": [
          {
            "expr": "shield_circuit_breaker_state",
            "legendFormat": "{{service}}/{{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Failure Rate",
        "targets": [
          {
            "expr": "rate(shield_circuit_breaker_failures_total[5m])",
            "legendFormat": "{{service}}/{{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Circuit Opens",
        "targets": [
          {
            "expr": "increase(shield_circuit_breaker_opens_total[1h])",
            "legendFormat": "{{service}}/{{endpoint}}"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

### Alerts

```yaml
# prometheus_alerts.yml
groups:
  - name: circuit_breakers
    rules:
      - alert: CircuitBreakerOpen
        expr: shield_circuit_breaker_state == 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker open for {{ $labels.service }}/{{ $labels.endpoint }}"
          description: "Service may be down or experiencing issues"
          
      - alert: CircuitBreakerFlapping
        expr: increase(shield_circuit_breaker_opens_total[10m]) > 3
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker flapping for {{ $labels.service }}"
          description: "Circuit opened 3+ times in 10 minutes - unstable service"
          
      - alert: CircuitBreakerPermanentlyOpen
        expr: shield_circuit_breaker_state == 1
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker open for 10+ minutes"
          description: "Service {{ $labels.service }} has been down for extended period"
```

---

## 🧪 TESTING

### Unit Tests

```python
import pytest
from circuitbreaker import CircuitBreakerError
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit opens after threshold failures."""
    
    # Mock HTTP client to always fail
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.side_effect = httpx.HTTPError("Service unavailable")
        
        # Make requests until circuit opens
        for i in range(FAILURE_THRESHOLD):
            with pytest.raises(httpx.HTTPError):
                await call_orchestrator_api("/test", {})
        
        # Next request should fail with CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await call_orchestrator_api("/test", {})


@pytest.mark.asyncio
async def test_circuit_breaker_recovers():
    """Test circuit recovers after timeout."""
    
    # Mock HTTP client
    with patch('httpx.AsyncClient.post') as mock_post:
        # First 5 requests fail
        mock_post.side_effect = [
            httpx.HTTPError("Error")] * FAILURE_THRESHOLD
        
        # Trigger failures to open circuit
        for _ in range(FAILURE_THRESHOLD):
            with pytest.raises(httpx.HTTPError):
                await call_orchestrator_api("/test", {})
        
        # Circuit should be open
        with pytest.raises(CircuitBreakerError):
            await call_orchestrator_api("/test", {})
        
        # Wait for recovery timeout
        await asyncio.sleep(RECOVERY_TIMEOUT + 1)
        
        # Next request succeeds (mock recovery)
        mock_post.side_effect = None
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"status": "success"}
        )
        
        # Should succeed and close circuit
        result = await call_orchestrator_api("/test", {})
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_circuit_breaker_fast_fail():
    """Test fast-fail when circuit is open."""
    
    # Open circuit
    with patch('httpx.AsyncClient.post', side_effect=httpx.HTTPError("Error")):
        for _ in range(FAILURE_THRESHOLD):
            try:
                await call_orchestrator_api("/test", {})
            except httpx.HTTPError:
                pass
    
    # Measure fast-fail time
    import time
    start = time.time()
    
    try:
        await call_orchestrator_api("/test", {})
    except CircuitBreakerError:
        pass
    
    duration = time.time() - start
    
    # Should fail in < 10ms (not 30s timeout)
    assert duration < 0.01, f"Fast-fail took {duration}s, expected < 0.01s"
```

### Integration Tests

```python
@pytest.mark.integration
async def test_circuit_breaker_with_real_service():
    """Test circuit breaker with real orchestrator."""
    
    # Start orchestrator
    orchestrator_proc = await start_orchestrator()
    
    try:
        # Make successful requests
        for _ in range(10):
            result = await call_orchestrator_api("/health", {})
            assert result["status"] == "ok"
        
        # Stop orchestrator (simulate failure)
        orchestrator_proc.kill()
        await asyncio.sleep(1)
        
        # Circuit should open after failures
        for i in range(FAILURE_THRESHOLD + 2):
            try:
                await call_orchestrator_api("/health", {})
            except (httpx.HTTPError, CircuitBreakerError) as e:
                if i >= FAILURE_THRESHOLD:
                    assert isinstance(e, CircuitBreakerError)
        
        # Restart orchestrator
        orchestrator_proc = await start_orchestrator()
        await asyncio.sleep(2)
        
        # Wait for recovery
        await asyncio.sleep(RECOVERY_TIMEOUT)
        
        # Should recover
        result = await call_orchestrator_api("/health", {})
        assert result["status"] == "ok"
        
    finally:
        orchestrator_proc.kill()
```

### Manual Testing

```bash
# Terminal 1: Start MCP server with circuit breaker
python -m shield_mcp_server

# Terminal 2: Start orchestrator
python -m shield_orchestrator

# Terminal 3: Make requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/mcp/crawl_web \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  sleep 1
done

# Stop orchestrator (Ctrl+C in Terminal 2)

# Continue making requests - should fail fast
for i in {1..10}; do
  time curl -X POST http://localhost:8000/mcp/crawl_web \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  sleep 1
done
# Note: Each request should return in < 100ms (not 30s)

# Check circuit breaker state
curl http://localhost:9090/metrics | grep circuit_breaker_state

# Restart orchestrator
python -m shield_orchestrator

# Wait 60 seconds for recovery timeout
sleep 60

# Make request - should succeed (circuit recovered)
curl -X POST http://localhost:8000/mcp/crawl_web \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## 🔧 TROUBLESHOOTING

### Problem: Circuit opens too frequently

**Symptoms**:
- Circuit opens during normal operation
- Services work but circuit stays open
- Frequent flapping between states

**Causes**:
- Threshold too low
- Transient errors counted as failures
- Network latency causing timeouts

**Solutions**:

1. **Increase failure threshold**:
   ```python
   @circuit(failure_threshold=10)  # Was 5
   ```

2. **Exclude transient errors**:
   ```python
   @circuit(
       failure_threshold=5,
       expected_exception=(httpx.ConnectError, httpx.TimeoutException)
       # Don't count HTTP 4xx as failures
   )
   ```

3. **Increase timeout**:
   ```python
   response = await http_client.post(url, json=data, timeout=60.0)  # Was 30
   ```

### Problem: Circuit never opens

**Symptoms**:
- Service is down but circuit stays closed
- Requests keep timing out (30s each)
- No fast-fail behavior

**Causes**:
- Circuit breaker not applied
- Exceptions not caught
- Wrong exception type

**Solutions**:

1. **Verify decorator applied**:
   ```python
   # Check function has _circuit_breaker attribute
   assert hasattr(call_orchestrator_api, '_circuit_breaker')
   ```

2. **Check exception handling**:
   ```python
   @circuit(expected_exception=httpx.HTTPError)  # Must match raised exception
   async def call_api():
       try:
           response = await http_client.post(url)
           response.raise_for_status()  # Raises HTTPError
       except Exception as e:
           # Don't catch here - let circuit breaker see it
           raise
   ```

3. **Enable debug logging**:
   ```python
   import logging
   logging.getLogger('circuitbreaker').setLevel(logging.DEBUG)
   ```

### Problem: Circuit never recovers

**Symptoms**:
- Circuit opened hours ago
- Service is back up
- Requests still fail with CircuitBreakerError

**Causes**:
- Recovery timeout too long
- Test request still failing
- Service actually still down

**Solutions**:

1. **Check service health**:
   ```bash
   curl http://orchestrator:8001/health
   ```

2. **Reduce recovery timeout**:
   ```python
   @circuit(recovery_timeout=30)  # Was 60
   ```

3. **Check logs for recovery attempts**:
   ```bash
   grep "half-open" logs/mcp-server.log
   grep "recovery" logs/mcp-server.log
   ```

4. **Manually reset circuit**:
   ```python
   # In Python REPL or admin endpoint
   call_orchestrator_api._circuit_breaker.call_succeeded()
   ```

### Problem: Fast-fail not working

**Symptoms**:
- Circuit is open but requests still slow
- Timeout still 30 seconds
- No performance improvement

**Causes**:
- CircuitBreakerError not caught
- Timeout happening before circuit check
- Multiple circuit breakers in chain

**Solutions**:

1. **Handle CircuitBreakerError properly**:
   ```python
   try:
       result = await call_orchestrator_api("/endpoint", data)
   except CircuitBreakerError:
       # Return immediately - don't retry or wait
       return {"status": "error", "error": "service_unavailable"}
   ```

2. **Don't wrap circuit breaker calls in retry logic**:
   ```python
   # BAD - retries defeat circuit breaker
   for attempt in range(3):
       try:
           result = await call_orchestrator_api("/endpoint", data)
           break
       except CircuitBreakerError:
           time.sleep(10)  # Waiting defeats fast-fail!
   
   # GOOD - fail immediately
   try:
       result = await call_orchestrator_api("/endpoint", data)
   except CircuitBreakerError:
       return error_response
   ```

---

## 📚 BEST PRACTICES

### 1. One Circuit Breaker Per Service

```python
# GOOD - Separate circuit breakers
@circuit(failure_threshold=5, recovery_timeout=60)
async def call_orchestrator():
    ...

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_qdrant():
    ...

# BAD - Single circuit breaker for multiple services
@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_service(service_url):
    ...  # Qdrant failure opens circuit for orchestrator too!
```

### 2. Appropriate Thresholds

```python
# Consider request rate and service stability
SERVICE_CONFIGS = {
    "critical_stable": {
        "failure_threshold": 10,    # High threshold
        "recovery_timeout": 120     # Long recovery
    },
    "critical_unstable": {
        "failure_threshold": 3,     # Low threshold
        "recovery_timeout": 30      # Fast recovery
    },
    "non_critical": {
        "failure_threshold": 1,     # Open immediately
        "recovery_timeout": 300     # Don't spam recovery
    }
}
```

### 3. Informative Error Messages

```python
except CircuitBreakerError:
    return {
        "status": "error",
        "error": "service_unavailable",
        "message": "Orchestrator service is temporarily unavailable",
        "retry_after": RECOVERY_TIMEOUT,
        "support_action": "If issue persists, contact support with this error code: CB_OPEN_001"
    }
```

### 4. Monitor and Alert

```python
# Always track circuit state
circuit_breaker_state.labels(service='orchestrator').set(state_value)

# Set up alerts
"""
- Alert if circuit open > 5 minutes (critical)
- Alert if circuit flaps > 3 times/hour (warning)
- Alert if failure rate > 10% (warning)
"""
```

### 5. Test Failure Scenarios

```python
# Include in CI/CD
async def test_circuit_breaker_scenarios():
    # Test: Service down
    # Test: Service slow
    # Test: Intermittent failures
    # Test: Recovery
    # Test: Multiple services
    pass
```

---

## 📖 REFERENCES

### Libraries

- **Python**: `circuitbreaker==1.4.0` ([PyPI](https://pypi.org/project/circuitbreaker/))
- **Alternatives**: `pybreaker`, `aiobreaker` (async-native)

### Patterns

- Martin Fowler: [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- Netflix Hystrix: [How It Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works)
- Microsoft Azure: [Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)

### Related Patterns

- **Retry Pattern**: Try again after transient failure
- **Timeout Pattern**: Limit waiting time
- **Bulkhead Pattern**: Isolate resources
- **Rate Limiting**: Control request rate

---

**Document Status**: ✅ **READY FOR IMPLEMENTATION**  
**Last Updated**: October 10, 2025  
**Next Review**: After Phase 1 completion

