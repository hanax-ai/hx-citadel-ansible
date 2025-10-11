# FastMCP Quick Reference Guide

**Target Server**: hx-mcp1-server (192.168.10.59)  
**Date**: October 9, 2025

---

## What is FastMCP?

FastMCP is a production-ready Python framework for building Model Context Protocol (MCP) servers that expose tools, resources, and prompts to LLMs.

Think of it as: **"API server, but specifically designed for LLM interactions"**

---

## Quick Facts

| Aspect | Details |
|--------|---------|
| **Language** | Python 3.10+ |
| **License** | Apache 2.0 |
| **Transports** | STDIO (local), HTTP (network), SSE (legacy) |
| **Auth** | Google, GitHub, Azure, Auth0, WorkOS, JWT, Bearer tokens |
| **Dependencies** | `uv` (recommended) or `pip` |
| **Production Ready** | ✅ Yes - includes auth, logging, health checks, metrics |

---

## Minimal Example

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("HX-Citadel MCP")

@mcp.tool
def query_knowledge(question: str) -> str:
    """Query the knowledge base"""
    return f"Answer to: {question}"

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
```

**Run it**:
```bash
python server.py
# Server at http://localhost:8000/mcp/
```

---

## Three Core Concepts

### 1. Tools (Functions LLMs Can Call)

```python
@mcp.tool
def process_data(input: str) -> dict:
    """Process and return data"""
    return {"result": f"Processed: {input}"}
```

### 2. Resources (Data Sources)

```python
@mcp.resource("config://version")
def get_version() -> str:
    return "1.0.0"
```

### 3. Prompts (Reusable Templates)

```python
@mcp.prompt
def summarize(text: str) -> str:
    return f"Please summarize: {text}"
```

---

## Deployment Options

### Option A: Direct HTTP (Simplest)

```python
mcp.run(transport="http", host="0.0.0.0", port=8000)
```

**Command**: `python server.py`

### Option B: ASGI (Production)

```python
app = mcp.http_app()
```

**Command**: `uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4`

### Option C: Config-Driven (Recommended for Ansible)

**fastmcp.json**:
```json
{
  "source": {"path": "server.py", "entrypoint": "mcp"},
  "environment": {
    "python": ">=3.10",
    "dependencies": ["fastmcp", "asyncpg", "redis"]
  },
  "deployment": {
    "transport": "http",
    "host": "0.0.0.0",
    "port": 8000,
    "log_level": "INFO"
  }
}
```

**Command**: `fastmcp run`

---

## HX-Citadel Integration Examples

### PostgreSQL Integration

```python
import asyncpg

@mcp.tool
async def query_db(sql: str) -> list:
    """Query PostgreSQL"""
    pool = await asyncpg.create_pool(
        "postgresql://postgres:Major8859!@hx-sqldb-server/citadel"
    )
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql)
    return [dict(row) for row in rows]
```

### Qdrant Vector Search

```python
from qdrant_client import AsyncQdrantClient

qdrant = AsyncQdrantClient(url="http://hx-vectordb-server:6333")

@mcp.tool
async def semantic_search(query: str) -> list:
    """Search vector database"""
    results = await qdrant.search(
        collection_name="knowledge_base",
        query_text=query,
        limit=10
    )
    return [{"id": r.id, "score": r.score} for r in results]
```

### Redis Caching

```python
import redis.asyncio as redis

redis_client = redis.from_url("redis://hx-vectordb-server:6379")

@mcp.tool
async def cached_lookup(key: str) -> str:
    """Lookup with caching"""
    cached = await redis_client.get(key)
    if cached:
        return cached.decode()
    # Compute and cache
    value = compute_value(key)
    await redis_client.set(key, value, ex=3600)
    return value
```

### Ollama LLM Integration

```python
import httpx

@mcp.tool
async def ask_llm(prompt: str, model: str = "llama2") -> str:
    """Query local LLM"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://hx-ollama1:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
    return response.json()["response"]
```

---

## Authentication Examples

### Bearer Token (Simple)

```python
from fastmcp.server.auth import BearerTokenAuth

auth = BearerTokenAuth(token="Major8859!")
mcp = FastMCP("Protected Server", auth=auth)
```

### OAuth2 with Google

```python
from fastmcp.server.auth import GoogleProvider

auth = GoogleProvider(
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    base_url="https://mcp.hana-x.ai"
)
mcp = FastMCP("Protected Server", auth=auth)
```

---

## Health Check & Metrics

```python
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({
        "status": "healthy",
        "service": "hx-mcp-server",
        "version": "1.0.0"
    })

@mcp.custom_route("/metrics", methods=["GET"])
async def metrics(request):
    return JSONResponse({
        "mcp_tools_called_total": 1234,
        "mcp_errors_total": 5
    })
```

---

## Systemd Service Template

```ini
[Unit]
Description=HX-Citadel MCP Server
After=network.target postgresql.service

[Service]
Type=simple
User=agent0
WorkingDirectory=/opt/hx-mcp-server
Environment="PATH=/opt/hx-mcp-server/.venv/bin"
ExecStart=/opt/hx-mcp-server/.venv/bin/fastmcp run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

---

## Testing Pattern

```python
import pytest
from fastmcp import FastMCP, Client

@pytest.fixture
def mcp_server():
    mcp = FastMCP("Test Server")
    
    @mcp.tool
    def add(a: int, b: int) -> int:
        return a + b
    
    return mcp

@pytest.mark.asyncio
async def test_add_tool(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("add", {"a": 5, "b": 3})
        assert result.content[0].text == "8"
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Python 3.10+ installed
- [ ] `uv` package manager installed
- [ ] Network access to databases (PostgreSQL, Redis, Qdrant)
- [ ] Network access to LLM nodes (Ollama)
- [ ] Firewall allows port 8000
- [ ] SSH access configured (✅ done)
- [ ] DNS resolution working (✅ done)

### Deployment
- [ ] Create `/opt/hx-mcp-server` directory
- [ ] Create virtual environment
- [ ] Install FastMCP: `uv pip install fastmcp`
- [ ] Deploy server code
- [ ] Deploy `fastmcp.json` configuration
- [ ] Create systemd service
- [ ] Enable and start service
- [ ] Test health endpoint
- [ ] Test MCP endpoint

### Post-Deployment
- [ ] Configure monitoring
- [ ] Set up log rotation
- [ ] Test from orchestrator
- [ ] Document tools and endpoints

---

## Essential Commands

```bash
# Install FastMCP
uv pip install fastmcp

# Run server (auto-detects fastmcp.json)
fastmcp run

# Run with explicit config
fastmcp run fastmcp.json

# Development mode with Inspector UI
fastmcp dev

# Check server capabilities
fastmcp inspect

# Production with Uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Common Patterns

### Logging with Context

```python
from fastmcp import Context

@mcp.tool
async def process(data: str, ctx: Context):
    await ctx.info(f"Processing {data}")
    try:
        result = do_work(data)
        await ctx.info("Success")
        return result
    except Exception as e:
        await ctx.error(f"Failed: {e}")
        raise
```

### Environment Variables

```python
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/db")
API_KEY = os.environ.get("API_KEY", "default-key")

@mcp.tool
def get_config() -> dict:
    return {
        "database": DATABASE_URL,
        "api_configured": bool(API_KEY)
    }
```

### Error Handling

```python
@mcp.tool
async def safe_operation(input: str) -> dict:
    """Operation with error handling"""
    try:
        result = await risky_operation(input)
        return {"status": "success", "data": result}
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        return {"status": "error", "message": "Internal error"}
```

---

## Key Takeaways

1. **FastMCP = MCP Server Framework** (like FastAPI but for LLM tools)
2. **Python 3.10+** required (Ubuntu 24.04 ✅)
3. **Three concepts**: Tools (functions), Resources (data), Prompts (templates)
4. **Three transports**: STDIO (local), HTTP (network), SSE (legacy)
5. **Production-ready**: Auth, logging, health checks, metrics built-in
6. **Config-driven**: `fastmcp.json` for declarative deployment
7. **Ansible-friendly**: Systemd service + config file deployment

---

## Resources

- **Full Review**: [FASTMCP-DEPLOYMENT-PREP.md](./FASTMCP-DEPLOYMENT-PREP.md)
- **Official Docs**: https://gofastmcp.com
- **GitHub**: https://github.com/jlowin/fastmcp
- **LLM Docs**: https://gofastmcp.com/llms-full.txt

---

**Ready to build deployment plan! ✅**
