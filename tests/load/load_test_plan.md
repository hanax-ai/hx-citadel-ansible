# Load Test Plan - TASK-019
## Circuit Breaker Behavior Under Load

**Date**: October 11, 2025  
**Component**: Shield MCP Server with Circuit Breaker  
**Objective**: Validate circuit breaker opens/closes correctly under failure scenarios

---

## Test Scenarios

### Scenario 1: Normal Load (Circuit CLOSED)
**Objective**: Baseline performance with healthy orchestrator

**Setup**:
- Orchestrator running and healthy
- Circuit breaker in CLOSED state
- 100 concurrent requests over 60 seconds

**Expected Results**:
- All requests succeed
- Circuit remains CLOSED
- Response time < 5s (p95)
- No circuit breaker errors

**Command**:
```bash
# Requires MCP load testing tool
python3 scripts/load_test.py \
  --server hx-mcp1-server:8081 \
  --tool lightrag_query \
  --concurrency 10 \
  --duration 60 \
  --expect-success
```

---

### Scenario 2: Gradual Failures (Circuit Opens)
**Objective**: Verify circuit opens after fail_max=5 failures

**Setup**:
- Stop orchestrator: `systemctl stop orchestrator-api`
- Circuit breaker in CLOSED state
- Send requests until circuit opens

**Expected Results**:
- First 5 requests fail with orchestrator_error (30s timeout each)
- 6th request fails instantly with circuit_breaker_error (< 1ms)
- Circuit state = OPEN
- fail_counter = 5

**Test Steps**:
```bash
# 1. Stop orchestrator
ssh hx-orchestrator-server "sudo systemctl stop orchestrator-api"

# 2. Invoke tool 5 times (slowly to avoid race conditions)
for i in {1..5}; do
  echo "Request $i..."
  time python3 scripts/invoke_mcp_tool.py \
    --server hx-mcp1-server:8081 \
    --tool lightrag_query \
    --args '{"query": "test", "mode": "hybrid"}'
  sleep 2
done

# 3. Check circuit state
curl http://hx-mcp1-server:8081/health | jq '.circuit_breakers.orchestrator'
# Expected: {"state": "open", "fail_counter": 5}

# 4. Invoke again - should fail instantly
echo "Testing fast-fail..."
time python3 scripts/invoke_mcp_tool.py \
  --server hx-mcp1-server:8081 \
  --tool lightrag_query \
  --args '{"query": "test", "mode": "hybrid"}'
# Expected: < 100ms response with "circuit breaker open" error
```

---

### Scenario 3: Recovery (Half-Open → Closed)
**Objective**: Verify circuit recovers when orchestrator comes back

**Setup**:
- Circuit in OPEN state (from Scenario 2)
- Wait 60 seconds for reset_timeout
- Start orchestrator

**Expected Results**:
- After 60s, circuit moves to HALF_OPEN
- First request succeeds → circuit moves to CLOSED
- Subsequent requests succeed normally
- fail_counter resets to 0

**Test Steps**:
```bash
# 1. Wait for reset timeout
echo "Waiting 60 seconds for half-open state..."
sleep 60

# 2. Start orchestrator
ssh hx-orchestrator-server "sudo systemctl start orchestrator-api"
sleep 5  # Allow orchestrator to stabilize

# 3. Send test request
echo "Sending recovery request..."
python3 scripts/invoke_mcp_tool.py \
  --server hx-mcp1-server:8081 \
  --tool lightrag_query \
  --args '{"query": "test", "mode": "hybrid"}'

# 4. Check circuit closed
curl http://hx-mcp1-server:8081/health | jq '.circuit_breakers.orchestrator'
# Expected: {"state": "closed", "fail_counter": 0}
```

---

### Scenario 4: High Load with Failures
**Objective**: Verify circuit breaker protects under heavy load

**Setup**:
- Orchestrator DOWN
- 50 concurrent requests
- Circuit should open quickly

**Expected Results**:
- First 5 requests timeout (30s each)
- Remaining 45 requests fail fast (< 1ms each)
- Total test time < 3 minutes (not 25 minutes if no circuit breaker)
- Circuit opens and stays OPEN

**Command**:
```bash
# Simulate high load with down orchestrator
python3 scripts/load_test.py \
  --server hx-mcp1-server:8081 \
  --tool lightrag_query \
  --concurrency 50 \
  --requests 50 \
  --orchestrator-down \
  --expect-circuit-open

# Measure performance improvement
# Without circuit breaker: 50 * 30s = 1500s (25 minutes)
# With circuit breaker: 5 * 30s + 45 * 0.001s = ~150s (2.5 minutes)
# Improvement: 10x faster failure handling
```

---

### Scenario 5: Flapping Protection
**Objective**: Verify circuit doesn't flap with intermittent failures

**Setup**:
- Orchestrator unstable (random 50% failure rate)
- 100 requests over 2 minutes
- Circuit should stabilize in OPEN

**Expected Results**:
- Circuit opens after 5 failures
- Stays OPEN even with occasional successes
- Prevents resource exhaustion
- Most requests fail fast

---

## Load Testing Tools Required

### Option 1: Python MCP Load Tester
```python
# scripts/load_test.py (to be created)
"""
MCP protocol load testing tool
- Supports concurrent requests
- Measures response times
- Tracks circuit breaker state
- Generates performance reports
"""
```

### Option 2: Locust (HTTP Load Testing)
```python
# locustfile.py
from locust import HttpUser, task, between
import json

class MCPUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def query_lightrag(self):
        # Would need MCP protocol support
        pass
```

### Option 3: Manual Testing
```bash
# Simple bash script for basic testing
for i in {1..10}; do
  # Invoke MCP tool via client
  echo "Request $i"
  time <mcp_client_command>
  sleep 1
done
```

---

## Success Criteria

| Criterion | Target | Method |
|-----------|--------|--------|
| Circuit opens after failures | 5 failures | Count errors before fast-fail |
| Fast-fail response time | < 100ms | Time circuit_breaker_error responses |
| Reset timeout | 60 seconds | Measure time to half-open |
| Recovery on success | 1 success | Verify transition to closed |
| Resource protection | No exhaustion | Monitor memory/CPU during failures |
| Concurrent requests | Handles 50+ | Load test with concurrency |

---

## Performance Metrics

### Baseline (No Circuit Breaker)
- **Failed Request Time**: 30-60s (timeout)
- **50 Failed Requests**: ~25 minutes
- **Resource Usage**: High (blocked threads)
- **User Experience**: Very poor

### With Circuit Breaker
- **Failed Request Time**: < 1ms (after circuit opens)
- **50 Failed Requests**: ~2.5 minutes (5 timeouts + 45 fast-fails)
- **Resource Usage**: Low (fast-fail)
- **User Experience**: Much better (fast feedback)

**Improvement**: **10x faster** failure handling

---

## Test Execution Log

### Test Run #1 - Static Validation
**Date**: 2025-10-11  
**Status**: ✅ PASS

- Service running: ✅
- PyBreaker installed: ✅
- Circuit configured: ✅
- Wrapper protecting calls: ✅
- Metrics exposed: ✅

### Test Run #2 - Dynamic Validation
**Date**: TBD  
**Status**: ⏸️ PENDING (orchestrator access required)

**Prerequisites**:
- Orchestrator server accessible
- MCP client tool available
- Permission to stop/start orchestrator

**When Ready**:
1. Run Scenario 2 (failure simulation)
2. Run Scenario 3 (recovery)
3. Run Scenario 4 (high load)
4. Document results here

---

## Monitoring During Tests

### Logs to Monitor
```bash
# MCP Server logs
journalctl -u shield-mcp-server -f

# Watch for circuit breaker events
journalctl -u shield-mcp-server -f | grep -E '(circuit_breaker|orchestrator)'

# Circuit breaker state
watch -n 5 'curl -s http://hx-mcp1-server:8081/health | jq .circuit_breakers.orchestrator'
```

### Metrics to Track
- Circuit breaker state transitions
- fail_counter increments
- Response times (fast-fail vs timeout)
- Error types (orchestrator_error vs circuit_breaker_error)
- Memory/CPU usage during failures

---

## Current Status

✅ **Circuit Breaker Implementation**: COMPLETE  
✅ **Static Validation**: PASS  
⏸️ **Dynamic Load Testing**: PENDING (orchestrator access)

**Recommendation**: Mark TASK-019 as complete with documented test plan. Execute dynamic tests during integration phase when orchestrator is available.

---

**Created**: 2025-10-11  
**Task**: TASK-019  
**Sprint**: 1.2 Circuit Breakers  
**Status**: ✅ Implementation Complete, Testing Documented

