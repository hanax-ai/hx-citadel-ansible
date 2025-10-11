# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

HX-Citadel Ansible Infrastructure automates deployment and management of a 17-server AI fleet running the HX-Citadel RAG pipeline on Ubuntu 24.04. The control node is hx-devops-server (192.168.10.14).

**Current Status** (October 11, 2025):
- **Phase 1 COMPLETE**: 21/21 critical tasks delivered (100%)
- **Phase 2 IN PROGRESS**: Quality Improvements (TASK-032 active - 45% complete)
- **Production Readiness**: 90% (RAG pipeline fully operational)
- **MCP Server**: Operational with 7 tools at hx-mcp1-server:8081
- **Open WebUI**: Deployed and operational at hx-webui-server:8080
- **Overall Progress**: 21/59 tasks (36%)

## Essential Commands

### Setup and Installation

```bash
# Install Galaxy dependencies (required after clone)
ansible-galaxy install -r requirements.yml

# Verify connectivity across fleet
ansible all -i inventory/prod.ini -m ping
```

### Deployment Commands

```bash
# RECOMMENDED: Deploy with automatic validation and smoke tests
ansible-playbook -i inventory/prod.ini playbooks/deploy-with-validation.yml

# ALWAYS run pre-flight checks before deployment
ansible-playbook -i inventory/prod.ini playbooks/preflight-check.yml

# Full deployment
ansible-playbook -i inventory/prod.ini site.yml

# Dry run (no changes) - CRITICAL for testing
ansible-playbook -i inventory/prod.ini site.yml --check --diff

# Component-specific deployment using tags
ansible-playbook -i inventory/prod.ini site.yml --tags db          # Database layer only
ansible-playbook -i inventory/prod.ini site.yml --tags models      # LLM nodes only
ansible-playbook -i inventory/prod.ini site.yml --tags api         # API layer only

# Single host deployment
ansible-playbook -i inventory/prod.ini site.yml --limit hx-sqldb-server
```

### Testing and Validation

```bash
# Syntax check (always run before deployment)
ansible-playbook --syntax-check site.yml

# Lint check (enforce best practices)
ansible-lint site.yml

# Post-deployment smoke tests
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml

# Specific component tests
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags database
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags vector
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags llm
```

### Service Management

```bash
# Check service status
ansible all -i inventory/prod.ini -m systemd -a "name=postgresql" -b

# Verify API endpoints (use FQDNs for consistency)
curl http://hx-vectordb-server:6333/healthz           # Qdrant
curl http://hx-ollama1:11434/api/version              # Ollama
curl http://hx-orchestrator-server:8080/healthz       # Orchestrator
curl http://hx-mcp1-server:8081/health                # MCP Server (NEW - Phase 1)

# MCP Server Health Check (includes circuit breaker metrics)
curl http://hx-mcp1-server:8081/health | jq

# View service logs
ansible db_nodes -i inventory/prod.ini -m shell -a "journalctl -u postgresql -n 50" -b

# MCP Server logs (includes circuit breaker events)
ansible hx-mcp1-server -i inventory/prod.ini -m shell -a "journalctl -u shield-mcp-server -n 50" -b
```

## Architecture

### Shield Five-Layer Architecture (Master Design)

The HX-Citadel Shield follows a **five-layer architecture** (see `docs/Delivery-Enhancements/HX-ARCHITECTURE.md` for complete design):

1. **Layer 1 - Frontend**: Open WebUI (✅ deployed at hx-webui-server:8080), shield-power-ui, shield-ag-ui, shield-dashboard (planned)
2. **Layer 2 - Gateway**: LiteLLM API Gateway (✅ hx-litellm-server:4000 - routes to Ollama + OpenAI)
3. **Layer 3 - Tool Execution**: FastMCP Server (✅ hx-mcp1-server:8081 - 7 tools, circuit breakers)
4. **Layer 4 - Orchestration**: Orchestrator (✅ hx-orchestrator-server:8000 - LightRAG, LangGraph, workers)
5. **Layer 5 - Data**: Qdrant, PostgreSQL, Redis, Ollama (✅ all operational)

### Multi-Layered Service Architecture (Current Deployment)

**Database Layer** (hx-sqldb-server - 192.168.10.48)
- PostgreSQL: Primary relational database
- Redis: Cache and message queue (with Redis Streams for event bus)

**Vector Database Layer** (hx-vectordb-server - 192.168.10.9)
- Qdrant: Vector similarity search and storage

**LLM & Embedding Layer** (3 Ollama instances)
- **hx-orchestrator-server** (192.168.10.8:11434): **Embedding models** (co-located for low latency)
  - mxbai-embed-large:latest (1024-dim, 669MB)
  - nomic-embed-text:latest (768-dim, 274MB)
  - all-minilm:latest (384-dim, 46MB)
- **hx-ollama1** (192.168.10.50:11434): Primary LLM inference (3 models: gemma3:27b, gpt-oss:20b, mistral:7b)
- **hx-ollama2** (192.168.10.52:11434): Secondary LLM inference (6 models: qwen variants, cogito)

**Frontend Layer** (hx-webui-server - 192.168.10.TBD)
- **Open WebUI** (http://hx-webui-server:8080): ✅ Deployed and operational
  - Chat interface with LLM access via LiteLLM
  - Connected to: LiteLLM Gateway (http://hx-litellm-server:4000/v1)
  - Also connected to: OpenAI API (https://api.openai.com/v1)
  - MCP tools: Not yet integrated (future enhancement)

**API Gateway Layer**
- **LiteLLM** (hx-litellm-server:4000): ✅ Unified API gateway
  - Routes embeddings → hx-orchestrator-server (192.168.10.8)
  - Routes LLMs → hx-ollama1/hx-ollama2 (192.168.10.50/.52)
  - 12 models total (3 embeddings + 9 LLMs)
  - OpenAI-compatible /v1 endpoints
- Prisma ORM (hx-prisma-server - 192.168.10.47): Database middleware

**Orchestration Layer** (hx-orchestrator-server - 192.168.10.8)
- FastAPI orchestrator service
- Manages: LightRAG, LangGraph, Pydantic AI, CopilotKit
- Worker pool for async job processing
- Integration with all backend services

**Model Context Protocol** (hx-mcp1-server - 192.168.10.59) ✨ **Phase 1 Complete**
- **MCP server with 7 operational tools**: `crawl_web`, `ingest_doc`, `qdrant_find`, `qdrant_store`, `lightrag_query`, `get_job_status`, `health_check`
- **Circuit breaker protection**: 10x faster failure handling (< 1ms fast-fail vs 30s timeout)
- **HTTP 202 async pattern**: Long-running task support with job status tracking
- **Service status**: Active and stable at hx-mcp1-server:8081
- **Reference**: See `docs/MCP_TOOLS_REFERENCE.md` for complete API documentation

**Management Layer** (hx-qwebui-server - 192.168.10.53)
- Qdrant Web UI for vector database management

### Orchestrator Component Architecture

The orchestrator is the most complex component with multiple integrated subsystems:

1. **Base Components** (orchestrator_base_setup, orchestrator_fastapi)
   - Virtual environment setup at /opt/hx-citadel-shield
   - FastAPI application framework
   - Health check endpoints (/healthz)
   - Systemd service: shield-orchestrator.service

2. **Framework Integrations**
   - **orchestrator_lightrag**: Document processing and ingestion
   - **orchestrator_langgraph**: Workflow orchestration with state graphs
   - **orchestrator_pydantic_ai**: Agent-based AI coordination
   - **orchestrator_copilotkit**: Real-time collaboration adapter

3. **Service Connectors** (orchestrator_postgresql, orchestrator_qdrant, orchestrator_redis)
   - Database connection pooling with SQLAlchemy
   - Qdrant client with health monitoring
   - Redis Streams for event-driven architecture

4. **Worker System** (orchestrator_workers)
   - Async worker pool (4+ workers default)
   - Job tracking and status management
   - Event bus integration via Redis Streams
   - Graceful shutdown with SIGTERM/SIGINT handling

### Deployment Flow

The `site.yml` orchestrator imports playbooks in dependency order:
1. `deploy-base.yml` - Base system configuration (all nodes)
2. `deploy-db.yml` - PostgreSQL and Redis
3. `deploy-vector.yml` - Qdrant vector database
4. `deploy-llm.yml` - Ollama LLM nodes with model sync
5. `deploy-api.yml` - LiteLLM and Prisma API layer
6. `deploy-orchestrator-local.yml` - Orchestrator with all integrations

The safe deployment wrapper (`deploy-with-validation.yml`) adds:
- Stage 1: Pre-flight validation (connectivity, sudo, disk space)
- Stage 2: User confirmation + deployment
- Stage 3: Smoke tests (service health validation)

## Critical Development Standards

### MANDATORY: Ansible Best Practices

**ALL code MUST follow `docs/ANSIBLE-BEST-PRACTICES.md`**. Key requirements:

1. **FQCN (Fully Qualified Collection Names) - NO EXCEPTIONS**
   - ALWAYS use `ansible.builtin.apt`, `ansible.builtin.service`, etc.
   - NEVER use short names like `apt:`, `service:`, `file:`
   - Reference: `tech_kb/ansible-devel/` for official module syntax

2. **Modern YAML Syntax**
   - Use dictionary format, not inline: `ansible.builtin.service:` with parameters on new lines
   - Use `loop:` instead of deprecated `with_items:`
   - Explicitly set `gather_facts: yes/no` based on needs

3. **Error Handling**
   - Use `block/rescue/always` for critical operations
   - Set `changed_when` and `failed_when` appropriately
   - Use `no_log: true` for sensitive data (passwords, tokens)

4. **Idempotency**
   - All tasks must be safe to run multiple times
   - Use `state: present` (not `latest`) unless updates are intended
   - Avoid shell/command modules when native modules exist

5. **Security**
   - Use Ansible Vault for all secrets (vault_password_file: ~/.ansible_vault_pass)
   - Never expose passwords in command line or logs
   - Use environment variables (REDISCLI_AUTH) for CLI tools

### Linting and Validation

The project enforces strict linting via `.ansible-lint`:
- **fqcn-builtins**: Mandatory FQCN for all core modules
- **no-changed-when**: Command/shell tasks need changed_when
- **risky-file-permissions**: Explicit file permissions required

Pre-commit hooks run:
- `ansible-lint` for playbook validation
- FQCN compliance check via `scripts/check-fqdn.sh`

### Testing Workflow

```bash
# 1. Syntax check
ansible-playbook --syntax-check site.yml

# 2. Lint check
ansible-lint site.yml

# 3. Check mode (dry run)
ansible-playbook -i inventory/prod.ini site.yml --check

# 4. Diff mode (show changes)
ansible-playbook -i inventory/prod.ini site.yml --check --diff

# 5. Limited deployment (test on one host)
ansible-playbook -i inventory/prod.ini site.yml --limit hx-test-server

# 6. Full deployment
ansible-playbook -i inventory/prod.ini site.yml
```

## Variable Management

### Variable Precedence (low to high)
1. Role defaults (`roles/*/defaults/main.yml`)
2. Inventory vars (`inventory/prod.ini`)
3. `group_vars/all/`
4. `group_vars/<group>.yml`
5. `host_vars/<host>/`
6. Play vars
7. Task vars
8. Extra vars (`-e` flag)

### Naming Convention
- **Role-specific**: Prefix with role name (e.g., `postgresql_version`, `redis_port`)
- **Application-wide**: Use `orchestrator_*` prefix (e.g., `orchestrator_venv_dir`, `orchestrator_app_dir`)
- **Never use generic names** like `version`, `port`, `user` (causes conflicts)

### Key Variables

**Orchestrator paths** (defined in orchestrator_base_setup):
- `orchestrator_app_dir`: /opt/hx-citadel-shield
- `orchestrator_venv_dir`: {{ orchestrator_app_dir }}/orchestrator-venv
- `orchestrator_service_user`: agent0

**Service ports**:
- PostgreSQL: 5432
- Redis: 6379
- Qdrant: 6333, 6334
- Ollama: 11434
- Orchestrator: 8080
- MCP Server: 8081 (NEW - Phase 1)

## Role Structure

Roles follow standard Ansible structure:
```
roles/<role_name>/
├── tasks/
│   └── main.yml          # Task orchestration
├── templates/
│   └── *.j2              # Jinja2 templates
├── defaults/
│   └── main.yml          # Default variables
├── vars/
│   └── main.yml          # Role variables
├── handlers/
│   └── main.yml          # Service handlers
└── README.md             # Role documentation
```

**Orchestrator roles** use numbered task files:
```
roles/orchestrator_*/tasks/
├── 01-dependencies.yml
├── 02-configuration.yml
├── 03-validation.yml
└── main.yml (imports all)
```

## Special Inventories

- **Production**: `inventory/prod.ini` (17 servers, all groups)
- **Qdrant UI**: `inventory/hx-qwui.ini` (separate for UI-only deployment)

Use specific inventory for Qdrant UI: `ansible-playbook -i inventory/hx-qwui.ini playbooks/deploy-qdrant-ui.yml`

## Reference Materials

### Ansible Resources
- **Ansible Core Source**: `tech_kb/ansible-devel/` - Official Ansible 2.20 dev repository
- **Module Examples**: `tech_kb/ansible-devel/lib/ansible/modules/` - Core module implementations
- **Development Tools**: `tech_kb/ansible-devel/hacking/` - Testing utilities

**When in doubt, reference tech_kb/ansible-devel - never guess!**

### Shield Architecture
- **Master Architecture**: `docs/Delivery-Enhancements/HX-ARCHITECTURE.md` - Complete system design (v3.0 - Oct 2025)
  - Five-layer architecture (Frontend → Gateway → Tools → Orchestration → Data)
  - **Actual deployment topology**: Embeddings on orchestrator, LLMs on dedicated nodes
  - **LiteLLM routing**: 12 models (3 embeddings + 9 LLMs) with intelligent routing
  - **Open WebUI integration**: Chat interface with LiteLLM + OpenAI access
  - Production optimizations (async ingestion, circuit breakers, Redis Streams)
  - Testing strategy (RAG evaluation, HITL workflows, load testing)
  - Monitoring & observability (OpenTelemetry, Prometheus, Grafana)
  - **Critical**: Reference this for understanding the complete Shield vision and architecture decisions

### Tech Knowledge Base (`tech_kb/`) - 🎯 **CRITICAL RESOURCE**

The `tech_kb/` directory contains **source code, documentation, and configurations** for all technologies used in the project. This is your "Model Context Protocol for Humans" - a curated reference library with **33 technology repositories**.

#### **Most Critical References**

1. **`tech_kb/shield_mcp_complete/`** ⭐ **HIGHEST VALUE**
   - Complete MCP server reference implementation (~35 files)
   - Production-ready code examples for Phase 1 implementation
   - Architecture docs, deployment scripts, database schemas
   - **When implementing MCP tools**: Check here for working examples
   - **Key file**: `README.md` - comprehensive implementation guide

2. **`tech_kb/ansible-devel/`** (5,604 files)
   - Official Ansible 2.20 development repository
   - Core module implementations at `lib/ansible/modules/`
   - **When writing Ansible tasks**: Reference this for FQCN syntax and best practices
   - **Critical**: Never guess module syntax - look it up here!

3. **`tech_kb/fastmcp-main/`** (629 files)
   - FastMCP framework source code
   - Tool patterns, server setup, MCP protocol implementation
   - **When creating MCP tools**: Study the framework internals here

4. **`tech_kb/LightRAG-main/`** (401 files)
   - LightRAG RAG engine source
   - Knowledge graph construction, hybrid retrieval
   - **When working with RAG**: Understand the LightRAG API and patterns

5. **`tech_kb/litellm-main/`** (3,970 files)
   - LiteLLM gateway source code
   - Guardrails, routing, caching patterns
   - **When configuring gateway**: Reference for advanced features

#### **Framework References**

| Technology | Directory | Files | Use Cases |
|-----------|-----------|-------|-----------|
| **Ollama** | `ollama-main/` | 963 | LLM deployment, model serving, embeddings |
| **FastAPI** | `fastapi/` | 2,551 | API development, async patterns, validation |
| **LangGraph** | `langgraph-main/` | 1,094 | Workflow orchestration, state graphs |
| **Pydantic AI** | `pydantic-main/` | 483 | Agent definitions, type validation |
| **CopilotKit** | `CopilotKit-main/` | 2,821 | HITL UI integration, state streaming |
| **AG-UI** | `ag-ui-main/` | 696 | Event-driven UI, real-time updates |
| **Crawl4AI** | `crawl4ai-main/` | 628 | Web crawling implementation |
| **Docling** | `docling-main/` | 710 | Document processing, multi-format support |

#### **Database & Storage**

| Technology | Directory | Files | Use Cases |
|-----------|-----------|-------|-----------|
| **Qdrant** | `qdrant-master/` | 1,316 | Vector DB server implementation |
| **Qdrant Client** | `qdrant-client-master/` | 293 | Python client for vector operations |
| **PostgreSQL** | `postgres-master/` | 7,301 | Database internals, optimization |
| **Redis** | `redis-unstable/` | 1,703 | Streams, caching, pub/sub patterns |

#### **Frontend & UI**

| Technology | Directory | Files | Use Cases |
|-----------|-----------|-------|-----------|
| **Next.js** | `next.js-canary/` | 25,300 | React framework, SSR patterns |
| **Open WebUI** | `open-webui-main/` | 4,790 | Chat UI implementation |
| **Zod** | `zod-main/` | 536 | Schema validation |
| **Zustand** | `zustand-main/` | 137 | State management |

#### **Design Patterns**

| Technology | Directory | Files | Use Cases |
|-----------|-----------|-------|-----------|
| **Agentic Patterns** | `agentic-design-patterns-docs-main/` | 66 | Agent design patterns, best practices |
| **Ottomator Agents** | `ottomator-agents-main/` | 756 | Live agent studio examples |

#### **How to Use This Knowledge Base**

1. **Before implementing a feature**:
   ```bash
   # Search for similar implementations
   grep -r "async def" tech_kb/fastmcp-main/

   # Find module examples
   ls tech_kb/ansible-devel/lib/ansible/modules/

   # Study reference implementation
   cat tech_kb/shield_mcp_complete/implementation/mcp_server/src/main.py
   ```

2. **When stuck on syntax**:
   - Ansible: Check `tech_kb/ansible-devel/lib/ansible/modules/`
   - FastMCP: Check `tech_kb/fastmcp-main/src/`
   - LightRAG: Check `tech_kb/LightRAG-main/lightrag/`

3. **For production patterns**:
   - Reference: `tech_kb/shield_mcp_complete/`
   - Architecture: `tech_kb/shield_mcp_complete/architecture/`
   - Deployment: `tech_kb/shield_mcp_complete/implementation/scripts/`

4. **For design decisions**:
   - Patterns: `tech_kb/agentic-design-patterns-docs-main/`
   - Examples: `tech_kb/ottomator-agents-main/`

**⚠️ Important**: This knowledge base contains **67,000+ files**. Use targeted searches rather than reading entire repositories. The `shield_mcp_complete/` directory is your starting point for Shield-specific implementations.

## Common Patterns

### Service Deployment Pattern
```yaml
# 1. Install dependencies
- name: Install package
  ansible.builtin.apt:
    name: package-name
    state: present
  become: yes

# 2. Configure with template
- name: Deploy configuration
  ansible.builtin.template:
    src: config.j2
    dest: /etc/service/config
    backup: yes
  notify: restart service

# 3. Ensure service is running
- name: Start and enable service
  ansible.builtin.systemd:
    name: service-name
    state: started
    enabled: yes
  become: yes
```

### Health Check Pattern
```yaml
- name: Check service health
  ansible.builtin.uri:
    url: "http://{{ ansible_host }}:{{ port }}/healthz"
    status_code: 200
    timeout: 5
  register: health_check
  retries: 5
  delay: 2
  until: health_check.status == 200
```

### Error Handling Pattern
```yaml
- name: Critical operation
  block:
    - name: Backup existing config
      ansible.builtin.copy:
        src: /etc/config
        dest: /etc/config.backup
        remote_src: yes

    - name: Update configuration
      ansible.builtin.template:
        src: config.j2
        dest: /etc/config

  rescue:
    - name: Restore backup
      ansible.builtin.copy:
        src: /etc/config.backup
        dest: /etc/config
        remote_src: yes

  always:
    - name: Ensure service is running
      ansible.builtin.systemd:
        name: myservice
        state: started
```

## Phase 1 Achievements ✨

**Status**: ✅ COMPLETE (October 11, 2025) - 21/21 tasks delivered (100%)

### Critical Features Implemented
1. **MCP Server Fully Operational**
   - 7 production-ready tools (~1,125 LOC)
   - Location: `roles/fastmcp_server/`
   - Service: shield-mcp-server at hx-mcp1-server:8081
   - Tools: `crawl_web`, `ingest_doc`, `qdrant_find`, `qdrant_store`, `lightrag_query`, `get_job_status`, `health_check`

2. **Circuit Breaker Protection**
   - PyBreaker integration on all orchestrator calls
   - Fast-fail < 1ms (vs 30s timeout) - 10x performance improvement
   - Health metrics at `/health` endpoint

3. **HTTP 202 Async Pattern**
   - Job status tracking for long-running operations
   - Endpoint: `get_job_status(job_id)`

4. **Error Handling Framework**
   - 4 block/rescue/always patterns in Ansible deployment
   - Comprehensive logging and recovery

5. **Test Documentation**
   - Location: `tests/` directory
   - 4 test procedures: TEST-004, TEST-005, TEST-009, TEST-011
   - Circuit breaker validation and load test plans

**Production Readiness**: 85% (Phase 1 → Phase 2 transition)

### Known Issues and Fixes

All 45 critical issues from initial assessment have been resolved (see `docs/CRITICAL_FIXES_REMAINING.md` for audit trail):
- ✅ Security: No password exposure in logs/process lists
- ✅ Runtime: All TypeError, NameError, AttributeError crashes fixed
- ✅ Performance: LLM healthcheck caching, concurrent embeddings processing
- ✅ Correctness: Service naming, variable definitions, privilege escalation

## Documentation

### Core Guides (in `docs/`)
- `ANSIBLE-BEST-PRACTICES.md` - **MANDATORY** coding standards
- `DEPLOYMENT-GUIDE.md` - Comprehensive deployment procedures
- `QUICK-START.md` - Fast reference commands
- `IMPLEMENTATION-SUMMARY.md` - Safe deployment framework
- `MCP_TOOLS_REFERENCE.md` - Complete MCP tools API documentation (NEW - Phase 1)

### Phase 1 Deliverables (in `docs/Delivery-Enhancements/`)
- **`TASK-TRACKER.md`** - Real-time progress tracking (21/59 tasks, 36%)
- **`EXECUTIVE-BRIEFING.md`** - Leadership summary (v2.0 - Phase 1 complete)
- **`COMPREHENSIVE-IMPLEMENTATION-ROADMAP.md`** - 3-week master plan
- **`TASK-EXECUTION-MATRIX.md`** - Detailed task specifications
- **`POST-PHASE1-CLEANUP-SUMMARY.md`** - Repository cleanup summary

### Test Documentation (in `tests/`)
- `TEST-004-web-crawling.md` - Web crawling test procedures
- `TEST-005-document-processing.md` - Document processing tests
- `TEST-009-qdrant-operations.md` - Vector database operations tests
- `TEST-011-lightrag-e2e.md` - LightRAG end-to-end tests
- `load_test_plan.md` - Circuit breaker load testing scenarios
- `test-mcp-tools.py` - MCP tools testing script
- `test_circuit_breaker.sh` - Circuit breaker validation script

### Operational Documentation
- `maintenance/host-inventory.yml` - Fleet documentation
- `status/*.md` - Deployment status snapshots
- `docs/CIRCUIT-BREAKER-VALIDATION.md` - Circuit breaker testing report
- `docs/NEXT-SESSION-REMINDER.md` - Session handoff documentation

## Development Workflow

1. **Before making changes**:
   - Read `docs/ANSIBLE-BEST-PRACTICES.md`
   - Check existing role structure for patterns
   - Reference `tech_kb/ansible-devel` for module syntax

2. **During development**:
   - Use FQCN for ALL modules
   - Add error handling (block/rescue/always)
   - Use `no_log: true` for sensitive data
   - Test with `--check --diff`

3. **Before committing**:
   - Run `ansible-playbook --syntax-check`
   - Run `ansible-lint`
   - Verify idempotency (run twice, second run shows no changes)
   - Update relevant documentation

4. **Deployment to production**:
   - ALWAYS run pre-flight checks first
   - Use `deploy-with-validation.yml` for safety
   - Monitor logs after deployment
   - Run smoke tests to validate

## Current Implementation Status

### Phase Progress
- **Phase 1: Critical Fixes** ✅ COMPLETE (21/21 tasks, 100%)
- **Phase 2: Quality Improvements** ⏭️ READY TO START (0/18 tasks, 0%)
  - Sprint 2.1: Type Hints Migration (9 tasks)
  - Sprint 2.2: Automated Testing & CI/CD (9 tasks)
- **Phase 3: Production Hardening** ⏭️ PENDING (0/20 tasks, 0%)
  - Sprint 3.1: Documentation (7 tasks)
  - Sprint 3.2: Monitoring & Alerting (13 tasks)

### Next Steps (Phase 2)
1. **TASK-022**: Setup Mypy (1 hour) - Create `mypy.ini`, add type stubs
2. **TASK-023**: Create Common Types Module (2 hours) - Define shared types
3. **TASK-024-030**: Type Hints Migration (95%+ coverage target)
4. **TASK-031-039**: Automated Testing & CI/CD (80%+ test coverage target)

**Tracking**: See `docs/Delivery-Enhancements/TASK-TRACKER.md` for daily updates

## Repository Structure (Post-Phase 1)

Key directories after October 11, 2025 cleanup:
```
hx-citadel-ansible/
├── README.md                      # Comprehensive project overview (updated)
├── CLAUDE.md                      # This file
├── docs/
│   ├── MCP_TOOLS_REFERENCE.md     # NEW - Phase 1 deliverable
│   ├── CIRCUIT-BREAKER-VALIDATION.md  # Circuit breaker testing report
│   ├── Delivery-Enhancements/     # Implementation tracking (Phase 1-3)
│   │   ├── TASK-TRACKER.md        # Daily progress tracking
│   │   ├── EXECUTIVE-BRIEFING.md  # Leadership summary (v2.0)
│   │   └── *.md                   # Implementation planning docs
│   └── [other documentation]
├── tests/                         # NEW - Test artifacts organized
│   ├── TEST-*.md                  # Test procedure documentation
│   ├── test-*.py                  # Test scripts
│   └── *.sh                       # Validation scripts
├── roles/
│   ├── fastmcp_server/            # NEW - Phase 1 deliverable (7 tools)
│   └── [other roles]
└── [standard Ansible directories]
```

## Ansible Configuration

Key settings from `ansible.cfg`:
- Default inventory: `./inventory/prod.ini`
- Fact caching: JSON file at `./.ansible_cache` (24h TTL)
- Vault password: `~/.ansible_vault_pass`
- SSH pipelining: Enabled for performance
- Control persistence: 60 minutes for faster repeated runs

---

**Last Updated**: October 11, 2025 (Post-Phase 1 Cleanup)
**Phase 1 Status**: ✅ COMPLETE - All 21/21 critical tasks delivered
**Current Branch**: `main` (feature/production-parity merged)
**Production Readiness**: 85%
**Next Milestone**: Phase 2 - Quality Improvements (Type Hints & Testing)
