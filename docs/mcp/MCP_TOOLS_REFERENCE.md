# MCP Tools Reference
## Shield MCP Server - Complete API Documentation

**Version**: 1.0  
**Last Updated**: October 10, 2025  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Tools Reference](#tools-reference)
   - [crawl_web](#1-crawl_web)
   - [ingest_doc](#2-ingest_doc)
   - [qdrant_find](#3-qdrant_find)
   - [qdrant_store](#4-qdrant_store)
   - [lightrag_query](#5-lightrag_query)
   - [health_check](#6-health_check)
4. [Error Handling](#error-handling)
5. [Best Practices](#best-practices)
6. [Examples](#examples)

---

## Overview

The Shield MCP Server provides 6 production-grade tools for AI-powered knowledge management:

| Tool | Purpose | Async | Dependencies |
|------|---------|-------|--------------|
| **crawl_web** | Web crawling and ingestion | ✅ HTTP 202 | Crawl4AI, Orchestrator |
| **ingest_doc** | Document processing | ✅ HTTP 202 | Docling, Orchestrator |
| **qdrant_find** | Semantic vector search | ❌ Direct | Qdrant, Ollama |
| **qdrant_store** | Vector storage | ❌ Direct | Qdrant, Ollama |
| **lightrag_query** | Hybrid knowledge retrieval | ❌ Direct | Orchestrator |
| **health_check** | System health monitoring | ❌ Direct | All services |

### Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Shield MCP Server  │
│                     │
│ ┌─────────────────┐ │
│ │   crawl_web()   │──→ Orchestrator (HTTP 202)
│ │   ingest_doc()  │──→ Orchestrator (HTTP 202)
│ │                 │ │
│ │ qdrant_find()   │──→ Qdrant + Ollama
│ │ qdrant_store()  │──→ Qdrant + Ollama
│ │                 │ │
│ │lightrag_query() │──→ Orchestrator
│ └─────────────────┘ │
└─────────────────────┘
```

---

## Quick Start

### Prerequisites

- Shield Orchestrator running on `http://192.168.10.8:8000`
- Qdrant vector database running
- Ollama embedding service running
- Python 3.11+ environment

### Basic Usage

```python
from fastmcp import FastMCP

mcp = FastMCP.from_server("shield-mcp-server")

# Example: Crawl a website
result = await mcp.call_tool("crawl_web", {
    "url": "https://example.com",
    "max_pages": 10
})

# Example: Search knowledge base
results = await mcp.call_tool("lightrag_query", {
    "query": "What is machine learning?",
    "mode": "hybrid"
})
```

---

## Tools Reference

### 1. crawl_web()

**Purpose**: Crawl websites and send content for async ingestion into knowledge base

**Signature**:
```python
async def crawl_web(
    url: str,
    max_pages: int = 10,
    allowed_domains: Optional[List[str]] = None,
    max_depth: int = 2
) -> dict
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | ✅ Yes | - | Starting URL to crawl |
| `max_pages` | integer | ❌ No | 10 | Maximum number of pages to crawl |
| `allowed_domains` | list[string] | ❌ No | Same as URL domain | List of allowed domains to crawl |
| `max_depth` | integer | ❌ No | 2 | Maximum crawl depth |

**Returns** (HTTP 202 Pattern):
```json
{
  "status": "accepted",
  "message": "Web crawl initiated for https://example.com",
  "job_id": "job_abc123",
  "pages_crawled": 5,
  "source_url": "https://example.com",
  "check_status_endpoint": "/jobs/job_abc123"
}
```

**Features**:
- ✅ Async web crawling with Crawl4AI
- ✅ Multi-page support with link extraction
- ✅ Domain filtering to prevent external crawling
- ✅ Graceful error handling (403, 404, timeouts)
- ✅ 30s timeout per page
- ✅ Orchestrator integration for async ingestion

**Example**:
```python
# Basic crawl
result = await mcp.call_tool("crawl_web", {
    "url": "https://docs.python.org"
})

# Advanced crawl with restrictions
result = await mcp.call_tool("crawl_web", {
    "url": "https://example.com",
    "max_pages": 50,
    "allowed_domains": ["example.com", "docs.example.com"],
    "max_depth": 3
})

# Check job status later
status = await orchestrator.get(f"/jobs/{result['job_id']}")
```

**Error Types**:
- `validation_error`: Invalid URL format
- `http_error`: HTTP errors (403, 404, etc.)
- `timeout_error`: Crawl timeout
- `orchestrator_error`: Orchestrator ingestion failed

---

### 2. ingest_doc()

**Purpose**: Process documents (PDF, DOCX, TXT, MD) and send for async ingestion

**Signature**:
```python
async def ingest_doc(
    file_path: str,
    source_name: Optional[str] = None
) -> dict
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | string | ✅ Yes | - | Path to document file |
| `source_name` | string | ❌ No | Filename | Optional name for the source |

**Supported Formats**:
- ✅ PDF (`.pdf`)
- ✅ Microsoft Word (`.docx`, `.doc`)
- ✅ Plain Text (`.txt`)
- ✅ Markdown (`.md`)

**Returns** (HTTP 202 Pattern):
```json
{
  "status": "accepted",
  "message": "Document ingestion initiated for report.pdf",
  "job_id": "job_def456",
  "source_name": "report.pdf",
  "file_format": ".pdf",
  "content_length": 15243,
  "page_count": 10,
  "check_status_endpoint": "/jobs/job_def456"
}
```

**Features**:
- ✅ Multi-format document processing with Docling
- ✅ Automatic format detection
- ✅ Metadata extraction (title, page count, etc.)
- ✅ Markdown export for unified format
- ✅ File validation (exists, readable, correct type)
- ✅ Orchestrator integration for async ingestion

**Example**:
```python
# Basic document ingestion
result = await mcp.call_tool("ingest_doc", {
    "file_path": "/path/to/report.pdf"
})

# With custom source name
result = await mcp.call_tool("ingest_doc", {
    "file_path": "/data/Q3_Report.docx",
    "source_name": "Q3 Financial Report"
})
```

**Error Types**:
- `file_not_found`: File doesn't exist
- `invalid_path`: Path is not a file
- `unsupported_format`: File format not supported
- `corrupted_file`: File is corrupted or invalid
- `conversion_failed`: Document conversion failed
- `orchestrator_error`: Orchestrator ingestion failed

---

### 3. qdrant_find()

**Purpose**: Search vectors in Qdrant using semantic similarity

**Signature**:
```python
async def qdrant_find(
    query: str,
    collection: Optional[str] = None,
    limit: int = 10,
    score_threshold: float = 0.0,
    filter_conditions: Optional[dict] = None
) -> dict
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | Search query text |
| `collection` | string | ❌ No | `shield_knowledge_base` | Qdrant collection name |
| `limit` | integer | ❌ No | 10 | Number of results to return |
| `score_threshold` | float | ❌ No | 0.0 | Minimum similarity score (0.0-1.0) |
| `filter_conditions` | dict | ❌ No | None | Optional metadata filters |

**Returns**:
```json
{
  "status": "success",
  "query": "machine learning",
  "collection": "shield_knowledge_base",
  "result_count": 5,
  "results": [
    {
      "id": "point_123",
      "score": 0.92,
      "payload": {
        "text": "Machine learning is...",
        "source": "ml_guide.pdf",
        "page": 1
      }
    }
  ],
  "score_threshold": 0.0,
  "embedding_model": "nomic-embed-text"
}
```

**Features**:
- ✅ Semantic search via embeddings
- ✅ Automatic embedding generation (Ollama)
- ✅ Filter support for metadata
- ✅ Score threshold filtering
- ✅ Pagination with configurable limit
- ✅ Auto collection detection

**Example**:
```python
# Basic search
results = await mcp.call_tool("qdrant_find", {
    "query": "How does photosynthesis work?"
})

# Advanced search with filters
results = await mcp.call_tool("qdrant_find", {
    "query": "quantum computing",
    "collection": "tech_knowledge",
    "limit": 20,
    "score_threshold": 0.7,
    "filter_conditions": {
        "source_type": "research_paper",
        "year": 2024
    }
})
```

**Error Types**:
- `embedding_error`: Ollama embedding generation failed
- `collection_not_found`: Qdrant collection doesn't exist
- `http_error`: Qdrant API error

---

### 4. qdrant_store()

**Purpose**: Store text with embeddings in Qdrant

**Signature**:
```python
async def qdrant_store(
    text: str,
    metadata: Optional[dict] = None,
    collection: Optional[str] = None,
    point_id: Optional[str] = None
) -> dict
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | ✅ Yes | - | Text to embed and store |
| `metadata` | dict | ❌ No | None | Optional metadata dictionary |
| `collection` | string | ❌ No | `shield_knowledge_base` | Qdrant collection name |
| `point_id` | string | ❌ No | Auto-generated UUID | Specific ID for the point |

**Returns**:
```json
{
  "status": "success",
  "message": "Vector stored successfully in collection 'shield_knowledge_base'",
  "point_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection": "shield_knowledge_base",
  "embedding_dimension": 768,
  "embedding_model": "nomic-embed-text",
  "payload_keys": ["text", "created_at", "embedding_model", "source", "category"]
}
```

**Features**:
- ✅ Upsert operation (create or update)
- ✅ Automatic embedding generation
- ✅ Metadata merging (user + system)
- ✅ Auto collection creation if not exists
- ✅ UUID generation for point IDs
- ✅ Timestamp tracking

**Example**:
```python
# Basic storage
result = await mcp.call_tool("qdrant_store", {
    "text": "The Earth orbits around the Sun in approximately 365 days."
})

# Storage with metadata
result = await mcp.call_tool("qdrant_store", {
    "text": "Quantum entanglement is a phenomenon where...",
    "metadata": {
        "source": "quantum_physics_textbook",
        "chapter": 5,
        "topic": "quantum_mechanics",
        "difficulty": "advanced"
    },
    "collection": "physics_knowledge"
})

# Storage with custom ID
result = await mcp.call_tool("qdrant_store", {
    "text": "Important fact to remember",
    "point_id": "my-custom-id-123",
    "metadata": {"priority": "high"}
})
```

**Error Types**:
- `embedding_error`: Ollama embedding generation failed
- `http_error`: Qdrant API error

---

### 5. lightrag_query()

**Purpose**: Query knowledge base using LightRAG hybrid retrieval

**Signature**:
```python
async def lightrag_query(
    query: str,
    mode: str = "hybrid",
    only_need_context: bool = False
) -> dict
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | The query text |
| `mode` | string | ❌ No | `hybrid` | Retrieval mode |
| `only_need_context` | boolean | ❌ No | False | Return only context without response |

**Retrieval Modes**:

| Mode | Description | Use Case | Speed |
|------|-------------|----------|-------|
| `naive` | Simple vector search | Quick lookups | ⚡ Fastest |
| `local` | Local entity-based retrieval | Entity-focused queries | 🔥 Fast |
| `global` | Global community-based retrieval | Broad context queries | 🐢 Slower |
| `hybrid` | Combined approach | **Recommended - Best results** | ⚖️ Balanced |

**Returns**:
```json
{
  "status": "success",
  "query": "What is machine learning?",
  "mode": "hybrid",
  "response": "Machine learning is a subset of artificial intelligence...",
  "context": [
    {
      "text": "Machine learning algorithms...",
      "score": 0.95,
      "source": "ml_textbook.pdf"
    }
  ],
  "metadata": {
    "retrieval_time_ms": 234,
    "sources_count": 3
  }
}
```

**Features**:
- ✅ LightRAG hybrid retrieval integration
- ✅ Multiple retrieval modes (naive, local, global, hybrid)
- ✅ Mode validation with clear errors
- ✅ Context-only queries
- ✅ 60s timeout for complex queries
- ✅ Orchestrator forwarding

**Example**:
```python
# Basic query (hybrid mode)
result = await mcp.call_tool("lightrag_query", {
    "query": "Explain neural networks"
})

# Specific mode
result = await mcp.call_tool("lightrag_query", {
    "query": "Who invented the transistor?",
    "mode": "local"  # Entity-focused
})

# Context only (no response generation)
result = await mcp.call_tool("lightrag_query", {
    "query": "quantum computing applications",
    "mode": "hybrid",
    "only_need_context": True
})
```

**Error Types**:
- `validation_error`: Invalid mode selection
- `orchestrator_error`: Orchestrator query failed
- `timeout_error`: Query timeout (60s)

---

### 6. health_check()

**Purpose**: Comprehensive health check of MCP server and dependencies

**Signature**:
```python
async def health_check() -> dict
```

**Parameters**: None

**Returns**:
```json
{
  "overall_status": "healthy",
  "services": {
    "orchestrator": {
      "status": "up",
      "url": "http://192.168.10.8:8000",
      "response_time_ms": 45
    },
    "qdrant": {
      "status": "up",
      "collections": 3
    },
    "ollama": {
      "status": "up",
      "models": ["nomic-embed-text"]
    }
  },
  "timestamp": "2025-10-10T12:34:56Z"
}
```

**Example**:
```python
health = await mcp.call_tool("health_check", {})
if health["overall_status"] == "healthy":
    print("All systems operational")
```

---

## Error Handling

### Error Response Format

All tools return consistent error responses:

```json
{
  "status": "error",
  "error": "Detailed error message",
  "error_type": "specific_error_type"
}
```

### Common Error Types

| Error Type | Description | Retry? |
|------------|-------------|--------|
| `validation_error` | Invalid input parameters | ❌ Fix input |
| `file_not_found` | File doesn't exist | ❌ Check path |
| `unsupported_format` | File format not supported | ❌ Convert file |
| `corrupted_file` | File is corrupted | ❌ Fix file |
| `http_error` | HTTP API error | ✅ Retry |
| `timeout_error` | Operation timeout | ✅ Retry |
| `orchestrator_error` | Orchestrator unavailable | ✅ Retry |
| `embedding_error` | Embedding generation failed | ✅ Retry |
| `collection_not_found` | Qdrant collection missing | ❌ Create collection |
| `unknown_error` | Unexpected error | ✅ Retry + Report |

### Error Handling Example

```python
try:
    result = await mcp.call_tool("crawl_web", {"url": "https://example.com"})
    
    if result["status"] == "error":
        error_type = result["error_type"]
        
        if error_type in ["http_error", "timeout_error", "orchestrator_error"]:
            # Retry logic
            await asyncio.sleep(5)
            result = await mcp.call_tool("crawl_web", {"url": "https://example.com"})
        else:
            # Log and handle
            logger.error(f"Crawl failed: {result['error']}")
            
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

---

## Best Practices

### 1. Async Operations (HTTP 202 Pattern)

For `crawl_web()` and `ingest_doc()`:

```python
# Step 1: Initiate async operation
result = await mcp.call_tool("crawl_web", {"url": "https://example.com"})
job_id = result["job_id"]

# Step 2: Poll for status
import asyncio

async def wait_for_job(job_id, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        status = await orchestrator.get(f"/jobs/{job_id}")
        if status["state"] in ["completed", "failed"]:
            return status
        await asyncio.sleep(2)
    raise TimeoutError("Job timed out")

final_status = await wait_for_job(job_id)
```

### 2. Batch Operations

For storing multiple items:

```python
# Store multiple items
texts = ["Text 1", "Text 2", "Text 3"]

for text in texts:
    await mcp.call_tool("qdrant_store", {
        "text": text,
        "metadata": {"batch_id": "batch_001"}
    })
```

### 3. Search Optimization

```python
# Use score threshold to filter low-quality results
results = await mcp.call_tool("qdrant_find", {
    "query": "machine learning",
    "score_threshold": 0.7,  # Only high-quality matches
    "limit": 5
})

# Use filters to narrow search
results = await mcp.call_tool("qdrant_find", {
    "query": "quantum computing",
    "filter_conditions": {
        "source_type": "research_paper",
        "year": 2024,
        "reviewed": True
    }
})
```

### 4. Mode Selection (LightRAG)

```python
# Use appropriate mode for query type
queries = [
    ("Who is the CEO of Apple?", "local"),       # Entity query
    ("What are AI trends?", "global"),            # Broad context
    ("Explain transformers", "hybrid"),           # Best overall
    ("Quick fact check", "naive")                 # Fast lookup
]

for query, mode in queries:
    result = await mcp.call_tool("lightrag_query", {
        "query": query,
        "mode": mode
    })
```

### 5. Health Monitoring

```python
# Check health before critical operations
health = await mcp.call_tool("health_check", {})

if health["overall_status"] != "healthy":
    # Wait for services
    await asyncio.sleep(10)
    health = await mcp.call_tool("health_check", {})
    
if health["overall_status"] == "healthy":
    # Proceed with operations
    pass
```

---

## Examples

### Complete Workflow: Ingest and Query

```python
# 1. Crawl a website
crawl_result = await mcp.call_tool("crawl_web", {
    "url": "https://docs.python.org/3/tutorial/",
    "max_pages": 20
})
crawl_job_id = crawl_result["job_id"]

# 2. Ingest a document
doc_result = await mcp.call_tool("ingest_doc", {
    "file_path": "/data/python_guide.pdf",
    "source_name": "Python Complete Guide"
})
doc_job_id = doc_result["job_id"]

# 3. Wait for jobs to complete
await wait_for_job(crawl_job_id)
await wait_for_job(doc_job_id)

# 4. Query the knowledge base
query_result = await mcp.call_tool("lightrag_query", {
    "query": "How do I use decorators in Python?",
    "mode": "hybrid"
})

print(query_result["response"])
```

### Vector Storage Pipeline

```python
# Extract text from various sources
texts = [
    "Python is a high-level programming language.",
    "Machine learning is a subset of AI.",
    "Quantum computing uses quantum mechanics."
]

# Store with metadata
for idx, text in enumerate(texts):
    await mcp.call_tool("qdrant_store", {
        "text": text,
        "metadata": {
            "index": idx,
            "category": "definitions",
            "verified": True
        }
    })

# Search stored vectors
results = await mcp.call_tool("qdrant_find", {
    "query": "What is AI?",
    "score_threshold": 0.6
})
```

### Multi-Format Document Processing

```python
# Process various document types
documents = [
    "/data/report.pdf",
    "/data/presentation.pptx",  # Will fail - not supported
    "/data/notes.txt",
    "/data/README.md"
]

for doc_path in documents:
    try:
        result = await mcp.call_tool("ingest_doc", {
            "file_path": doc_path
        })
        
        if result["status"] == "accepted":
            print(f"✅ Processing {doc_path}: {result['job_id']}")
        else:
            print(f"❌ Failed {doc_path}: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error {doc_path}: {e}")
```

---

## Configuration

### Environment Variables

Required environment variables:

```bash
# Orchestrator
ORCHESTRATOR_BASE_URL=http://192.168.10.8:8000

# Qdrant
QDRANT_URL=http://qdrant-server:6333
QDRANT_API_KEY=your-api-key  # Optional for local
QDRANT_COLLECTION=shield_knowledge_base

# Ollama
OLLAMA_BASE_URL=http://ollama-server:11434
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768

# MCP Server
FASTMCP_PORT=8080
```

### Collection Setup (Qdrant)

Collections are auto-created by `qdrant_store()`, but you can pre-create:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url="http://qdrant-server:6333")

client.create_collection(
    collection_name="shield_knowledge_base",
    vectors_config=VectorParams(
        size=768,  # nomic-embed-text dimension
        distance=Distance.COSINE
    )
)
```

---

## Troubleshooting

### Common Issues

**1. Orchestrator Connection Failed**
```
Error: "Orchestrator ingestion failed: 502"
Solution: Check orchestrator is running: curl http://192.168.10.8:8000/health
```

**2. Embedding Generation Timeout**
```
Error: "Failed to generate embedding: timeout"
Solution: Check Ollama service: curl http://ollama-server:11434/api/tags
```

**3. Collection Not Found**
```
Error: "Collection 'shield_knowledge_base' not found"
Solution: Use qdrant_store() to auto-create or manually create collection
```

**4. File Not Found**
```
Error: "File not found: /path/to/doc.pdf"
Solution: Use absolute paths and verify file exists
```

**5. Invalid Mode**
```
Error: "Invalid mode 'hybird'. Must be one of: naive, local, global, hybrid"
Solution: Check mode spelling (common: hybird → hybrid)
```

---

## Performance

### Benchmarks (Approximate)

| Operation | Avg Time | Notes |
|-----------|----------|-------|
| `crawl_web` (10 pages) | 30-45s | Async (HTTP 202) |
| `ingest_doc` (PDF, 50 pages) | 5-10s | Async (HTTP 202) |
| `qdrant_find` | 100-300ms | Includes embedding generation |
| `qdrant_store` | 200-400ms | Includes embedding generation |
| `lightrag_query` (hybrid) | 1-3s | Includes LLM generation |
| `health_check` | 50-100ms | Parallel checks |

### Optimization Tips

1. **Batch Operations**: Group multiple stores together
2. **Caching**: Cache frequently used embeddings
3. **Score Threshold**: Use to reduce result processing
4. **Mode Selection**: Use `naive` for speed, `hybrid` for quality
5. **Async Jobs**: Don't wait synchronously for HTTP 202 jobs

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-10 | Initial production release |

---

**📚 For more information, see:**
- [Deployment Guide](./DEPLOYMENT-GUIDE.md)
- [Architecture Overview](./SHIELD-MASTER-ARCHITECTURE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

**🔗 Related Services:**
- Shield Orchestrator API: http://192.168.10.8:8000/docs
- Qdrant Dashboard: http://qdrant-server:6333/dashboard
- Ollama Models: http://ollama-server:11434/api/tags



