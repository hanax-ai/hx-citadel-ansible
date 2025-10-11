# Orchestrator Server Deployment Plan
## HX-Citadel Shield Intelligence Hub - Complete Tech Stack Installation

**Date:** October 9, 2025  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Deployment Method:** Ansible Automation  
**Timeline:** 2-3 weeks for complete deployment  
**Status:** Planning Phase - Ready for Approval

---

## Executive Summary

This deployment plan covers the complete installation and configuration of the **Shield Orchestrator Server** (Intelligence Hub) using Ansible automation. The Orchestrator is the brain of the Shield architecture, coordinating:

- **LightRAG Engine** (hybrid Knowledge Graph + Vector retrieval)
- **LangGraph Workflows** (multi-step agent coordination)
- **Pydantic AI Agents** (type-safe agent definitions)
- **Redis Streams Event Bus** (durable event delivery)
- **Worker Pool** (asynchronous task processing)
- **CopilotKit Adapter** (HITL integration)

**Complexity:** High  
**Risk:** Medium (multiple integrated components)  
**Dependencies:** MCP Server, Qdrant, PostgreSQL, Redis, Ollama

---

## Table of Contents

1. [Tech Stack Outline](#1-tech-stack-outline)
2. [Configuration and Integration](#2-configuration-and-integration)
3. [Deployment Roadmap](#3-deployment-roadmap)
4. [Individual Component Plans](#4-individual-component-plans)
5. [Testing and Validation](#5-testing-and-validation)
6. [Success Criteria](#6-success-criteria)

---

## 1. Tech Stack Outline

### **1.1 Core Framework Stack**

#### **Layer 4: Orchestration Server (Intelligence Hub)**

```yaml
Server: hx-orchestrator-server
IP: 192.168.10.8
FQDN: hx-orchestrator-server.dev-test.hana-x.ai
OS: Ubuntu Server 24.04.2 LTS
Python: 3.12.3
Port: 8000 (FastAPI main application)

Purpose:
  • LightRAG Knowledge Graph + Vector Hybrid Retrieval
  • LangGraph multi-step workflow coordination
  • Pydantic AI agent definitions
  • Redis Streams event bus (durable delivery)
  • Async worker pool (task processing)
  • CopilotKit adapter (HITL integration)
  • AG-UI event streaming (WebSocket/SSE)
```

---

### **1.2 Complete Technology Stack**

#### **🔧 Component 1: LightRAG Engine**

**Repository:** `tech_kb/LightRAG-main`  
**Version:** 0.10+ (from pyproject.toml)  
**Purpose:** Hybrid retrieval (Knowledge Graph + Vector Search)

**Core Dependencies:**
```yaml
Package: lightrag-hku
Python: >=3.10 (we use 3.12)

Required Dependencies:
  • aiohttp                      # Async HTTP client
  • configparser                 # Configuration management
  • python-dotenv                # Environment variables
  • json_repair                  # JSON parsing/repair
  • nano-vectordb                # Lightweight vector DB (fallback)
  • networkx                     # Graph algorithms
  • numpy                        # Numerical operations
  • pandas>=2.0.0                # Data manipulation
  • pydantic                     # Data validation
  • pypinyin                     # Chinese NLP (optional)
  • tenacity                     # Retry logic
  • tiktoken                     # Token counting
  • xlsxwriter>=3.1.0            # Export capabilities

API Dependencies (for orchestrator):
  • fastapi                      # REST API framework
  • uvicorn                      # ASGI server
  • aiofiles                     # Async file I/O
  • asyncpg                      # PostgreSQL async driver
  • httpx                        # HTTP client
  • python-multipart             # File uploads
  • PyJWT                        # JWT tokens
  • python-jose[cryptography]    # JWT encryption
  • passlib[bcrypt]              # Password hashing
  • psutil                       # System monitoring

Integration:
  • Qdrant Client (vector storage)
  • PostgreSQL (KG storage via asyncpg)
  • OpenAI-compatible API (Ollama via LiteLLM)
```

---

#### **🔧 Component 2: LangGraph Workflows**

**Repository:** `tech_kb/` (reference from CopilotKit/ottomator-agents)  
**Package:** `langgraph`  
**Purpose:** Multi-step agent coordination and state management

**Dependencies:**
```yaml
Package: langgraph
Version: Latest stable

Core Dependencies:
  • langchain-core               # LangChain abstractions
  • langchain-community          # Community integrations
  • langchain-openai             # OpenAI/compatible LLM
  • pydantic                     # State models

Integration:
  • LightRAG (knowledge retrieval)
  • Redis (state persistence)
  • PostgreSQL (checkpoint storage)
```

---

#### **🔧 Component 3: Pydantic AI Agents**

**Repository:** Reference implementation in `source/rag_agent.py`  
**Package:** `pydantic-ai`  
**Purpose:** Type-safe agent definitions

**Dependencies:**
```yaml
Package: pydantic-ai
Version: Latest stable

Core Dependencies:
  • pydantic>=2.0                # Data validation
  • typing-extensions            # Type hints

Integration:
  • FastAPI (REST endpoints)
  • LightRAG (knowledge access)
  • LangGraph (workflow coordination)
```

---

#### **🔧 Component 4: Redis Streams Event Bus**

**Purpose:** Durable event delivery (at-least-once semantics)

**Dependencies:**
```yaml
Package: redis[hiredis]
Version: >=5.0.0

Features Required:
  • Redis Streams support
  • Consumer groups
  • XREADGROUP command
  • Event replay capability

Integration:
  • Shield MCP Server (event producers)
  • AG-UI frontends (event consumers)
  • Worker pool (task queue)
```

---

#### **🔧 Component 5: Worker Pool (Async Processing)**

**Purpose:** Background task processing for LightRAG ingestion

**Dependencies:**
```yaml
Framework: FastAPI + Background Tasks
Alternative: Celery (if needed for distributed workers)

Core Dependencies:
  • asyncio                      # Async coordination
  • aioredis                     # Redis async client
  • structlog                    # Structured logging

Integration:
  • Redis Streams (task queue)
  • LightRAG (chunk processing)
  • PostgreSQL (job tracking)
```

---

#### **🔧 Component 6: FastAPI Application Framework**

**Purpose:** REST API server and WebSocket/SSE endpoints

**Dependencies:**
```yaml
Package: fastapi
Version: >=0.115.0

Core Dependencies:
  • fastapi                      # Web framework
  • uvicorn[standard]>=0.30.0    # ASGI server
  • pydantic>=2.0                # Request/response models
  • python-multipart             # File uploads
  • sse-starlette>=2.0.0         # Server-Sent Events
  • websockets>=15.0.1           # WebSocket support

Middleware:
  • slowapi                      # Rate limiting
  • python-jose[cryptography]    # JWT auth
  • passlib[bcrypt]              # Password hashing
```

---

#### **🔧 Component 7: Database Clients**

**Purpose:** PostgreSQL (KG storage) and Redis (event bus)

**Dependencies:**
```yaml
PostgreSQL:
  • asyncpg>=0.29.0              # Async PostgreSQL driver
  • sqlalchemy[asyncio]>=2.0.0   # ORM (optional)
  • alembic>=1.13.0              # Database migrations

Redis:
  • redis[hiredis]>=5.0.0        # Redis client with C parser
  • aioredis>=2.0.0              # Async Redis client (if needed)

Qdrant:
  • qdrant-client>=1.7.0         # Vector DB client
```

---

#### **🔧 Component 8: CopilotKit Adapter**

**Purpose:** HITL integration for shield-power-ui

**Dependencies:**
```yaml
Integration Type: Custom FastAPI adapter

Dependencies:
  • fastapi                      # REST endpoints
  • sse-starlette                # State streaming
  • pydantic                     # Data models

Reference:
  • tech_kb/CopilotKit-main/     # Integration patterns
  • useCopilotReadable patterns
  • useCopilotAction patterns
```

---

#### **🔧 Component 9: Monitoring and Observability**

**Purpose:** Prometheus metrics, structured logging, health checks

**Dependencies:**
```yaml
Monitoring:
  • prometheus-client>=0.20.0    # Metrics
  • opentelemetry-api>=1.20.0    # Tracing
  • opentelemetry-sdk>=1.20.0    # Tracing SDK
  • opentelemetry-instrumentation-fastapi  # FastAPI tracing

Logging:
  • structlog>=24.0.0            # Structured logging
  • python-json-logger           # JSON formatter

Health:
  • httpx                        # Health check dependencies
```

---

#### **🔧 Component 10: Additional Utilities**

```yaml
Utilities:
  • pyyaml>=6.0                  # YAML parsing
  • python-dateutil              # Date utilities
  • pytz                         # Timezone handling
  • click>=8.0.0                 # CLI tools
  • rich>=13.9.4                 # Terminal formatting

Security:
  • cryptography>=42.0.0         # Encryption
  • bcrypt>=4.0.0                # Password hashing
  • python-jose[cryptography]    # JWT
```

---

### **1.3 System Dependencies**

```yaml
APT Packages (Ubuntu 24.04):
  • python3.12, python3.12-venv, python3.12-dev
  • python3-pip
  • build-essential
  • libpq-dev                    # PostgreSQL client
  • libssl-dev                   # SSL/TLS
  • libffi-dev                   # Foreign function interface
  • redis-tools                  # Redis CLI
  • postgresql-client            # PostgreSQL CLI
  • curl, wget, git, jq
```

---

## 2. Configuration and Integration

### **2.1 Server Specifications**

```yaml
Hardware:
  CPU: 8 cores minimum, 16 recommended
  RAM: 16GB minimum, 32GB recommended
  Storage: 200GB SSD minimum, 500GB recommended
  Network: 1Gbps minimum

Directories:
  Application: /opt/hx-citadel-shield/orchestrator
  Logs: /var/log/hx-citadel/orchestrator
  Virtual Environment: /opt/hx-citadel-shield/orchestrator-venv
  Data: /opt/hx-citadel-shield/data
  Config: /opt/hx-citadel-shield/orchestrator/config
```

---

### **2.2 Fleet Integration**

```yaml
Upstream Dependencies:
  Qdrant Vector DB:
    Host: 192.168.10.9:6333
    Protocol: HTTPS (self-signed cert)
    API Key: {{ vault_qdrant_api_key }}
    Collection: hx_corpus_v1
    Status: ✅ Operational

  PostgreSQL:
    Host: 192.168.10.48:5432
    Database: shield_orchestrator
    User: orchestrator
    Password: {{ vault_postgres_orchestrator_password }}
    Status: ✅ Operational

  Redis:
    Host: 192.168.10.48:6379
    Streams: shield:ingestion_queue, shield:events
    Consumer Groups: lightrag-workers
    Status: ✅ Operational

  Ollama LLM:
    Primary: 192.168.10.50:11434 (hx-ollama1)
    Secondary: 192.168.10.52:11434 (hx-ollama2)
    Models Required:
      • mxbai-embed-large (embeddings)
      • llama3.2:latest (entity extraction)
      • qwen2.5:latest (fallback)
    Status: ✅ Operational

  LiteLLM Proxy:
    Host: 192.168.10.46:4000
    Endpoint: /v1 (OpenAI-compatible)
    API Key: {{ vault_litellm_api_key }}
    Status: ✅ Operational

Downstream Consumers:
  FastMCP Server:
    Host: 192.168.10.59:8081
    Protocol: HTTP (localhost)
    Integration: Tool calls via HTTP API
    Status: ✅ Deployed

  Frontend UIs:
    • Open WebUI: 192.168.10.11
    • shield-power-ui: 192.168.10.12:3000
    • shield-ag-ui: 192.168.10.12:3001
    • shield-dashboard: 192.168.10.12:3002
```

---

### **2.3 Environment Configuration**

**File:** `/opt/hx-citadel-shield/orchestrator/config/.env`

```bash
# Server Configuration
ORCHESTRATOR_ENV=production
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8000
ORCHESTRATOR_WORKERS=4
LOG_LEVEL=INFO
LOG_FORMAT=json

# LightRAG Configuration
LIGHTRAG_WORKING_DIR=/opt/hx-citadel-shield/data/lightrag
LIGHTRAG_KG_ENABLE=true
LIGHTRAG_VECTOR_ENABLE=true
LIGHTRAG_HYBRID_ENABLE=true

# LLM Configuration (via LiteLLM)
LLM_API_BASE=http://192.168.10.46:4000/v1
LLM_API_KEY={{ vault_litellm_api_key }}
LLM_MODEL=llama3.2:latest
LLM_EMBEDDING_MODEL=mxbai-embed-large

# Vector Database (Qdrant)
QDRANT_URL=https://192.168.10.9:6333
QDRANT_API_KEY={{ vault_qdrant_api_key }}
QDRANT_COLLECTION=hx_corpus_v1
QDRANT_VERIFY_SSL=false

# PostgreSQL (KG Storage)
POSTGRES_HOST=192.168.10.48
POSTGRES_PORT=5432
POSTGRES_DB=shield_orchestrator
POSTGRES_USER=orchestrator
POSTGRES_PASSWORD={{ vault_postgres_orchestrator_password }}
DATABASE_URL=postgresql+asyncpg://orchestrator:{{ vault_postgres_orchestrator_password }}@192.168.10.48:5432/shield_orchestrator

# Redis (Event Bus + Task Queue)
REDIS_HOST=192.168.10.48
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://192.168.10.48:6379/0

# Redis Streams Configuration
REDIS_STREAM_INGESTION=shield:ingestion_queue
REDIS_STREAM_EVENTS=shield:events
REDIS_CONSUMER_GROUP=lightrag-workers
REDIS_MAX_LEN=10000

# Worker Pool Configuration
WORKER_POOL_SIZE=4
WORKER_BATCH_SIZE=10
WORKER_RETRY_ATTEMPTS=3
WORKER_TIMEOUT_SECONDS=300

# CopilotKit Adapter
COPILOTKIT_ENABLE=true
COPILOTKIT_SSE_ENDPOINT=/copilotkit/stream

# AG-UI Event Streaming
AG_UI_ENABLE=true
AG_UI_WS_ENDPOINT=/events/ws
AG_UI_SSE_ENDPOINT=/events/stream

# Security
JWT_SECRET_KEY={{ vault_jwt_secret_key }}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
OPENTELEMETRY_ENABLED=true
OPENTELEMETRY_ENDPOINT=http://192.168.10.16:4317
```

---

### **2.4 Application Structure**

```
/opt/hx-citadel-shield/orchestrator/
├── main.py                      # FastAPI application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py              # Pydantic Settings
│   └── .env                     # Environment variables (vault-managed)
├── models/
│   ├── __init__.py
│   ├── requests.py              # Request models (Pydantic)
│   ├── responses.py             # Response models (Pydantic)
│   └── database.py              # SQLAlchemy models
├── services/
│   ├── __init__.py
│   ├── lightrag_service.py      # LightRAG engine wrapper
│   ├── redis_streams.py         # Redis Streams wrapper
│   ├── job_tracker.py           # Job state management
│   ├── event_bus.py             # Event emission
│   └── copilotkit_adapter.py    # CopilotKit integration
├── agents/
│   ├── __init__.py
│   ├── web_crawl_coordinator.py # Pydantic AI agent
│   ├── doc_process_coordinator.py # Pydantic AI agent
│   └── query_router.py          # Pydantic AI agent
├── workflows/
│   ├── __init__.py
│   ├── ingestion_workflow.py    # LangGraph workflow
│   └── query_workflow.py        # LangGraph workflow
├── workers/
│   ├── __init__.py
│   ├── worker_pool.py           # Worker pool manager
│   └── lightrag_processor.py    # Chunk processing worker
├── api/
│   ├── __init__.py
│   ├── ingestion.py             # Ingestion endpoints
│   ├── query.py                 # Query endpoints
│   ├── jobs.py                  # Job tracking endpoints
│   ├── events.py                # SSE/WebSocket endpoints
│   ├── copilotkit.py            # CopilotKit adapter endpoints
│   └── health.py                # Health checks
├── database/
│   ├── __init__.py
│   ├── connection.py            # DB connection pool
│   ├── migrations/              # Alembic migrations
│   └── seed.py                  # Initial data
├── utils/
│   ├── __init__.py
│   ├── logging_config.py        # Structured logging
│   ├── metrics.py               # Prometheus metrics
│   └── security.py              # JWT, encryption
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
└── requirements.txt             # Python dependencies
```

---

## 3. Deployment Roadmap

### **📅 Phase 1: Foundation (Week 1)**

**Goal:** Base infrastructure and core frameworks

```yaml
Week 1 - Days 1-2: Server Provisioning
  Tasks:
    - Provision hx-orchestrator-server VM
    - Ubuntu 24.04 installation
    - Network configuration
    - Domain join (realm join)
    - CA trust installation
    - SSH key distribution
  
  Deliverable: Server ready for deployment
  Owner: System Administrator

Week 1 - Days 3-4: Base System Setup
  Tasks:
    - Install Python 3.12 and development tools
    - Install system dependencies (PostgreSQL client, Redis tools)
    - Create service user (orchestrator:orchestrator)
    - Create directory structure
    - Setup virtual environment
  
  Deliverable: Base system configured
  Owner: DevOps Engineer
  Ansible Playbook: playbooks/deploy-base.yml

Week 1 - Days 5-7: FastAPI Framework
  Tasks:
    - Install FastAPI and Uvicorn
    - Create base application structure
    - Setup configuration management (Pydantic Settings)
    - Deploy environment variables (vault-managed)
    - Create systemd service
    - Setup health check endpoints
  
  Deliverable: FastAPI server running
  Owner: Backend Engineer
  Validation: curl http://192.168.10.8:8000/health
```

---

### **📅 Phase 2: Data Layer Integration (Week 2)**

**Goal:** Database and event bus connectivity

```yaml
Week 2 - Days 1-2: PostgreSQL Integration
  Tasks:
    - Create database: shield_orchestrator
    - Create user: orchestrator
    - Install asyncpg and SQLAlchemy
    - Setup database models
    - Create Alembic migrations
    - Run initial migration
    - Seed initial data
  
  Deliverable: PostgreSQL connected and migrated
  Owner: Database Engineer
  Validation: Database tables created

Week 2 - Days 3-4: Redis Integration
  Tasks:
    - Install Redis client (redis[hiredis])
    - Setup Redis Streams wrapper
    - Create consumer groups
    - Test event emission and consumption
    - Setup connection pooling
  
  Deliverable: Redis Streams operational
  Owner: Backend Engineer
  Validation: Events flow through Redis Streams

Week 2 - Days 5-7: Qdrant Integration
  Tasks:
    - Install Qdrant client
    - Configure HTTPS connection (self-signed cert)
    - Test collection access (hx_corpus_v1)
    - Setup error handling
    - Create connection pool
  
  Deliverable: Qdrant connected
  Owner: Backend Engineer
  Validation: Vector search working
```

---

### **📅 Phase 3: LightRAG Engine (Week 3)**

**Goal:** Core RAG engine operational

```yaml
Week 3 - Days 1-3: LightRAG Installation
  Tasks:
    - Install lightrag-hku package
    - Configure LightRAG working directory
    - Setup LLM integration (via LiteLLM)
    - Configure embedding model (mxbai-embed-large)
    - Setup Knowledge Graph storage (PostgreSQL)
    - Configure Vector storage (Qdrant)
  
  Deliverable: LightRAG engine installed
  Owner: ML Engineer
  Validation: LightRAG can initialize

Week 3 - Days 4-5: Entity Extraction
  Tasks:
    - Configure entity extraction prompts
    - Test with sample documents
    - Tune extraction parameters
    - Setup entity validation
  
  Deliverable: Entity extraction working
  Owner: ML Engineer
  Validation: Entities extracted from test doc

Week 3 - Days 6-7: Hybrid Retrieval
  Tasks:
    - Configure Knowledge Graph retrieval
    - Configure Vector retrieval
    - Implement hybrid scoring
    - Test retrieval accuracy
  
  Deliverable: Hybrid retrieval operational
  Owner: ML Engineer
  Validation: RAGAS score >0.7
```

---

### **📅 Phase 4: Worker Pool & Async Processing (Week 4)**

**Goal:** Asynchronous ingestion pipeline

```yaml
Week 4 - Days 1-2: Worker Pool Implementation
  Tasks:
    - Create worker pool manager
    - Implement Redis Streams consumer
    - Setup job tracking (PostgreSQL)
    - Configure retry logic
    - Setup graceful shutdown
  
  Deliverable: Worker pool operational
  Owner: Backend Engineer
  Validation: Workers consume from queue

Week 4 - Days 3-4: Async Ingestion Pipeline
  Tasks:
    - Implement POST /lightrag/ingest-async (HTTP 202)
    - Add chunks to Redis Streams
    - Workers process chunks via LightRAG
    - Emit events via Redis Streams
    - Update job status
  
  Deliverable: Async ingestion working
  Owner: Backend Engineer
  Validation: End-to-end async flow

Week 4 - Days 5-7: Event Streaming
  Tasks:
    - Implement GET /events/stream (SSE)
    - Implement GET /events/ws (WebSocket)
    - Setup consumer groups for frontends
    - Test event replay
    - Configure max event retention
  
  Deliverable: Event streaming operational
  Owner: Backend Engineer
  Validation: Frontends receive events
```

---

### **📅 Phase 5: Agent Coordination (Week 5)**

**Goal:** Pydantic AI and LangGraph integration

```yaml
Week 5 - Days 1-3: Pydantic AI Agents
  Tasks:
    - Install pydantic-ai
    - Create web_crawl_coordinator agent
    - Create doc_process_coordinator agent
    - Create query_router agent
    - Setup agent dependencies
  
  Deliverable: Agents defined and operational
  Owner: AI Engineer
  Validation: Agents can be invoked

Week 5 - Days 4-7: LangGraph Workflows
  Tasks:
    - Install langgraph
    - Create ingestion_workflow (multi-step)
    - Create query_workflow (routing)
    - Setup state management (Redis)
    - Test workflow execution
  
  Deliverable: Workflows operational
  Owner: AI Engineer
  Validation: Multi-step workflows complete
```

---

### **📅 Phase 6: Frontend Integration (Week 6)**

**Goal:** CopilotKit and AG-UI adapters

```yaml
Week 6 - Days 1-3: CopilotKit Adapter
  Tasks:
    - Create CopilotKit adapter endpoints
    - Implement state streaming (useCopilotReadable)
    - Implement actions (useCopilotAction)
    - Test with shield-power-ui
    - Optimize latency
  
  Deliverable: CopilotKit adapter working
  Owner: Frontend Engineer + Backend Engineer
  Validation: HITL UI functional

Week 6 - Days 4-7: AG-UI Integration
  Tasks:
    - Verify event streaming endpoints
    - Test with shield-ag-ui
    - Optimize event throughput
    - Setup consumer groups
  
  Deliverable: AG-UI integrated
  Owner: Frontend Engineer + Backend Engineer
  Validation: Real-time events in UI
```

---

### **📅 Phase 7: Production Hardening (Week 7)**

**Goal:** Monitoring, security, performance

```yaml
Week 7 - Days 1-2: Monitoring
  Tasks:
    - Setup Prometheus metrics
    - Configure Grafana dashboards
    - Setup distributed tracing (OpenTelemetry)
    - Configure alert rules
  
  Deliverable: Monitoring operational
  Owner: DevOps Engineer

Week 7 - Days 3-4: Security
  Tasks:
    - Implement JWT authentication
    - Setup RBAC (if needed)
    - Configure HTTPS (reverse proxy)
    - Security audit
  
  Deliverable: Security hardened
  Owner: Security Engineer

Week 7 - Days 5-7: Performance
  Tasks:
    - Load testing (Locust)
    - Performance optimization
    - Connection pooling tuning
    - Caching strategy
  
  Deliverable: Performance validated
  Owner: Performance Engineer
```

---

### **📅 Phase 8: Testing & Documentation (Week 8)**

**Goal:** Comprehensive testing and documentation

```yaml
Week 8 - Days 1-3: Testing
  Tasks:
    - Unit tests (>80% coverage)
    - Integration tests
    - E2E tests
    - RAGAS evaluation
    - Load testing
  
  Deliverable: Test suite passing
  Owner: QA Engineer

Week 8 - Days 4-7: Documentation
  Tasks:
    - API documentation (OpenAPI/Swagger)
    - Deployment runbook
    - Troubleshooting guide
    - Architecture decision records
  
  Deliverable: Documentation complete
  Owner: Technical Writer
```

---

## 4. Individual Component Plans

**Next Steps:** Once this roadmap is approved, we will create individual deployment plans for each component:

1. ✅ **Base System Setup** (`base-system-setup-plan.md`)
2. ✅ **FastAPI Framework** (`fastapi-framework-plan.md`)
3. ✅ **PostgreSQL Integration** (`postgresql-integration-plan.md`)
4. ✅ **Redis Streams Integration** (`redis-streams-integration-plan.md`)
5. ✅ **Qdrant Integration** (`qdrant-integration-plan.md`)
6. ✅ **LightRAG Engine** (`lightrag-engine-plan.md`)
7. ✅ **Worker Pool** (`worker-pool-plan.md`)
8. ✅ **Pydantic AI Agents** (`pydantic-ai-agents-plan.md`)
9. ✅ **LangGraph Workflows** (`langgraph-workflows-plan.md`)
10. ✅ **CopilotKit Adapter** (`copilotkit-adapter-plan.md`)

Each plan will include:
- Detailed Ansible playbook
- Configuration templates
- Testing procedures
- Rollback strategies

---

## 5. Testing and Validation

### **5.1 Component Testing**

```yaml
LightRAG Engine:
  • Entity extraction accuracy >90%
  • Hybrid retrieval RAGAS score >0.7
  • KG construction time <5s per 1000 tokens
  • Vector search latency <100ms

Worker Pool:
  • Queue processing >100 chunks/second
  • Worker restart on failure <5 seconds
  • No message loss (Redis Streams ACK)
  • Job status updated in <1 second

Event Streaming:
  • Event delivery latency <500ms
  • WebSocket connection stability >99.9%
  • Consumer group isolation verified
  • Event replay works after disconnect
```

---

### **5.2 Integration Testing**

```yaml
End-to-End Flow:
  1. FastMCP crawl_web → Orchestrator queue
  2. Worker processes chunks via LightRAG
  3. KG entities extracted and stored (PostgreSQL)
  4. Vectors stored (Qdrant)
  5. Events emitted (Redis Streams)
  6. Frontend receives updates (SSE/WebSocket)
  7. Query retrieves hybrid results

Performance:
  • 1000 chunks processed in <60 seconds
  • Concurrent queries: 100 requests/second
  • Memory usage: <8GB under load
  • CPU usage: <80% under load
```

---

## 6. Success Criteria

### **6.1 Deployment Success**

```yaml
✅ Infrastructure:
   • hx-orchestrator-server provisioned
   • All system packages installed
   • Python 3.12 environment ready
   • Service user created

✅ Data Layer:
   • PostgreSQL connected and migrated
   • Redis Streams operational
   • Qdrant connected

✅ LightRAG Engine:
   • Entity extraction working
   • Hybrid retrieval operational
   • KG construction validated

✅ Async Processing:
   • Worker pool running (4 workers)
   • Async ingestion pipeline operational
   • Event streaming working

✅ Agent Coordination:
   • Pydantic AI agents functional
   • LangGraph workflows executing
   • Multi-step coordination working

✅ Frontend Integration:
   • CopilotKit adapter operational
   • AG-UI event streaming working
   • All 4 frontends connected

✅ Production Readiness:
   • Monitoring configured (Prometheus + Grafana)
   • Security hardened (JWT + HTTPS)
   • Performance validated (load tests)
   • Documentation complete
```

---

### **6.2 Quality Metrics**

```yaml
Code Quality:
  • Type hints: 100%
  • Test coverage: >80%
  • Linter compliance: 100%
  • Documentation: Complete

Performance:
  • LightRAG ingestion: <5s per 1000 tokens
  • Hybrid retrieval: <100ms p95
  • Event delivery: <500ms p95
  • API response: <200ms p95

Reliability:
  • Service uptime: >99.9%
  • Worker restart: <5s
  • Event delivery: 100% (at-least-once)
  • Database failover: <10s

Quality:
  • Entity extraction accuracy: >90%
  • RAGAS faithfulness: >0.8
  • RAGAS relevance: >0.7
  • User satisfaction: >4/5
```

---

## 7. Risk Assessment

### **7.1 Deployment Risks**

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **LightRAG installation fails** | Medium | High | Test in dev environment first, fallback to nano-vectordb |
| **PostgreSQL migration fails** | Low | High | Backup before migration, test rollback procedure |
| **Worker pool doesn't scale** | Medium | Medium | Load testing, tune worker count, monitor Redis queue depth |
| **Event stream overflow** | Low | Medium | Set MAXLEN on streams, consumer group isolation |
| **LLM integration timeout** | Medium | Medium | Circuit breakers, retry logic, fallback models |

---

### **7.2 Mitigation Strategies**

```yaml
Mitigation 1: Pre-deployment validation
  • Test in dev environment
  • Validate all dependencies
  • Check network connectivity
  • Verify vault secrets

Mitigation 2: Phased rollout
  • Deploy one component at a time
  • Validate before next phase
  • Rollback capability at each phase

Mitigation 3: Comprehensive monitoring
  • Prometheus alerts for all components
  • Grafana dashboards
  • Distributed tracing
  • Structured logging
```

---

## 8. Timeline Summary

```yaml
Total Duration: 8 weeks

Phase 1 (Week 1): Foundation ✅
Phase 2 (Week 2): Data Layer ✅
Phase 3 (Week 3): LightRAG Engine ✅
Phase 4 (Week 4): Worker Pool & Async ✅
Phase 5 (Week 5): Agent Coordination ✅
Phase 6 (Week 6): Frontend Integration ✅
Phase 7 (Week 7): Production Hardening ✅
Phase 8 (Week 8): Testing & Documentation ✅

Parallel Tracks:
  • Frontend development (Weeks 4-6)
  • Testing (continuous)
  • Documentation (continuous)
```

---

## 9. Approval Checklist

**Before proceeding to individual component plans, confirm:**

- [ ] Tech stack approved (all 10 components)
- [ ] Integration architecture approved
- [ ] 8-week timeline acceptable
- [ ] Resource allocation confirmed
- [ ] Risk mitigation strategies approved
- [ ] Success criteria agreed upon
- [ ] Testing strategy approved

---

## Conclusion

This deployment plan provides a comprehensive roadmap for deploying the Shield Orchestrator Server (Intelligence Hub). The plan is structured to:

1. ✅ Deploy incrementally (8 phases)
2. ✅ Validate at each step
3. ✅ Minimize risk through phased rollout
4. ✅ Leverage tech_kb for proven implementations
5. ✅ Align with Shield Master Architecture

**Next Step:** Once approved, we will create individual Ansible playbooks for each of the 10 components, following the same proven pattern as the MCP server deployment.

---

**Deployment Plan By:** Agent C  
**Date:** October 9, 2025  
**Status:** ⏸️ **AWAITING APPROVAL**  
**Confidence:** 90% (complex multi-component system)

---

## References

- **Master Architecture:** `Codename_Shield/2.0-Architecture/SHIELD-MASTER-ARCHITECTURE.md`
- **MCP Server Deployment:** `Codename_Shield/9.0-Deployment/mcp-server-deployment-plan.md`
- **LightRAG Source:** `tech_kb/LightRAG-main/`
- **CopilotKit Source:** `tech_kb/CopilotKit-main/`
- **Agentic Patterns:** `tech_kb/agentic-design-patterns-docs-main/`

**Standing by for your approval, Agent 99!** 🎯


