# Actual Deployed Architecture & Configuration Analysis

**Date**: October 11, 2025
**Purpose**: Document the ACTUAL deployed architecture based on detailed codebase review
**Status**: Configuration mismatches identified and documented

---

## Executive Summary

✅ **All Services Are Deployed and Running**
⚠️ **Two Critical Misconfigurations Found**:
1. MCP Server pointing to wrong Ollama instance
2. Orchestrator embedding service pointing to wrong Ollama instance

---

## 1. Actual Ollama Deployment Topology

### Orchestrator Server (192.168.10.8) - **EMBEDDING MODELS**

**Service**: Ollama (localhost:11434)
**Purpose**: Embedding generation for RAG pipeline
**Status**: ✅ Active (running)

**Deployed Models** (3 embedding models):
```json
{
  "mxbai-embed-large:latest": {
    "size": "669 MB",
    "dimensions": 1024,
    "family": "bert",
    "parameter_size": "334M",
    "quantization": "F16"
  },
  "nomic-embed-text:latest": {
    "size": "274 MB",
    "dimensions": 768,
    "family": "nomic-bert",
    "parameter_size": "137M",
    "quantization": "F16"
  },
  "all-minilm:latest": {
    "size": "46 MB",
    "dimensions": 384,
    "family": "bert",
    "parameter_size": "23M",
    "quantization": "F16"
  }
}
```

**Architecture Rationale**: ✅ **CORRECT**
- Embedding models co-located with orchestrator for low latency
- Reduces network hops for frequent embedding operations
- Separation of concerns: embeddings vs LLM generation

---

### hx-ollama1 (192.168.10.50) - **LLM GENERATION**

**Service**: Ollama (11434)
**Purpose**: Primary LLM inference for text generation
**Status**: ✅ Active (running 1 week)

**Deployed Models** (3 LLMs):
```
- gemma3:27b      (Large general-purpose LLM)
- gpt-oss:20b     (Open source LLM)
- mistral:7b      (Fast inference LLM)
```

**No embedding models** - This is **by design** (dedicated LLM node)

---

### hx-ollama2 (192.168.10.52) - **SPECIALIZED MODELS**

**Service**: Ollama (11434)
**Purpose**: Secondary LLM node with specialized models
**Status**: ✅ Active (running 1 week)

**Deployed Models** (6 models):
```
- hx-cogito-3b:latest        (Small reasoning model)
- hx-qwen2.5-7b:latest       (Qwen LLM)
- hx-qwen3-coder-30b:latest  (Code generation)
- cogito:3b
- qwen3-coder:30b
- qwen2.5:7b
```

**No embedding models** - This is **by design** (specialized LLM node)

---

## 2. LiteLLM API Gateway (192.168.10.46:4000)

### Deployment Status
- **Service**: ✅ Active (running 1 week)
- **Port**: 4000
- **Purpose**: Unified API gateway for all LLM/embedding requests
- **Database**: PostgreSQL (hx-sqldb-server:5432/appdb)

### Configuration Analysis

**Deployed Config** (`/etc/litellm/litellm.yaml`):

```yaml
model_list:
  # ✅ Embedding Models → 192.168.10.8 (orchestrator)
  - model_name: mxbai-embed-large
    litellm_params:
      model: ollama/mxbai-embed-large:latest
      api_base: http://192.168.10.8:11434  # ✅ CORRECT

  - model_name: all-minilm
    litellm_params:
      model: ollama/all-minilm:latest
      api_base: http://192.168.10.8:11434  # ✅ CORRECT

  - model_name: nomic-embed-text
    litellm_params:
      model: ollama/nomic-embed-text:latest
      api_base: http://192.168.10.8:11434  # ✅ CORRECT

  # ✅ LLM Models → 192.168.10.50 (hx-ollama1)
  - model_name: mistral-7b
    litellm_params:
      model: ollama/mistral:7b
      api_base: http://192.168.10.50:11434  # ✅ CORRECT

  - model_name: gemma3-27b
    litellm_params:
      model: ollama/gemma3:27b
      api_base: http://192.168.10.50:11434  # ✅ CORRECT

  # ✅ Specialized Models → 192.168.10.52 (hx-ollama2)
  - model_name: qwen2.5-7b
    litellm_params:
      model: ollama/qwen2.5:7b
      api_base: http://192.168.10.52:11434  # ✅ CORRECT
```

**Verdict**: ✅ **LiteLLM configuration is 100% CORRECT**
- Embedding requests → orchestrator (192.168.10.8)
- LLM requests → dedicated nodes (192.168.10.50, 192.168.10.52)
- Proper routing and abstraction

---

## 3. Orchestrator (192.168.10.8:8000)

### Deployment Status
- **Service**: ✅ Active (running 50+ minutes)
- **Port**: 8000
- **Process**: uvicorn (PID 844822)
- **Health**: ✅ Healthy (uptime: 3028 seconds)

### Deployed Structure (39 Python modules):

```
/opt/hx-citadel-shield/orchestrator/
├── agents/                          # Pydantic AI Agents (4 modules)
│   ├── doc_process_coordinator.py
│   ├── query_router.py
│   └── web_crawl_coordinator.py
├── api/                             # FastAPI Endpoints (7 modules)
│   ├── health.py
│   ├── events.py
│   ├── jobs.py
│   ├── ingestion.py
│   ├── query.py
│   └── copilotkit.py
├── services/                        # Core Services (10 modules)
│   ├── embeddings.py               # ⚠️ MISCONFIGURED
│   ├── qdrant_client.py
│   ├── lightrag_service.py
│   ├── redis_streams.py
│   ├── event_bus.py
│   ├── job_tracker.py
│   ├── agent_manager.py
│   ├── copilotkit_adapter.py
│   ├── vector_search.py
│   └── workflow_manager.py
├── workers/                         # Async Workers (2 modules)
│   ├── worker_pool.py
│   └── lightrag_processor.py
├── workflows/                       # LangGraph Workflows (3 modules)
│   ├── ingestion_workflow.py
│   └── query_workflow.py
├── database/                        # PostgreSQL (3 modules)
│   ├── connection.py
│   ├── models.py
│   └── migrations/env.py
├── config/                          # Configuration (2 modules)
│   └── settings.py
├── utils/                           # Utilities (1 module)
│   └── logging_config.py
└── main.py                          # FastAPI Application
```

### ⚠️ MISCONFIGURATION #1: Orchestrator Embedding Service

**File**: `/opt/hx-citadel-shield/orchestrator/services/embeddings.py`

**Current Config** (Line 21):
```python
self.ollama_url = "http://192.168.10.50:11434"  # ❌ WRONG - points to hx-ollama1
```

**Problem**:
- Points to hx-ollama1 (192.168.10.50) which has NO embedding models
- Should point to localhost where embedding models ARE deployed

**Impact**:
- Embedding generation will FAIL with "model not found" error
- RAG pipeline cannot function
- Document ingestion will fail
- Vector search will fail

**Correct Configuration** (Option 1 - Direct):
```python
self.ollama_url = "http://localhost:11434"  # ✅ Local embedding models
# OR
self.ollama_url = "http://192.168.10.8:11434"  # ✅ Self-reference
```

**Correct Configuration** (Option 2 - Via LiteLLM - **RECOMMENDED**):
```python
self.litellm_url = "http://192.168.10.46:4000/v1/embeddings"  # ✅ Gateway abstraction
# Use LiteLLM's OpenAI-compatible API
```

---

## 4. MCP Server (192.168.10.59:8081)

### Deployment Status
- **Service**: ✅ Active
- **Port**: 8081
- **Tools**: 7 operational tools
- **Health**: ✅ Circuit breaker enabled

### ⚠️ MISCONFIGURATION #2: MCP Server Ollama URL

**File**: `/opt/fastmcp/shield/.env`

**Current Config**:
```bash
OLLAMA_BASE_URL=https://192.168.10.50:11434  # ❌ WRONG - points to hx-ollama1
```

**Problem**:
- Points to hx-ollama1 (192.168.10.50) which has NO embedding models
- MCP tools that use embeddings will FAIL

**Correct Configuration** (Option 1 - Direct):
```bash
OLLAMA_BASE_URL=http://192.168.10.8:11434  # ✅ Orchestrator (has embeddings)
```

**Correct Configuration** (Option 2 - Via LiteLLM - **RECOMMENDED**):
```bash
# Use LiteLLM gateway instead
LITELLM_BASE_URL=http://192.168.10.46:4000
# Then call: POST /chat/completions or /embeddings
```

---

## 5. Correct Architecture Diagram

### Current (Misconfigured) Flow:
```
┌─────────────────┐
│   MCP Server    │
│  192.168.10.59  │
│                 │──────┐
│ OLLAMA_BASE_URL │      │  ❌ Tries to get embeddings
│ 192.168.10.50   │      │     from hx-ollama1 (NO models)
└─────────────────┘      │
                         ▼
         ┌───────────────────────────┐
         │    hx-ollama1             │
         │    192.168.10.50          │
         │                           │
         │  Models:                  │
         │  - gemma3:27b             │
         │  - gpt-oss:20b            │
         │  - mistral:7b             │
         │                           │
         │  ❌ NO EMBEDDING MODELS   │
         └───────────────────────────┘

┌─────────────────────┐
│   Orchestrator      │
│   192.168.10.8      │
│                     │
│  embeddings.py:     │──────┐
│  ollama_url =       │      │  ❌ Also tries to get embeddings
│  192.168.10.50      │      │     from hx-ollama1 (NO models)
└─────────────────────┘      │
                             ▼
         ┌───────────────────────────┐
         │    hx-ollama1             │
         │    192.168.10.50          │
         │    ❌ NO EMBEDDING MODELS │
         └───────────────────────────┘
```

### Correct Architecture (Option 1 - Direct):
```
┌─────────────────┐
│   MCP Server    │
│  192.168.10.59  │
│                 │──────┐
│ OLLAMA_BASE_URL │      │  ✅ Get embeddings from
│ 192.168.10.8    │      │     orchestrator
└─────────────────┘      │
                         ▼
         ┌───────────────────────────────────┐
         │    Orchestrator + Local Ollama    │
         │    192.168.10.8:11434             │
         │                                   │
         │  Embedding Models:                │
         │  ✅ mxbai-embed-large (1024-dim)  │
         │  ✅ nomic-embed-text (768-dim)    │
         │  ✅ all-minilm (384-dim)          │
         └───────────────────────────────────┘

┌─────────────────────┐
│   Orchestrator      │
│   192.168.10.8      │
│                     │
│  embeddings.py:     │──────┐
│  ollama_url =       │      │  ✅ Use localhost
│  localhost:11434    │      │     (same server)
└─────────────────────┘      │
                             ▼
         ┌───────────────────────────────────┐
         │    Local Ollama                   │
         │    localhost:11434                │
         │  ✅ HAS EMBEDDING MODELS          │
         └───────────────────────────────────┘
```

### Correct Architecture (Option 2 - Via LiteLLM - **RECOMMENDED**):
```
┌─────────────────┐       ┌─────────────────────┐
│   MCP Server    │       │   Orchestrator      │
│  192.168.10.59  │       │   192.168.10.8      │
│                 │       │                     │
│ Use LiteLLM     │       │  embeddings.py:     │
│ for all calls   │       │  Use LiteLLM API    │
└────────┬────────┘       └──────────┬──────────┘
         │                           │
         │  ✅ Unified abstraction   │
         └──────────┬────────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │      LiteLLM Gateway    │
         │      192.168.10.46:4000 │
         │                         │
         │  ✅ Intelligent routing │
         │  ✅ Model abstraction   │
         │  ✅ Monitoring          │
         └────────┬────────────────┘
                  │
      ┌───────────┼───────────────┐
      │           │               │
      ▼           ▼               ▼
  ┌─────┐    ┌─────────┐    ┌─────────┐
  │ Emb │    │  LLM 1  │    │  LLM 2  │
  │.8   │    │  .50    │    │  .52    │
  └─────┘    └─────────┘    └─────────┘
```

---

## 6. Service Dependencies & Data Flow

### Document Ingestion Flow (Current - BROKEN):
```
1. User → MCP Server → crawl_web()
2. MCP Server → Orchestrator API → POST /ingestion
3. Orchestrator → embeddings.py → http://192.168.10.50:11434  ❌ FAIL
4. hx-ollama1 returns: "model 'mxbai-embed-large' not found"
5. Ingestion FAILS
```

### Document Ingestion Flow (Corrected):
```
1. User → MCP Server → crawl_web()
2. MCP Server → Orchestrator API → POST /ingestion
3. Orchestrator → embeddings.py → http://localhost:11434  ✅ SUCCESS
4. Local Ollama returns: [0.1, 0.2, ...] (1024-dim vector)
5. Orchestrator → Qdrant → store vector
6. Orchestrator → LightRAG → create knowledge graph
7. Return job_id to user
```

### Query Flow (Current - BROKEN):
```
1. User → MCP Server → lightrag_query()
2. MCP Server → Orchestrator API → POST /query
3. Orchestrator → embeddings.py → http://192.168.10.50:11434  ❌ FAIL
4. Query embedding generation FAILS
5. Vector search cannot proceed
```

### Query Flow (Corrected):
```
1. User → MCP Server → lightrag_query()
2. MCP Server → Orchestrator API → POST /query
3. Orchestrator → embeddings.py → http://localhost:11434  ✅ SUCCESS
4. Local Ollama returns query embedding
5. Orchestrator → Qdrant → vector search
6. Orchestrator → LightRAG → knowledge graph traversal
7. Return results to user
```

---

## 7. Testing Implications

### What This Means for TASK-032 (Unit Tests):

**Embedding Service Tests** (`test_orchestrator_embeddings.py`):
```python
# ✅ CORRECT - Mock the LOCAL Ollama endpoint
@pytest.fixture
def mock_ollama_client():
    """Mock LOCAL Ollama (localhost:11434 or 192.168.10.8:11434)"""
    mock = AsyncMock()
    mock.post.return_value.json.return_value = {
        "embedding": [0.1] * 1024,  # mxbai-embed-large dimensions
        "model": "mxbai-embed-large"
    }
    return mock

# Test should verify correct endpoint
def test_embedding_service_uses_local_ollama():
    service = EmbeddingService()
    # After fix, this should be localhost or 192.168.10.8
    assert "192.168.10.8" in service.ollama_url or "localhost" in service.ollama_url
```

**Integration Tests** (TASK-033):
```python
# Can test against ACTUAL deployed embedding models
async def test_real_embedding_generation():
    """Test against actual local Ollama on orchestrator"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "mxbai-embed-large", "prompt": "test"}
        )
        assert response.status_code == 200
        embedding = response.json()["embedding"]
        assert len(embedding) == 1024  # Verify dimensions
```

---

## 8. Action Items

### Immediate Fixes Required:

1. **Fix Orchestrator Embedding Service** (Priority: 🔴 CRITICAL)
   ```bash
   # File: roles/orchestrator_qdrant/templates/services/embeddings.py.j2
   # Line 21: Change from:
   self.ollama_url = "{{ ollama_url }}"  # Currently resolves to 192.168.10.50
   # To:
   self.ollama_url = "http://localhost:11434"  # Local embeddings
   ```

2. **Fix MCP Server Configuration** (Priority: 🔴 CRITICAL)
   ```bash
   # File: roles/fastmcp_server/templates/.env.j2
   # Change from:
   OLLAMA_BASE_URL=https://{{ hx_hosts_fqdn['hx-ollama1'] }}:11434
   # To:
   OLLAMA_BASE_URL=http://{{ hx_hosts_fqdn['hx-orchestrator-server'] }}:11434
   ```

3. **Redeploy Both Services**
   ```bash
   # Redeploy orchestrator
   ansible-playbook -i inventory/prod.ini playbooks/deploy-orchestrator-local.yml --tags qdrant

   # Redeploy MCP server
   ansible-playbook -i inventory/prod.ini playbooks/deploy-mcp-server.yml
   ```

4. **Verify Fixes**
   ```bash
   # Test embedding generation from orchestrator
   curl -X POST http://192.168.10.8:11434/api/embeddings \
     -H "Content-Type: application/json" \
     -d '{"model": "mxbai-embed-large", "prompt": "test"}' | jq '.embedding | length'
   # Expected: 1024

   # Test via orchestrator API
   curl -X POST http://192.168.10.8:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test query", "mode": "naive"}'
   ```

---

## 9. Corrected Test Coverage Plan

Based on **actual deployed architecture**:

### P0 Tests (Critical Path - 8-10 hours):

1. **Embedding Service** (12 tests) - **AFTER FIX**
   - Test localhost:11434 connectivity
   - Test mxbai-embed-large (1024-dim)
   - Test nomic-embed-text (768-dim)
   - Test all-minilm (384-dim)
   - Test batch processing
   - Test error handling

2. **LightRAG Service** (18 tests)
   - Query modes (naive, local, global, hybrid)
   - Knowledge graph integration
   - Qdrant vector storage
   - Document chunking

3. **Worker Pool** (25 tests)
   - Async task processing
   - Redis Streams integration
   - Graceful shutdown
   - Error handling

4. **Health Endpoints** (15 tests)
   - Basic health check
   - Detailed health with dependencies
   - Readiness probe
   - Liveness probe

5. **Job Tracker** (15 tests)
   - Job creation
   - Status updates
   - Progress tracking
   - Error handling

6. **Qdrant Client** (18 tests)
   - Vector search
   - Vector storage
   - Collection management
   - Connection pooling

**Total P0**: ~103 tests, 80%+ coverage

---

## 10. Summary & Key Learnings

### What I Learned from Detailed Review:

✅ **Architecture is SOUND**:
- Embedding models co-located with orchestrator (low latency)
- LLM models on dedicated nodes (resource separation)
- LiteLLM provides unified gateway (abstraction layer)

⚠️ **Configuration Errors**:
- 2 services pointing to wrong Ollama instance
- Both fixable with template changes

✅ **All Services Operational**:
- Orchestrator: Running, healthy
- LiteLLM: Running, correctly configured
- MCP Server: Running, needs config fix
- Ollama instances: All running with correct models

### User Feedback Was Correct:

> "the embeeding models are not missing, they are on the ochetsration server, you are oprtaing with partial information"

**You were absolutely right**. I should have:
1. Checked ALL Ollama instances (not just dedicated LLM nodes)
2. Reviewed LiteLLM configuration first (it had the correct topology)
3. Examined deployed orchestrator code (showed the misconfiguration)
4. Not made assumptions about where models "should" be

**Enterprise-level systems require detailed investigation, not high-level assumptions.**

---

**Document Version**: 1.0
**Created**: October 11, 2025
**Last Updated**: October 11, 2025
**Status**: Awaiting configuration fixes from user
**Next**: Update test coverage plan based on corrected architecture
