# FastMCP Deployment Preparation - Technical Review

**Date**: October 9, 2025  
**Reviewer**: GitHub Copilot  
**Purpose**: Prepare for MCP Server deployment on hx-mcp1-server (192.168.10.59)

---

## Executive Summary

FastMCP is a production-ready Python framework for building Model Context Protocol (MCP) servers. It provides the standard way to expose tools, resources, and prompts to LLMs. The framework extends the official MCP SDK with enterprise features including authentication, deployment tools, testing utilities, and comprehensive client libraries.

### Key Takeaways for Deployment

1. **Python 3.10+ Required** - Modern Python with async/await support
2. **Multiple Transport Options** - STDIO (local), HTTP (network), SSE (legacy)
3. **Production-Ready** - Built-in auth, logging, error handling, health checks
4. **Dependency Management** - Uses `uv` for fast, reliable package management
5. **Configuration-Driven** - `fastmcp.json` for declarative server setup

---

## 1. Technology Stack

### Core Dependencies

From `pyproject.toml`:

```toml
[project]
name = "fastmcp"
requires-python = ">=3.10"

dependencies = [
    "python-dotenv>=1.1.0",      # Environment variable management
    "exceptiongroup>=1.2.2",     # Enhanced exception handling
    "httpx>=0.28.1",             # HTTP client for async requests
    "mcp>=1.12.4,<2.0.0",        # Official MCP SDK (FastMCP 1.0 was merged here)
    "openapi-pydantic>=0.5.1",   # OpenAPI schema support
    "rich>=13.9.4",              # Beautiful terminal output
    "cyclopts>=3.0.0",           # CLI framework
    "authlib>=1.5.2",            # OAuth/OIDC authentication
    "pydantic[email]>=2.11.7",   # Data validation
    "pyperclip>=1.9.0",          # Clipboard operations
    "openapi-core>=0.19.5",      # OpenAPI validation
    "websockets>=15.0.1",        # WebSocket support
]
```

### System Requirements

- **Python**: 3.10, 3.11, or 3.12
- **OS**: Linux (Ubuntu 24.04 on hx-mcp1-server)
- **Package Manager**: `uv` (recommended) or `pip`
- **Network**: HTTP transport requires open port (default: 8000)

---

## 2. Architecture Overview

### FastMCP Server Structure

```python
from fastmcp import FastMCP

# Create server instance
mcp = FastMCP("Server Name")

# Define tools (functions LLMs can call)
@mcp.tool
def process_data(input: str) -> str:
    """Process and return data"""
    return f"Processed: {input}"

# Define resources (data sources for LLM context)
@mcp.resource("config://version")
def get_version() -> str:
    return "1.0.0"

# Define prompts (reusable templates)
@mcp.prompt
def summarize(text: str) -> str:
    return f"Please summarize: {text}"

# Run the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
```

### Transport Protocols

1. **STDIO** (Default)
   - Standard input/output communication
   - Process spawned per client session
   - Perfect for desktop apps (Claude Desktop)
   - Single-user, local execution

2. **HTTP** (Recommended for Production)
   - Network-accessible via URL
   - Multiple concurrent clients
   - Full bidirectional communication
   - RESTful endpoint at `/mcp/`

3. **SSE** (Legacy)
   - Server-Sent Events
   - Backward compatibility only
   - Limited to server→client streaming
   - **Not recommended for new deployments**

---

## 3. Deployment Patterns

### Option A: Direct HTTP Server (Simplest)

**Use Case**: Standalone MCP server, quick deployment

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("HX-Citadel MCP")

@mcp.tool
def query_database(query: str) -> dict:
    """Query the knowledge base"""
    # Implementation here
    return {"result": "data"}

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",      # Listen on all interfaces
        port=8000,
        path="/mcp/"         # Endpoint URL
    )
```

**Deployment**:
```bash
python server.py
```

**Pros**: 
- Minimal configuration
- FastMCP handles all HTTP details
- Quick to deploy and test

**Cons**:
- Single process (no multi-worker support)
- Limited scalability
- No advanced server features

---

### Option B: ASGI Application (Production)

**Use Case**: Production deployment, multiple workers, integration with existing services

```python
# app.py
from fastmcp import FastMCP
import os

mcp = FastMCP("HX-Citadel MCP")

@mcp.tool
def query_database(query: str) -> dict:
    """Query the knowledge base"""
    return {"result": "data"}

# Create ASGI application
app = mcp.http_app(path="/mcp/")
```

**Deployment with Uvicorn**:
```bash
# Install uvicorn with performance extras
pip install 'uvicorn[standard]'

# Run with multiple workers
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

# Or with environment-based configuration
MCP_LOG_LEVEL=INFO uvicorn app:app --host 0.0.0.0 --port 8000
```

**Pros**:
- Multi-worker support for concurrency
- Production-grade ASGI server
- Better performance and reliability
- Can integrate with existing FastAPI/Starlette apps

**Cons**:
- Requires ASGI server (Uvicorn/Gunicorn)
- Slightly more complex setup

---

### Option C: Configuration-Driven (Recommended)

**Use Case**: Team deployment, reproducible environments, multi-environment support

**server.py**:
```python
from fastmcp import FastMCP

mcp = FastMCP("HX-Citadel MCP")

@mcp.tool
def query_database(query: str) -> dict:
    """Query the knowledge base"""
    return {"result": "data"}
```

**fastmcp.json**:
```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": {
    "path": "server.py",
    "entrypoint": "mcp"
  },
  "environment": {
    "type": "uv",
    "python": ">=3.10",
    "dependencies": [
      "fastmcp",
      "asyncpg",
      "redis",
      "httpx"
    ]
  },
  "deployment": {
    "transport": "http",
    "host": "0.0.0.0",
    "port": 8000,
    "path": "/mcp/",
    "log_level": "INFO",
    "env": {
      "DATABASE_URL": "postgresql://user:pass@hx-sqldb-server/citadel",
      "REDIS_URL": "redis://hx-vectordb-server:6379",
      "ENVIRONMENT": "production"
    }
  }
}
```

**Deployment**:
```bash
# Simple - FastMCP handles everything
fastmcp run

# Or with explicit config file
fastmcp run fastmcp.json

# Development mode with Inspector UI
fastmcp dev

# Production with pre-built environment
fastmcp project prepare fastmcp.json --output-dir ./env
fastmcp run --project ./env
```

**Pros**:
- Single source of truth for configuration
- Environment-specific configs (dev, staging, prod)
- Automatic dependency management
- Portable across systems
- CLI integration

**Cons**:
- Requires learning JSON configuration schema
- Additional file to maintain

---

## 4. Authentication & Security

### Built-in Authentication Providers

FastMCP provides production-ready authentication:

```python
from fastmcp import FastMCP
from fastmcp.server.auth import GoogleProvider, GitHubProvider, BearerTokenAuth

# OAuth2 with Google
auth = GoogleProvider(
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    base_url="https://mcp.hana-x.ai"
)

# OAuth2 with GitHub
auth = GitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    base_url="https://mcp.hana-x.ai"
)

# Simple Bearer Token (for development)
auth = BearerTokenAuth(token="Major8859!")

mcp = FastMCP("Protected Server", auth=auth)
```

### Supported Auth Methods

1. **OAuth2/OIDC**:
   - Google
   - GitHub
   - Microsoft Azure AD
   - Auth0
   - WorkOS (SSO)
   - Descope

2. **Token-Based**:
   - Bearer tokens
   - JWT tokens
   - API keys

3. **Client Auto-Auth**:
   ```python
   # Client automatically handles OAuth flow
   async with Client("https://mcp.hana-x.ai/mcp", auth="oauth") as client:
       result = await client.call_tool("protected_tool")
   ```

### Security Best Practices

1. **Always use authentication for remote servers**
2. **Never hardcode secrets** - use environment variables
3. **Use HTTPS in production** (reverse proxy with nginx/caddy)
4. **Implement rate limiting** (via middleware or reverse proxy)
5. **Log security events** (auth failures, suspicious patterns)

---

## 5. Integration with HX-Citadel Infrastructure

### Database Integration

```python
import asyncpg
from fastmcp import FastMCP, Context

mcp = FastMCP("HX-Citadel MCP")

# PostgreSQL connection pool
DB_DSN = "postgresql://postgres:Major8859!@hx-sqldb-server:5432/citadel"

async def get_db_pool():
    return await asyncpg.create_pool(DB_DSN)

@mcp.tool
async def query_knowledge_base(query: str, ctx: Context) -> dict:
    """Query the PostgreSQL knowledge base"""
    await ctx.info(f"Executing query: {query}")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
        return {"rows": [dict(row) for row in rows]}
```

### Vector Database Integration (Qdrant)

```python
from qdrant_client import AsyncQdrantClient
from fastmcp import FastMCP

mcp = FastMCP("HX-Citadel MCP")

# Qdrant client
qdrant = AsyncQdrantClient(url="http://hx-vectordb-server:6333")

@mcp.tool
async def semantic_search(query: str, limit: int = 10) -> list:
    """Semantic search in vector database"""
    results = await qdrant.search(
        collection_name="knowledge_base",
        query_text=query,
        limit=limit
    )
    return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]
```

### Redis Caching Integration

```python
import redis.asyncio as redis
from fastmcp import FastMCP

mcp = FastMCP("HX-Citadel MCP")

# Redis connection
redis_client = redis.from_url("redis://hx-vectordb-server:6379")

@mcp.tool
async def cached_lookup(key: str) -> str:
    """Lookup value with Redis caching"""
    cached = await redis_client.get(key)
    if cached:
        return cached.decode()
    
    # Compute value if not cached
    value = f"Computed: {key}"
    await redis_client.set(key, value, ex=3600)  # 1 hour TTL
    return value
```

### LLM Integration (Ollama)

```python
import httpx
from fastmcp import FastMCP, Context

mcp = FastMCP("HX-Citadel MCP")

OLLAMA_URL = "http://hx-ollama1:11434"

@mcp.tool
async def ask_llm(prompt: str, model: str = "llama2", ctx: Context) -> str:
    """Query local Ollama LLM"""
    await ctx.info(f"Asking {model}: {prompt[:50]}...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
        return response.json()["response"]
```

---

## 6. Monitoring & Observability

### Health Checks

```python
from fastmcp import FastMCP
from starlette.responses import JSONResponse
import asyncpg

mcp = FastMCP("HX-Citadel MCP")

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for load balancers"""
    health_status = {
        "status": "healthy",
        "service": "hx-mcp-server",
        "version": "1.0.0"
    }
    
    # Check database connectivity
    try:
        pool = await asyncpg.create_pool("postgresql://...")
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return JSONResponse(health_status)

@mcp.custom_route("/metrics", methods=["GET"])
async def metrics(request):
    """Prometheus-compatible metrics"""
    return JSONResponse({
        "mcp_tools_called_total": 1234,
        "mcp_errors_total": 5,
        "mcp_active_connections": 3
    })
```

### Logging with Context

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("HX-Citadel MCP")

@mcp.tool
async def process_document(doc_id: str, ctx: Context) -> dict:
    """Process document with detailed logging"""
    
    # Log to MCP client (visible in Claude, etc.)
    await ctx.info(f"Processing document {doc_id}")
    
    try:
        # Processing logic
        result = {"doc_id": doc_id, "status": "processed"}
        
        await ctx.info("Processing completed successfully")
        return result
        
    except Exception as e:
        await ctx.error(f"Processing failed: {str(e)}")
        raise
```

---

## 7. Testing Strategy

### Unit Tests

```python
import pytest
from fastmcp import FastMCP, Client

@pytest.fixture
def mcp_server():
    mcp = FastMCP("Test Server")
    
    @mcp.tool
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b
    
    return mcp

@pytest.mark.asyncio
async def test_add_tool(mcp_server):
    """Test tool execution"""
    async with Client(mcp_server) as client:
        result = await client.call_tool("add", {"a": 5, "b": 3})
        assert result.content[0].text == "8"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_database_integration():
    """Test database connectivity"""
    mcp = FastMCP("Test Server")
    
    @mcp.tool
    async def query_db() -> dict:
        pool = await asyncpg.create_pool("postgresql://...")
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
        return {"result": result}
    
    async with Client(mcp) as client:
        result = await client.call_tool("query_db", {})
        assert result.content[0].json_data["result"] == 1
```

---

## 8. Deployment Checklist for hx-mcp1-server

### Pre-Deployment

- [ ] **Python 3.10+ installed** on hx-mcp1-server
- [ ] **uv package manager** installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] **Network access** to:
  - hx-sqldb-server (PostgreSQL)
  - hx-vectordb-server (Qdrant, Redis)
  - hx-ollama1, hx-ollama2 (LLM nodes)
- [ ] **Firewall rules** allow port 8000 (or chosen port)
- [ ] **SSH ed25519 key** configured (already done)
- [ ] **DNS/hosts resolution** working (already done)

### Deployment Steps

1. **Create project directory**:
   ```bash
   ssh agent0@192.168.10.59
   mkdir -p /opt/hx-mcp-server
   cd /opt/hx-mcp-server
   ```

2. **Create virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install FastMCP**:
   ```bash
   uv pip install fastmcp
   ```

4. **Deploy server code** (via Ansible)
   - Copy `server.py`
   - Copy `fastmcp.json`
   - Copy any additional modules

5. **Configure systemd service**:
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

6. **Enable and start service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable hx-mcp-server
   sudo systemctl start hx-mcp-server
   ```

7. **Verify deployment**:
   ```bash
   # Check service status
   systemctl status hx-mcp-server
   
   # Check health endpoint
   curl http://localhost:8000/health
   
   # Test MCP endpoint
   curl http://localhost:8000/mcp/
   ```

### Post-Deployment

- [ ] **Configure monitoring** (Prometheus metrics)
- [ ] **Set up log rotation** for service logs
- [ ] **Test from remote client** (from hx-orchestrator-server)
- [ ] **Document endpoints** and tools in wiki
- [ ] **Set up backup** for configuration files

---

## 9. Ansible Role Structure (Proposed)

```
roles/fastmcp/
├── defaults/
│   └── main.yml              # Default variables
├── files/
│   └── fastmcp.json.j2       # Config template
├── handlers/
│   └── main.yml              # Service restart handlers
├── tasks/
│   ├── main.yml              # Main task orchestration
│   ├── install.yml           # Install uv and fastmcp
│   ├── configure.yml         # Deploy config files
│   └── service.yml           # Systemd service setup
├── templates/
│   ├── fastmcp-server.service.j2  # Systemd unit
│   ├── server.py.j2          # Server code template
│   └── env.j2                # Environment variables
└── vars/
    └── main.yml              # Role variables
```

### Key Variables

```yaml
# defaults/main.yml
fastmcp_version: "latest"
fastmcp_install_dir: "/opt/hx-mcp-server"
fastmcp_user: "agent0"
fastmcp_port: 8000
fastmcp_host: "0.0.0.0"
fastmcp_log_level: "INFO"

# Database connections
fastmcp_db_host: "hx-sqldb-server"
fastmcp_db_port: 5432
fastmcp_db_name: "citadel"
fastmcp_db_user: "postgres"
fastmcp_db_password: "{{ vault_postgresql_password }}"

# Vector database
fastmcp_qdrant_url: "http://hx-vectordb-server:6333"
fastmcp_redis_url: "redis://hx-vectordb-server:6379"

# LLM nodes
fastmcp_ollama_urls:
  - "http://hx-ollama1:11434"
  - "http://hx-ollama2:11434"
```

---

## 10. Next Steps & Recommendations

### Immediate Actions (When You Return)

1. **Review this document** - Confirm deployment approach
2. **Define MCP tools** - What capabilities should the server expose?
3. **Design server.py** - Implement tools, resources, prompts
4. **Create Ansible role** - Automate deployment with best practices
5. **Test locally** - Validate on dev-test environment first
6. **Deploy to hx-mcp1-server** - Use safe deployment framework

### Deployment Approach Recommendation

**Recommended: Option C (Configuration-Driven)**

**Why:**
- ✅ Aligns with Ansible best practices
- ✅ Declarative, version-controlled configuration
- ✅ Easy to manage multiple environments
- ✅ FastMCP CLI handles dependency management
- ✅ Portable across team members
- ✅ Consistent with HX-Citadel standards

### Questions to Answer Before Deployment

1. **What tools should the MCP server expose?**
   - Knowledge base queries?
   - Document processing?
   - LLM interactions?
   - System monitoring?

2. **Authentication strategy?**
   - Internal-only (no auth)?
   - Bearer token for orchestrator?
   - OAuth for external access?

3. **Integration priorities?**
   - PostgreSQL knowledge base?
   - Qdrant vector search?
   - Ollama LLM access?
   - All of the above?

4. **Resource limits?**
   - Max concurrent connections?
   - Rate limiting?
   - Memory constraints?

5. **Backup and disaster recovery?**
   - Configuration backup strategy?
   - Service recovery procedures?
   - Data persistence requirements?

---

## 11. Reference Links

- **Official Documentation**: https://gofastmcp.com
- **GitHub Repository**: https://github.com/jlowin/fastmcp
- **LLM-friendly docs**: https://gofastmcp.com/llms-full.txt
- **MCP Protocol Spec**: https://modelcontextprotocol.io
- **PyPI Package**: https://pypi.org/project/fastmcp

---

## Conclusion

FastMCP provides a production-ready, Pythonic framework for building MCP servers. The technology stack aligns well with HX-Citadel infrastructure:

- ✅ Python 3.10+ (matches Ubuntu 24.04)
- ✅ Async/await (modern Python patterns)
- ✅ HTTP transport (network-accessible)
- ✅ Enterprise auth (OAuth2, JWT, tokens)
- ✅ Configuration-driven (Ansible-friendly)
- ✅ Database integration (PostgreSQL, Redis, Qdrant)
- ✅ Production-ready (logging, health checks, metrics)

**Ready to build deployment plan when you return from break.** 🚀
