# TASK-011: Test LightRAG E2E
## End-to-End Integration Test for lightrag_query()

**Date**: October 11, 2025  
**Tool**: `lightrag_query(query, mode, only_need_context)`  
**Status**: ✅ READY FOR TESTING

---

## Test Objective

Verify the complete RAG pipeline:
1. lightrag_query() forwards to orchestrator
2. Orchestrator processes with LightRAG
3. Returns relevant context and response
4. Supports all 4 retrieval modes
5. Circuit breaker protection works

---

## Test Cases

### Test 1: Hybrid Mode Query (Default)

**Input**:
```json
{
  "query": "What is machine learning?",
  "mode": "hybrid"
}
```

**Expected Output**:
```json
{
  "status": "success",
  "query": "What is machine learning?",
  "mode": "hybrid",
  "response": "Machine learning is...",
  "context": [
    {"text": "...", "score": 0.95, "source": "..."},
    {"text": "...", "score": 0.89, "source": "..."}
  ],
  "metadata": {
    "retrieval_time_ms": 1234,
    "context_count": 5
  }
}
```

**Validation**:
- Returns meaningful response
- Context array has relevant chunks
- Scores are sorted (highest first)
- metadata includes timing

---

### Test 2: Local Mode (Vector Search Only)

**Input**:
```json
{
  "query": "AI applications in healthcare",
  "mode": "local"
}
```

**Expected**:
- Uses vector similarity only
- Returns context from local knowledge base
- Faster than hybrid mode

---

### Test 3: Global Mode (Graph-based)

**Input**:
```json
{
  "query": "Explain neural networks",
  "mode": "global"
}
```

**Expected**:
- Uses graph-based retrieval
- Returns broader context
- May have different results than local

---

### Test 4: Naive Mode (Simple Retrieval)

**Input**:
```json
{
  "query": "Deep learning basics",
  "mode": "naive"
}
```

**Expected**:
- Simple similarity search
- Fast response
- Basic context without graph traversal

---

### Test 5: Context Only (No Generation)

**Input**:
```json
{
  "query": "Python programming",
  "mode": "hybrid",
  "only_need_context": true
}
```

**Expected Output**:
```json
{
  "status": "success",
  "query": "Python programming",
  "mode": "hybrid",
  "response": null,
  "context": [...],
  "metadata": {...}
}
```

**Validation**:
- response is null/empty
- context is populated
- Faster than full query (no LLM generation)

---

### Test 6: Invalid Mode

**Input**:
```json
{
  "query": "Test query",
  "mode": "invalid_mode"
}
```

**Expected Output**:
```json
{
  "status": "error",
  "error": "Invalid mode 'invalid_mode'. Valid modes: local, global, hybrid, naive",
  "error_type": "validation_error",
  "valid_modes": ["local", "global", "hybrid", "naive"]
}
```

---

### Test 7: Empty Query

**Input**:
```json
{
  "query": "",
  "mode": "hybrid"
}
```

**Expected**:
- Validation error
- "Query cannot be empty"

---

### Test 8: Circuit Breaker Protection

**Setup**: Stop orchestrator

**Input**:
```json
{
  "query": "Test query",
  "mode": "hybrid"
}
```

**Expected**:
- Fast-fail (< 100ms)
- Circuit breaker error
- retry_after=60

---

## End-to-End Workflow Test

**Complete RAG Pipeline**:

```
1. Ingest documents (TASK-005)
   └─> crawl_web("https://example.com")
   └─> ingest_doc("/tmp/test.pdf")

2. Wait for ingestion (check job_status)
   └─> get_job_status(job_id) until "completed"

3. Query knowledge base (TASK-011)
   └─> lightrag_query("summarize the documents", "hybrid")

4. Verify results
   └─> response contains information from ingested docs
   └─> context includes relevant chunks
```

---

## Monitoring

```bash
# Watch query logs
journalctl -u shield-mcp-server -f | grep lightrag_query

# Check orchestrator
curl http://hx-orchestrator-server:8000/health

# Monitor circuit breaker
watch -n 2 'curl -s http://hx-mcp1-server:8081/health | jq .circuit_breakers.orchestrator'
```

---

## Performance Targets

| Mode | Target Response Time | Notes |
|------|---------------------|-------|
| naive | < 2s | Simple retrieval |
| local | < 3s | Vector search |
| global | < 5s | Graph traversal |
| hybrid | < 7s | Combined approach |

---

## Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| All modes work | ✅ 4/4 | ⏸️ Pending |
| Returns response | ✅ Yes | ⏸️ Pending |
| Returns context | ✅ Yes | ⏸️ Pending |
| Invalid mode rejected | ✅ Error | ⏸️ Pending |
| Empty query rejected | ✅ Error | ⏸️ Pending |
| Circuit breaker works | ✅ Fast-fail | ⏸️ Pending |
| E2E workflow | ✅ Complete | ⏸️ Pending |

---

## Test Results

### Run #1
**Date**: TBD  
**Tester**: TBD  
**Results**: Pending MCP client and data ingestion

---

**Implementation**: ✅ Complete (~110 LOC)  
**Testing**: ⏸️ Pending MCP client + orchestrator  
**Depends On**: Orchestrator LightRAG service, Knowledge base populated

