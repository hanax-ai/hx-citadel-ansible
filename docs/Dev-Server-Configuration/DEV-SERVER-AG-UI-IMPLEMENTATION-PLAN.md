# Dev Server AG-UI Implementation Plan
## Shield AG-UI: Power User Interface Deployment

**Version**: 2.0 (Hybrid Approach)  
**Date**: October 12, 2025  
**Status**: 🟢 **APPROVED - HYBRID ARCHITECTURE**  
**Prepared By**: AI Agent  
**Revised By**: HX-Citadel Team (Oct 12, 2025)  
**Target Server**: hx-dev-server (192.168.10.12)

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Infrastructure Requirements](#3-infrastructure-requirements)
4. [Ansible Role Design](#4-ansible-role-design)
5. [Implementation Tasks](#5-implementation-tasks)
6. [Docker Configuration](#6-docker-configuration)
7. [Integration Points](#7-integration-points)
8. [Security & Access Control](#8-security-and-access-control)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment Timeline](#10-deployment-timeline)

---

## 1. Executive Summary

### 1.1 Vision

Deploy **shield-ag-ui** on hx-dev-server to provide Line-of-Business (LoB) power users with an advanced, real-time interface to the HX-Citadel Shield RAG pipeline. This **hybrid approach** leverages an existing Vite + React frontend (6,500 LOC) combined with a new FastAPI backend implementing the AG-UI Python SDK protocol for agent-user interaction, providing real-time event streaming, knowledge graph visualization, and advanced tool controls.

### 1.2 Key Objectives

| Objective | Description | Success Criteria |
|-----------|-------------|------------------|
| **AG-UI Deployment** | Deploy shield-ag-ui on hx-dev-server:3001 via Docker | Service running, health check passing |
| **Infrastructure Integration** | Connect to all existing services (Orchestrator, LiteLLM, Redis, etc.) | All APIs reachable, auth working |
| **Real-time Events** | Implement Redis Streams consumer for live updates | Events streaming to UI < 100ms |
| **Docker Orchestration** | Use Docker Compose for multi-container management | All containers healthy |
| **Ansible Automation** | Create reusable Ansible role for deployment | Idempotent, with error handling |

### 1.3 Target Users

- **LoB Power Users**: Advanced operations staff
- **Tools Access**: Full (all 7 MCP tools + kg_curate)
- **Events**: Complete event stream via Redis Streams
- **Quotas**: 1000 queries/hour

---

## 2. Architecture Overview

### 2.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  hx-dev-server (192.168.10.12)                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Docker Compose Stack                                  │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  shield-ag-ui-frontend (Port 3001)               │ │ │
│  │  │  Technology: Vite 5.4 + React 18 (SPA)           │ │ │
│  │  │  UI Framework: shadcn-ui + Radix UI              │ │ │
│  │  │  Source: Existing 6,500 LOC (Lovable-built)      │ │ │
│  │  │  Features:                                        │ │ │
│  │  │  • Real-time event timeline                      │ │ │
│  │  │  • Knowledge graph D3.js visualization           │ │ │
│  │  │  • Advanced tool controls                        │ │ │
│  │  │  • Batch operations                              │ │ │
│  │  │  • Job tracking dashboard                        │ │ │
│  │  │  • KG curation interface                         │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  ag-ui-backend (Port 8002)                       │ │ │
│  │  │  Technology: Python FastAPI + AG-UI Python SDK   │ │ │
│  │  │  Purpose: AG-UI protocol adapter                 │ │ │
│  │  │  Features:                                        │ │ │
│  │  │  • SSE event streaming                           │ │ │
│  │  │  • Redis Streams consumer                        │ │ │
│  │  │  • Event transformation                          │ │ │
│  │  │  • State synchronization                         │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  nginx (Port 80/443)                             │ │ │
│  │  │  Purpose: Reverse proxy & SSL termination        │ │ │
│  │  │  Routes:                                          │ │ │
│  │  │  • / → shield-ag-ui:3001                         │ │ │
│  │  │  • /api → ag-ui-backend:8002                     │ │ │
│  │  │  • /events → ag-ui-backend:8002/sse              │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  LiteLLM     │  │  Orchestrator    │  │  Redis          │
│  :4000       │  │  :8000           │  │  :6379          │
│  (Gateway)   │  │  (Intelligence)  │  │  (Events)       │
└──────────────┘  └──────────────────┘  └─────────────────┘
```

### 2.2 Integration Points

| Service | Endpoint | Purpose | Protocol |
|---------|----------|---------|----------|
| **LiteLLM Gateway** | hx-litellm-server:4000 | MCP tool execution via API | HTTP REST |
| **Orchestrator** | hx-orchestrator-server:8000 | LightRAG queries, job status | HTTP REST |
| **Redis Streams** | hx-sqldb-server:6379 | Real-time event streaming | Redis Streams |
| **Qdrant** | hx-vectordb-server:6333 | Direct vector operations | HTTP REST |

### 2.3 Technology Stack

**Frontend (shield-ag-ui-frontend)** - EXISTING CODEBASE:
- Vite 5.4 (Build tool - faster than Next.js for SPA)
- React 18 (UI framework)
- shadcn-ui + Radix UI (Component library - replaces AG-UI React SDK)
- TanStack Query (state management - replaces Zustand)
- Zod (schema validation)
- D3.js (knowledge graph visualization - already implemented)
- TailwindCSS (styling)
- **Source**: 6,500 LOC from Lovable.dev (90% feature-complete)

**Backend (ag-ui-backend)**:
- Python 3.12
- FastAPI (API framework)
- AG-UI Python SDK (ag-ui-protocol)
- Redis-py (Redis Streams consumer)
- HTTPX (async HTTP client)
- Pydantic (data validation)

**Infrastructure**:
- Docker 24.x
- Docker Compose 2.x
- Nginx (reverse proxy)
- SSL/TLS (Let's Encrypt or self-signed)

---

## 3. Infrastructure Requirements

### 3.1 Hybrid Approach Overview

**Architecture Decision**: Leverage existing Vite + React frontend (6,500 LOC from Lovable.dev) + build new FastAPI backend with AG-UI Python SDK protocol.

**Rationale**:
- Preserves 90% complete frontend implementation
- Reduces development time from 50 hours to ~20 hours
- Maintains AG-UI protocol compliance via backend
- Faster time to production (8 days vs 15 days)

### 3.2 Server Specifications

**Target Server**: hx-dev-server (192.168.10.12)

**Current Status** (to be verified):
- OS: Ubuntu 24.04 LTS
- CPU: TBD
- RAM: TBD (recommend 8GB minimum)
- Disk: TBD (recommend 50GB free)
- Network: 192.168.10.0/24

**Required Services**:
- ✅ Docker Engine 24.x+
- ✅ Docker Compose 2.x+
- ✅ Nginx (for reverse proxy)
- ✅ Node.js 20.x+ (for Vite builds - one-time build)
- ✅ Python 3.12+ (for FastAPI backend)

### 3.2 Network Requirements

**Inbound Ports**:
- 80/tcp - HTTP (redirect to HTTPS)
- 443/tcp - HTTPS (AG-UI frontend)
- 3001/tcp - AG-UI frontend (internal)
- 8002/tcp - AG-UI backend (internal)

**Outbound Connectivity**:
- hx-litellm-server:4000 (LiteLLM Gateway)
- hx-orchestrator-server:8000 (Orchestrator API)
- hx-sqldb-server:6379 (Redis Streams)
- hx-vectordb-server:6333 (Qdrant)

### 3.3 Dependencies

**System Packages**:
```yaml
- docker.io (or docker-ce)
- docker-compose-plugin
- nginx
- nodejs (20.x)
- npm
- python3.12
- python3.12-venv
- git
- curl
- jq
```

**Docker Images** (to be built):
```yaml
- shield-ag-ui-frontend:latest (Vite SPA - static build)
- ag-ui-backend:latest (FastAPI app)
- nginx:alpine (reverse proxy)
```

---

## 4. Ansible Role Design

### 4.1 Role Structure

```
roles/
└── ag_ui_app/
    ├── defaults/
    │   └── main.yml                    # Default variables
    ├── tasks/
    │   ├── main.yml                    # Main orchestrator
    │   ├── 01-prerequisites.yml        # System packages, Docker
    │   ├── 02-user-setup.yml           # Service user/group
    │   ├── 03-directories.yml          # App directories
    │   ├── 04-frontend-build.yml       # Vite build (static SPA)
    │   ├── 05-backend-setup.yml        # FastAPI backend
    │   ├── 06-docker-compose.yml       # Docker orchestration
    │   ├── 07-nginx-config.yml         # Reverse proxy
    │   └── 08-service-start.yml        # Start services
    ├── templates/
    │   ├── docker-compose.yml.j2       # Docker Compose config
    │   ├── Dockerfile.frontend.j2      # Vite SPA Dockerfile
    │   ├── Dockerfile.backend.j2       # FastAPI Dockerfile
    │   ├── nginx-ag-ui.conf.j2         # Nginx site config
    │   ├── backend-main.py.j2          # FastAPI application
    │   ├── backend-redis-consumer.py.j2 # Redis Streams consumer
    │   ├── frontend-env.production.j2  # Vite environment variables
    │   └── ag-ui-config.json.j2        # AG-UI configuration
    ├── files/
    │   ├── requirements.txt            # Python dependencies
    │   ├── package.json                # Node.js dependencies
    │   └── .dockerignore               # Docker ignore patterns
    └── handlers/
        └── main.yml                    # Service restart handlers
```

### 4.2 Role Variables

```yaml
# roles/ag_ui_app/defaults/main.yml

# Service configuration
ag_ui_service_user: agui
ag_ui_service_group: agui
ag_ui_user_shell: /bin/bash
ag_ui_user_home: /home/agui

# Application directories
ag_ui_app_dir: /opt/ag-ui
ag_ui_frontend_dir: "{{ ag_ui_app_dir }}/frontend"
ag_ui_backend_dir: "{{ ag_ui_app_dir }}/backend"
ag_ui_data_dir: "{{ ag_ui_app_dir }}/data"
ag_ui_logs_dir: /var/log/ag-ui

# Docker configuration
ag_ui_docker_network: ag-ui-network
ag_ui_compose_file: "{{ ag_ui_app_dir }}/docker-compose.yml"

# Service ports
ag_ui_frontend_port: 3001
ag_ui_backend_port: 8002
ag_ui_nginx_http_port: 80
ag_ui_nginx_https_port: 443

# Frontend configuration (Vite + React)
ag_ui_app_name: "Shield AG-UI"
ag_ui_app_description: "Power User Interface for HX-Citadel Shield"
ag_ui_node_version: "20"
ag_ui_vite_version: "5.4"
ag_ui_react_version: "18"
ag_ui_frontend_source_repo: "https://github.com/hanax-ai/citadel-shield-ui.git"
ag_ui_frontend_source_branch: "feature-1"

# Backend configuration
ag_ui_python_version: "3.12"
ag_ui_fastapi_version: "0.115.0"

# Dependency URLs (FQDN-compliant)
ag_ui_litellm_url: "http://hx-litellm-server:4000"
ag_ui_orchestrator_url: "http://hx-orchestrator-server:8000"
ag_ui_redis_url: "redis://hx-sqldb-server:6379"
ag_ui_qdrant_url: "http://hx-vectordb-server:6333"

# Redis Streams configuration
ag_ui_redis_stream: "shield:events"
ag_ui_redis_consumer_group: "ag-ui-clients"
ag_ui_redis_consumer_name: "{{ ansible_hostname }}"

# LiteLLM API key (for LoB power users)
ag_ui_litellm_api_key: "{{ vault_ag_ui_api_key | default('sk-shield-lob-default') }}"

# AG-UI Protocol configuration
ag_ui_event_stream_path: "/events"
ag_ui_sse_keepalive_interval: 15  # seconds
ag_ui_event_batch_size: 10

# Feature flags
ag_ui_enable_kg_visualization: true
ag_ui_enable_batch_operations: true
ag_ui_enable_kg_curation: true
ag_ui_enable_job_tracking: true

# Performance tuning
ag_ui_max_event_buffer: 1000
ag_ui_websocket_timeout: 300  # seconds
ag_ui_api_timeout: 30  # seconds

# Deployment environment
deployment_environment: dev-test
```

---

## 2. Architecture Overview

### 2.1 Current HX-Citadel Architecture

```
Layer 1: FRONTEND (User Interface)
├── Open WebUI (hx-webui-server:8080) ✅ DEPLOYED
├── shield-power-ui (CopilotKit) ⏭️ PLANNED (Phase 4)
├── shield-ag-ui (AG-UI) ⏭️ THIS PLAN 🎯
└── shield-dashboard ⏭️ PLANNED (Phase 4)
                    ↓
Layer 2: GATEWAY (Access Control)
└── LiteLLM (hx-litellm-server:4000) ✅ DEPLOYED
    • API key-based RBAC
    • tool_choice="required" enforcement
    • Rate limiting & quotas
                    ↓
Layer 3: MCP SERVER (Tool Execution)
└── FastMCP Server (hx-mcp1-server:8081) ✅ DEPLOYED
    • 7 MCP tools operational
    • Circuit breaker protection
    • HTTP 202 async pattern
                    ↓
Layer 4: ORCHESTRATOR (Intelligence Hub)
└── FastAPI Orchestrator (hx-orchestrator-server:8000) ✅ DEPLOYED
    • LightRAG engine
    • LangGraph workflows
    • Pydantic AI agents
    • Task queue & workers
    • Event bus (Redis Streams)
                    ↓
Layer 5: DATA & MODELS
├── Qdrant (hx-vectordb-server:6333) ✅
├── PostgreSQL (hx-sqldb-server:5432) ✅
├── Redis (hx-sqldb-server:6379) ✅
└── Ollama (hx-orchestrator-server:11434, hx-ollama1/2) ✅
```

### 2.2 Shield AG-UI Positioning

**Purpose**: Advanced interface for Line-of-Business power users

**Differentiators from Open WebUI**:

| Feature | Open WebUI | Shield AG-UI |
|---------|------------|--------------|
| **Target Users** | General/casual | LoB power users |
| **Tool Access** | Limited (safe tools only) | Full (all tools) |
| **Real-time Events** | Basic | Full event stream (Redis Streams) |
| **KG Visualization** | No | Yes (D3.js interactive) |
| **Batch Operations** | No | Yes |
| **Job Tracking** | Basic | Advanced dashboard |
| **KG Curation** | No | Yes (entity/relation editing) |
| **Approval Gates** | No | HITL pattern (CopilotKit-inspired) |
| **Quotas** | 100/hour | 1000/hour |

### 2.3 AG-UI Protocol Integration

**What is AG-UI?**
- Event-based protocol for agent-user interaction
- 16 standard event types (text, tool, state, progress, etc.)
- Bi-directional state synchronization
- Real-time streaming (SSE/WebSocket)
- Compatible with LangGraph, Pydantic AI, CrewAI, etc.

**How it Works in Shield**:

```
User Action → AG-UI Frontend → Backend API → LiteLLM → MCP → Orchestrator
                                    ↓                            ↓
                           (SSE connection)              (Redis Streams)
                                    ↑                            ↓
                                    ← Events ← Consumer ← Events Published
```

**Event Flow Example**:
1. User clicks "Crawl Web" in AG-UI
2. Frontend calls `/api/crawl` with parameters
3. Backend forwards to LiteLLM → MCP → Orchestrator
4. Orchestrator returns HTTP 202 + job_id
5. Worker processes asynchronously
6. Events published to Redis Streams (`shield:events`)
7. ag-ui-backend consumes events
8. Events transformed to AG-UI protocol format
9. Streamed to frontend via SSE
10. UI updates in real-time (progress, results, KG changes)

---

## 3. Infrastructure Requirements

### 3.1 Server Preparation Checklist

**hx-dev-server (192.168.10.12)**:

- [ ] Verify Ubuntu 24.04 LTS
- [ ] Check available disk space (>50GB recommended)
- [ ] Check available RAM (>8GB recommended)
- [ ] Verify network connectivity to all services
- [ ] SSH access configured (agent0 user)
- [ ] Sudo privileges available

### 3.2 Package Requirements

**System Packages** (via apt):
```yaml
required_packages:
  # Docker
  - docker.io
  - docker-compose-plugin
  - docker-buildx-plugin
  
  # Web server
  - nginx
  - certbot  # For SSL if needed
  - python3-certbot-nginx
  
  # Build tools
  - build-essential
  - git
  - curl
  - wget
  
  # Node.js ecosystem
  - nodejs (20.x from NodeSource)
  - npm
  
  # Python
  - python3.12
  - python3.12-venv
  - python3.12-dev
  - python3-pip
  
  # Utilities
  - jq
  - redis-tools  # For testing Redis connectivity
  - postgresql-client  # For testing DB connectivity
```

### 3.3 Python Dependencies

**ag-ui-backend** (`requirements.txt`):
```txt
# Web framework
fastapi==0.115.0
uvicorn[standard]==0.30.0

# AG-UI Protocol
ag-ui-protocol==0.1.0  # AG-UI Python SDK

# Redis Streams
redis==5.0.0
redis-py-cluster==2.1.3  # If using Redis cluster

# HTTP client
httpx==0.27.0

# Data validation
pydantic==2.7.0
pydantic-settings==2.2.0

# Async support
asyncio-redis==0.16.0

# Monitoring
prometheus-client==0.20.0

# Utilities
python-dotenv==1.0.0
```

### 3.4 Node.js Dependencies

**shield-ag-ui** (`package.json`):
```json
{
  "name": "shield-ag-ui",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3001",
    "build": "next build",
    "start": "next start -p 3001",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@ag-ui/core": "^0.1.0",
    "@ag-ui/react": "^0.1.0",
    "zustand": "^4.5.0",
    "zod": "^3.23.0",
    "d3": "^7.9.0",
    "@types/d3": "^7.4.3",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@types/node": "^20.0.0",
    "@types/react": "^18.3.0",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0"
  }
}
```

---

## 4. Ansible Role Design (Detailed)

### 4.1 Task Files Breakdown

#### **tasks/main.yml** - Orchestrator
```yaml
---
# Main deployment orchestrator for AG-UI application

- name: Display deployment information
  ansible.builtin.debug:
    msg: |
      ╔════════════════════════════════════════════════════════════╗
      ║        Shield AG-UI Deployment Starting                    ║
      ╠════════════════════════════════════════════════════════════╣
      ║  Target: {{ ansible_hostname }} ({{ ansible_host }})
      ║  Frontend Port: {{ ag_ui_frontend_port }}
      ║  Backend Port: {{ ag_ui_backend_port }}
      ║  Nginx HTTP: {{ ag_ui_nginx_http_port }}
      ║  LiteLLM: {{ ag_ui_litellm_url }}
      ║  Orchestrator: {{ ag_ui_orchestrator_url }}
      ║  Redis: {{ ag_ui_redis_url }}
      ╚════════════════════════════════════════════════════════════╝

- name: Include prerequisites tasks
  ansible.builtin.include_tasks: 01-prerequisites.yml

- name: Include user setup tasks
  ansible.builtin.include_tasks: 02-user-setup.yml

- name: Include directory setup tasks
  ansible.builtin.include_tasks: 03-directories.yml

- name: Include frontend build tasks
  ansible.builtin.include_tasks: 04-frontend-build.yml

- name: Include backend setup tasks
  ansible.builtin.include_tasks: 05-backend-setup.yml

- name: Include Docker Compose tasks
  ansible.builtin.include_tasks: 06-docker-compose.yml

- name: Include Nginx configuration tasks
  ansible.builtin.include_tasks: 07-nginx-config.yml

- name: Include service start tasks
  ansible.builtin.include_tasks: 08-service-start.yml

- name: Display deployment completion
  ansible.builtin.debug:
    msg: |
      ╔════════════════════════════════════════════════════════════╗
      ║        Shield AG-UI Deployment Complete                    ║
      ╠════════════════════════════════════════════════════════════╣
      ║  Frontend: http://{{ ansible_host }}:{{ ag_ui_frontend_port }}
      ║  Backend API: http://{{ ansible_host }}:{{ ag_ui_backend_port }}
      ║  Nginx Proxy: http://{{ ansible_host }}
      ║  
      ║  Next Steps:
      ║  1. Access UI: http://{{ ansible_host }}
      ║  2. Check logs: docker-compose -f {{ ag_ui_compose_file }} logs -f
      ║  3. Verify events: curl {{ ansible_host }}:{{ ag_ui_backend_port }}/events
      ║  4. Test MCP integration
      ╚════════════════════════════════════════════════════════════╝
```

#### **tasks/01-prerequisites.yml** - System Setup
```yaml
---
# Install system prerequisites and Docker

- name: Install system prerequisites with error handling
  block:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: yes
        cache_valid_time: 3600
      become: yes

    - name: Install Docker and dependencies
      ansible.builtin.apt:
        name:
          - docker.io
          - docker-compose-plugin
          - docker-buildx-plugin
          - nginx
          - git
          - curl
          - jq
          - redis-tools
          - build-essential
        state: present
      become: yes

    - name: Add NodeSource repository for Node.js 20.x
      ansible.builtin.shell: |
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
      become: yes
      args:
        creates: /etc/apt/sources.list.d/nodesource.list

    - name: Install Node.js and npm
      ansible.builtin.apt:
        name:
          - nodejs
        state: present
      become: yes

    - name: Install Python 3.12 and development tools
      ansible.builtin.apt:
        name:
          - python3.12
          - python3.12-venv
          - python3.12-dev
          - python3-pip
        state: present
      become: yes

    - name: Verify Docker is running
      ansible.builtin.systemd:
        name: docker
        state: started
        enabled: yes
      become: yes

  rescue:
    - name: Log prerequisites installation failure
      ansible.builtin.debug:
        msg: "⚠️  Prerequisites installation failed. Check package availability."
    
    - name: Fail deployment
      ansible.builtin.fail:
        msg: "Cannot proceed without required system packages"

  always:
    - name: Display installed versions
      ansible.builtin.debug:
        msg: |
          Installed versions:
          Docker: {{ docker_version.stdout | default('unknown') }}
          Node.js: {{ nodejs_version.stdout | default('unknown') }}
          Python: {{ python_version.stdout | default('unknown') }}
```

#### **tasks/02-user-setup.yml** - Service User
```yaml
---
# Create service user and group for AG-UI

- name: Create AG-UI service group
  ansible.builtin.group:
    name: "{{ ag_ui_service_group }}"
    state: present
    system: yes
  become: yes

- name: Create AG-UI service user
  ansible.builtin.user:
    name: "{{ ag_ui_service_user }}"
    group: "{{ ag_ui_service_group }}"
    shell: "{{ ag_ui_user_shell }}"
    home: "{{ ag_ui_user_home }}"
    create_home: yes
    system: yes
    comment: "AG-UI application service user"
  become: yes

- name: Add service user to docker group
  ansible.builtin.user:
    name: "{{ ag_ui_service_user }}"
    groups: docker
    append: yes
  become: yes

- name: Verify user can run docker
  ansible.builtin.shell: |
    su - {{ ag_ui_service_user }} -c "docker ps"
  become: yes
  register: docker_test
  failed_when: false
  changed_when: false
```

#### **tasks/03-directories.yml** - Directory Structure
```yaml
---
# Create application directories

- name: Create AG-UI application directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    owner: "{{ ag_ui_service_user }}"
    group: "{{ ag_ui_service_group }}"
    mode: '0755'
  become: yes
  loop:
    - "{{ ag_ui_app_dir }}"
    - "{{ ag_ui_frontend_dir }}"
    - "{{ ag_ui_backend_dir }}"
    - "{{ ag_ui_data_dir }}"
    - "{{ ag_ui_logs_dir }}"
    - "{{ ag_ui_app_dir }}/nginx"

- name: Create Docker network
  community.docker.docker_network:
    name: "{{ ag_ui_docker_network }}"
    state: present
  become: yes
```

---

## 5. Implementation Tasks

### 5.1 Phase 1: Foundation (Day 1-2)

**Sprint A: Infrastructure Setup**

| Task ID | Task Name | Effort | Dependencies | Deliverable |
|---------|-----------|--------|--------------|-------------|
| **DEV-001** | Create ag_ui_app Ansible role | 2 hours | None | Role structure created |
| **DEV-002** | Install Docker & prerequisites | 1 hour | DEV-001 | Docker running on dev-server |
| **DEV-003** | Setup service user (agui) | 30 min | DEV-002 | User with docker access |
| **DEV-004** | Create directory structure | 30 min | DEV-003 | App directories ready |
| **DEV-005** | Configure Docker network | 30 min | DEV-004 | ag-ui-network created |

### 5.2 Phase 2: Backend Development (Day 2-4)

**Sprint B: AG-UI Backend (FastAPI)**

| Task ID | Task Name | Effort | Dependencies | Deliverable |
|---------|-----------|--------|--------------|-------------|
| **DEV-006** | Create FastAPI backend template | 3 hours | DEV-005 | backend-main.py.j2 |
| **DEV-007** | Implement Redis Streams consumer | 4 hours | DEV-006 | Real-time event subscription |
| **DEV-008** | Create AG-UI protocol adapter | 4 hours | DEV-007 | Event transformation layer |
| **DEV-009** | Add SSE endpoint for events | 2 hours | DEV-008 | /events SSE streaming |
| **DEV-010** | Implement LiteLLM proxy client | 2 hours | DEV-006 | Tool execution via LiteLLM |
| **DEV-011** | Add health & monitoring endpoints | 1 hour | DEV-010 | /health, /metrics ready |
| **DEV-012** | Create backend Dockerfile | 2 hours | DEV-011 | Dockerfile.backend.j2 |

### 5.3 Phase 3: Frontend Development (Day 4-7)

**Sprint C: AG-UI Frontend Integration (Vite + React)**

| Task ID | Task Name | Effort | Dependencies | Deliverable |
|---------|-----------|--------|--------------|-------------|
| **DEV-013** | Clone and integrate existing Vite frontend | 2 hours | DEV-005 | Vite app ready |
| **DEV-014** | Integrate AG-UI React SDK | 3 hours | DEV-013 | @ag-ui/react configured |
| **DEV-015** | Create chat interface component | 4 hours | DEV-014 | Chat UI with streaming |
| **DEV-016** | Build event timeline component | 4 hours | DEV-014 | Real-time event display |
| **DEV-017** | Implement D3.js KG visualization | 6 hours | DEV-015 | Interactive graph view |
| **DEV-018** | Create job tracking dashboard | 4 hours | DEV-016 | Job status UI |
| **DEV-019** | Build tool parameter forms | 3 hours | DEV-015 | Advanced tool controls |
| **DEV-020** | Add KG curation interface | 4 hours | DEV-017 | Entity/relation editing |
| **DEV-021** | Create frontend Dockerfile | 2 hours | DEV-020 | Dockerfile.frontend.j2 |

### 5.4 Phase 4: Integration & Deployment (Day 7-9)

**Sprint D: Docker & Nginx**

| Task ID | Task Name | Effort | Dependencies | Deliverable |
|---------|-----------|--------|--------------|-------------|
| **DEV-022** | Create Docker Compose config | 3 hours | DEV-012, DEV-021 | docker-compose.yml.j2 |
| **DEV-023** | Configure Nginx reverse proxy | 2 hours | DEV-022 | nginx-ag-ui.conf.j2 |
| **DEV-024** | Setup SSL/TLS (self-signed for dev) | 1 hour | DEV-023 | HTTPS enabled |
| **DEV-025** | Deploy via Ansible playbook | 2 hours | DEV-024 | deploy-ag-ui.yml |
| **DEV-026** | Verify service health | 1 hour | DEV-025 | All containers healthy |
| **DEV-027** | Test event streaming | 2 hours | DEV-026 | Events flowing to UI |
| **DEV-028** | Test tool execution | 2 hours | DEV-027 | All 7 tools working |

### 5.5 Phase 5: Testing & Documentation (Day 9-10)

**Sprint E: Validation & Docs**

| Task ID | Task Name | Effort | Dependencies | Deliverable |
|---------|-----------|--------|--------------|-------------|
| **DEV-029** | E2E testing (Playwright) | 4 hours | DEV-028 | Test suite passing |
| **DEV-030** | Load testing | 2 hours | DEV-029 | Performance baseline |
| **DEV-031** | Create user documentation | 3 hours | DEV-028 | User guide |
| **DEV-032** | Create deployment runbook | 2 hours | DEV-031 | Ops runbook |
| **DEV-033** | Update architecture docs | 1 hour | DEV-032 | Docs updated |

**Total Tasks**: 33  
**Total Effort**: ~60 hours (~10 development days)

---

## 6. Docker Configuration

### 6.1 Docker Compose Stack

**File**: `templates/docker-compose.yml.j2`

```yaml
version: '3.9'

services:
  # AG-UI Frontend (Vite + React - existing)
  frontend:
    build:
      context: {{ ag_ui_frontend_dir }}
      dockerfile: Dockerfile
    image: shield-ag-ui:latest
    container_name: shield-ag-ui-frontend
    restart: unless-stopped
    ports:
      - "{{ ag_ui_frontend_port }}:3001"
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_API_URL: http://{{ ansible_host }}:{{ ag_ui_backend_port }}
      NEXT_PUBLIC_EVENT_STREAM_URL: http://{{ ansible_host }}:{{ ag_ui_backend_port }}/events
      NEXT_PUBLIC_APP_NAME: "{{ ag_ui_app_name }}"
    networks:
      - {{ ag_ui_docker_network }}
    volumes:
      - {{ ag_ui_logs_dir }}/frontend:/app/.next/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      - backend

  # AG-UI Backend (FastAPI)
  backend:
    build:
      context: {{ ag_ui_backend_dir }}
      dockerfile: Dockerfile
    image: ag-ui-backend:latest
    container_name: shield-ag-ui-backend
    restart: unless-stopped
    ports:
      - "{{ ag_ui_backend_port }}:8002"
    environment:
      PYTHON_ENV: production
      LOG_LEVEL: INFO
      
      # Service URLs (FQDN-compliant)
      LITELLM_URL: "{{ ag_ui_litellm_url }}"
      ORCHESTRATOR_URL: "{{ ag_ui_orchestrator_url }}"
      REDIS_URL: "{{ ag_ui_redis_url }}"
      QDRANT_URL: "{{ ag_ui_qdrant_url }}"
      
      # Redis Streams config
      REDIS_STREAM_NAME: "{{ ag_ui_redis_stream }}"
      REDIS_CONSUMER_GROUP: "{{ ag_ui_redis_consumer_group }}"
      REDIS_CONSUMER_NAME: "{{ ag_ui_redis_consumer_name }}"
      
      # API authentication
      LITELLM_API_KEY: "{{ ag_ui_litellm_api_key }}"
      
      # AG-UI protocol config
      EVENT_STREAM_PATH: "{{ ag_ui_event_stream_path }}"
      SSE_KEEPALIVE_INTERVAL: "{{ ag_ui_sse_keepalive_interval }}"
      EVENT_BATCH_SIZE: "{{ ag_ui_event_batch_size }}"
    networks:
      - {{ ag_ui_docker_network }}
    volumes:
      - {{ ag_ui_data_dir }}:/app/data
      - {{ ag_ui_logs_dir }}/backend:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: shield-ag-ui-nginx
    restart: unless-stopped
    ports:
      - "{{ ag_ui_nginx_http_port }}:80"
      - "{{ ag_ui_nginx_https_port }}:443"
    volumes:
      - {{ ag_ui_app_dir }}/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - {{ ag_ui_app_dir }}/nginx/ag-ui.conf:/etc/nginx/conf.d/default.conf:ro
      - {{ ag_ui_logs_dir }}/nginx:/var/log/nginx
    networks:
      - {{ ag_ui_docker_network }}
    depends_on:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  {{ ag_ui_docker_network }}:
    driver: bridge
    name: {{ ag_ui_docker_network }}
```

### 6.2 Frontend Dockerfile

**File**: `templates/Dockerfile.frontend.j2`

```dockerfile
# Multi-stage build for Vite SPA application
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment for build
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build Vite application (static SPA)
RUN npm run build

# Production image, copy all files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3001

ENV PORT 3001
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### 6.3 Backend Dockerfile

**File**: `templates/Dockerfile.backend.j2`

```dockerfile
# Python backend for AG-UI protocol adapter
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 agui && chown -R agui:agui /app
USER agui

# Expose backend port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
```

---

## 7. Integration Points

### 7.1 Backend Integration (FastAPI)

**File**: `templates/backend-main.py.j2`

```python
#!/usr/bin/env python3
"""
Shield AG-UI Backend - FastAPI Application
AG-UI Protocol adapter for HX-Citadel Shield

Features:
- Redis Streams consumer for real-time events
- SSE endpoint for frontend event streaming
- LiteLLM proxy for tool execution
- AG-UI protocol event transformation
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ag_ui.core import (
    TextMessageContentEvent,
    ToolCallEvent,
    ToolResultEvent,
    StateUpdateEvent,
    EventType
)
from ag_ui.encoder import EventEncoder
import redis.asyncio as redis
import httpx
import asyncio
import json
import os
from typing import AsyncGenerator
from datetime import datetime

# Configuration from environment
LITELLM_URL = os.getenv("LITELLM_URL", "http://hx-litellm-server:4000")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://hx-orchestrator-server:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://hx-sqldb-server:6379")
REDIS_STREAM = os.getenv("REDIS_STREAM_NAME", "shield:events")
REDIS_CONSUMER_GROUP = os.getenv("REDIS_CONSUMER_GROUP", "ag-ui-clients")
REDIS_CONSUMER_NAME = os.getenv("REDIS_CONSUMER_NAME", "{{ ansible_hostname }}")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-shield-lob-default")

app = FastAPI(title="Shield AG-UI Backend")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client (global)
redis_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection and consumer group"""
    global redis_client
    redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    
    # Create consumer group if not exists
    try:
        await redis_client.xgroup_create(
            REDIS_STREAM,
            REDIS_CONSUMER_GROUP,
            id="0",
            mkstream=True
        )
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection"""
    if redis_client:
        await redis_client.close()

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = False
    litellm_ok = False
    orchestrator_ok = False
    
    # Check Redis
    try:
        await redis_client.ping()
        redis_ok = True
    except Exception:
        pass
    
    # Check LiteLLM
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{LITELLM_URL}/health", timeout=5.0)
            litellm_ok = resp.status_code == 200
    except Exception:
        pass
    
    # Check Orchestrator
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ORCHESTRATOR_URL}/health", timeout=5.0)
            orchestrator_ok = resp.status_code == 200
    except Exception:
        pass
    
    status = "healthy" if all([redis_ok, litellm_ok, orchestrator_ok]) else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "redis": "ok" if redis_ok else "unavailable",
            "litellm": "ok" if litellm_ok else "unavailable",
            "orchestrator": "ok" if orchestrator_ok else "unavailable"
        }
    }

# SSE Event Stream
@app.get("/events")
async def event_stream(request: Request):
    """
    Server-Sent Events endpoint for real-time updates.
    Consumes from Redis Streams and transforms to AG-UI protocol.
    """
    async def generate_events() -> AsyncGenerator[str, None]:
        encoder = EventEncoder()
        last_id = ">"  # Start from new messages
        
        # Send connection established event
        welcome_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="sys_" + str(int(datetime.utcnow().timestamp())),
            delta="Connected to Shield AG-UI event stream"
        )
        yield encoder.encode(welcome_event)
        
        # Consume events from Redis Streams
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            try:
                # Read from stream
                messages = await redis_client.xreadgroup(
                    groupname=REDIS_CONSUMER_GROUP,
                    consumername=REDIS_CONSUMER_NAME,
                    streams={REDIS_STREAM: last_id},
                    count=10,
                    block=5000  # 5 second timeout
                )
                
                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, data in stream_messages:
                            last_id = message_id
                            
                            # Transform to AG-UI event
                            ag_ui_event = transform_to_agui_event(data)
                            if ag_ui_event:
                                yield encoder.encode(ag_ui_event)
                            
                            # Acknowledge message
                            await redis_client.xack(
                                REDIS_STREAM,
                                REDIS_CONSUMER_GROUP,
                                message_id
                            )
                
                # Keep-alive ping
                yield ": keepalive\n\n"
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but don't break stream
                error_event = TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id="err_" + str(int(datetime.utcnow().timestamp())),
                    delta=f"Stream error: {str(e)}"
                )
                yield encoder.encode(error_event)
                await asyncio.sleep(1)
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

def transform_to_agui_event(redis_data: dict):
    """
    Transform Redis Stream event to AG-UI protocol event.
    
    Maps Shield events to AG-UI event types:
    - tool:start → TOOL_CALL
    - tool:progress → STATE_UPDATE
    - tool:complete → TOOL_RESULT
    - rag:chunk_processed → TEXT_MESSAGE_CONTENT
    - rag:graph_updated → STATE_UPDATE
    """
    event_type = redis_data.get("type", "")
    
    # Map event types
    if event_type == "tool:start":
        return ToolCallEvent(
            type=EventType.TOOL_CALL,
            message_id=redis_data.get("message_id"),
            tool_call_id=redis_data.get("tool_call_id"),
            tool_name=redis_data.get("tool_name"),
            arguments=json.loads(redis_data.get("arguments", "{}"))
        )
    
    elif event_type in ["tool:progress", "rag:graph_updated"]:
        return StateUpdateEvent(
            type=EventType.STATE_UPDATE,
            message_id=redis_data.get("message_id"),
            state_key=redis_data.get("state_key", "progress"),
            state_value=json.loads(redis_data.get("state_value", "{}"))
        )
    
    elif event_type == "tool:complete":
        return ToolResultEvent(
            type=EventType.TOOL_RESULT,
            message_id=redis_data.get("message_id"),
            tool_call_id=redis_data.get("tool_call_id"),
            result=redis_data.get("result")
        )
    
    elif event_type.startswith("rag:"):
        # Text updates for RAG events
        return TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=redis_data.get("message_id"),
            delta=redis_data.get("message", "")
        )
    
    return None

# Tool execution endpoints
@app.post("/api/crawl")
async def execute_crawl(request: Request):
    """Proxy tool execution to LiteLLM"""
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LITELLM_URL}/chat/completions",
            json={
                "model": "gpt-4",  # Model doesn't matter, tools enforced
                "messages": [{"role": "user", "content": body.get("url")}],
                "tools": [{"type": "function", "function": {"name": "crawl_web"}}],
                "tool_choice": {"type": "function", "function": {"name": "crawl_web"}},
            },
            headers={"Authorization": f"Bearer {LITELLM_API_KEY}"}
        )
        return response.json()

# Similar endpoints for other tools...
```

### 7.2 Frontend Integration (Vite + React + shadcn-ui)

**Example Component**: `components/AgentChat.tsx`

```typescript
'use client';

import { useAgentChat } from '@ag-ui/react';
import { EventTimeline } from './EventTimeline';
import { KnowledgeGraphViz } from './KnowledgeGraphViz';

export function AgentChat() {
  const {
    messages,
    events,
    state,
    sendMessage,
    isStreaming
  } = useAgentChat({
    apiUrl: process.env.NEXT_PUBLIC_API_URL,
    eventStreamUrl: process.env.NEXT_PUBLIC_EVENT_STREAM_URL,
  });

  return (
    <div className="grid grid-cols-3 gap-4 h-screen">
      {/* Chat Interface */}
      <div className="col-span-2 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
        </div>
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>
      
      {/* Sidebar */}
      <div className="col-span-1 flex flex-col gap-4 p-4 bg-gray-50">
        {/* Real-time Event Timeline */}
        <EventTimeline events={events} />
        
        {/* Knowledge Graph Visualization */}
        {state.knowledge_graph && (
          <KnowledgeGraphViz data={state.knowledge_graph} />
        )}
        
        {/* Job Tracking */}
        {state.active_jobs && (
          <JobTracker jobs={state.active_jobs} />
        )}
      </div>
    </div>
  );
}
```

### 7.3 Redis Streams Integration

**Consumer Pattern**:

```python
async def consume_redis_events():
    """
    Background task to consume Redis Streams events.
    Transforms and broadcasts to connected SSE clients.
    """
    while True:
        try:
            messages = await redis_client.xreadgroup(
                groupname=REDIS_CONSUMER_GROUP,
                consumername=REDIS_CONSUMER_NAME,
                streams={REDIS_STREAM: ">"},  # Only new messages
                count=10,
                block=5000
            )
            
            for stream, stream_messages in messages:
                for msg_id, data in stream_messages:
                    # Transform to AG-UI event
                    event = transform_to_agui_event(data)
                    
                    # Broadcast to all connected SSE clients
                    await broadcast_event(event)
                    
                    # Acknowledge
                    await redis_client.xack(
                        REDIS_STREAM,
                        REDIS_CONSUMER_GROUP,
                        msg_id
                    )
        
        except Exception as e:
            logger.error(f"Redis consumer error: {e}")
            await asyncio.sleep(5)  # Back off on error
```

---

## 8. Security & Access Control

### 8.1 API Key Management

**LiteLLM API Key** (for AG-UI users):
```yaml
# In Ansible vault (group_vars/all/vault.yml)
vault_ag_ui_api_key: sk-shield-lob-team-alpha

# Permissions in LiteLLM config
lob-guardrail:
  api_key_pattern: "sk-shield-lob-*"
  default_action: "deny"
  allow:
    - function: "crawl_web"
    - function: "ingest_doc"
    - function: "qdrant_find"
    - function: "qdrant_store"
    - function: "lightrag_query"
    - function: "get_job_status"
    - function: "health_check"
    - function: "kg_curate"  # NEW - AG-UI only
  rate_limit:
    max_requests_per_hour: 1000
```

### 8.2 Network Security

**Firewall Rules** (ufw):
```yaml
- name: Configure UFW for AG-UI
  community.general.ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - 80   # HTTP
    - 443  # HTTPS
    - 3001 # Frontend (internal only - restrict in production)
    - 8002 # Backend (internal only - restrict in production)
  become: yes
```

### 8.3 Docker Security

**Docker Compose Security**:
```yaml
# Read-only filesystem where possible
read_only: true

# Drop capabilities
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE

# Security options
security_opt:
  - no-new-privileges:true

# Resource limits
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '0.5'
      memory: 1G
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Backend Tests** (`tests/test_backend.py`):
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_event_stream_connection():
    """Test SSE connection establishes"""
    with client.stream("GET", "/events") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

def test_redis_event_transformation():
    """Test Redis event → AG-UI event transformation"""
    redis_event = {
        "type": "tool:start",
        "tool_name": "crawl_web",
        "message_id": "msg_123",
        "tool_call_id": "call_456",
        "arguments": '{"url": "https://example.com"}'
    }
    
    agui_event = transform_to_agui_event(redis_event)
    assert agui_event.type == EventType.TOOL_CALL
    assert agui_event.tool_name == "crawl_web"
```

### 9.2 Integration Tests

**E2E Tests** (`tests/e2e/test_crawl_workflow.spec.ts`):
```typescript
import { test, expect } from '@playwright/test';

test('AG-UI crawl workflow with real-time events', async ({ page }) => {
  // Navigate to AG-UI
  await page.goto('http://hx-dev-server:3001');
  
  // Login (if auth implemented)
  // await login(page);
  
  // Start crawl
  await page.fill('[data-testid="crawl-url"]', 'https://example.com');
  await page.fill('[data-testid="crawl-max-pages"]', '5');
  await page.click('[data-testid="crawl-submit"]');
  
  // Wait for HTTP 202 response
  await expect(page.locator('[data-testid="job-id"]')).toBeVisible();
  const jobId = await page.locator('[data-testid="job-id"]').textContent();
  
  // Verify real-time events appear
  await expect(page.locator('[data-testid="event-timeline"]')).toBeVisible();
  
  // Wait for events (with timeout)
  await page.waitForSelector(
    '[data-testid="event-type-tool_call"]',
    { timeout: 10000 }
  );
  
  // Verify progress updates
  await expect(
    page.locator('[data-testid="progress-bar"]')
  ).toHaveAttribute('aria-valuenow', /[1-9]\d*/);
  
  // Verify knowledge graph updates
  await page.waitForSelector('[data-testid="kg-node"]', { timeout: 30000 });
  const nodes = await page.locator('[data-testid="kg-node"]').count();
  expect(nodes).toBeGreaterThan(0);
});
```

### 9.3 Load Tests

**Locust Test** (`tests/load/locustfile.py`):
```python
from locust import HttpUser, task, between
import json

class AGUIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Establish SSE connection"""
        self.sse_conn = self.client.get(
            "/events",
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
    
    @task(3)
    def query_lightrag(self):
        """Execute LightRAG query"""
        self.client.post("/api/query", json={
            "query": "What is Python?",
            "mode": "hybrid"
        })
    
    @task(1)
    def crawl_web(self):
        """Execute web crawl"""
        self.client.post("/api/crawl", json={
            "url": "https://example.com",
            "max_pages": 5
        })
```

---

## 10. Deployment Timeline

### 10.1 Phased Deployment (10 days)

```
Week 1 (Days 1-5): Foundation & Backend
├── Day 1: Infrastructure setup (DEV-001 to DEV-005)
│   └─> Ansible role created, Docker installed, directories ready
├── Day 2: Backend development starts (DEV-006 to DEV-008)
│   └─> FastAPI app, Redis consumer, AG-UI adapter
├── Day 3: Backend development continues (DEV-009 to DEV-011)
│   └─> SSE endpoint, LiteLLM client, monitoring
├── Day 4: Backend deployment (DEV-012)
│   └─> Dockerfile created, backend containerized
└── Day 5: Frontend setup begins (DEV-013 to DEV-014)
    └─> Vite app cloned, Supabase removed, backend API integrated

Week 2 (Days 6-10): Frontend & Integration
├── Day 6: Frontend components (DEV-015 to DEV-016)
│   └─> Chat interface, event timeline
├── Day 7: Advanced features (DEV-017 to DEV-019)
│   └─> KG visualization, job tracking, tool forms
├── Day 8: KG curation + Docker (DEV-020 to DEV-022)
│   └─> Entity editing, Docker Compose, frontend Dockerfile
├── Day 9: Nginx + deployment (DEV-023 to DEV-028)
│   └─> Reverse proxy, SSL, full stack deployed, tested
└── Day 10: Testing + docs (DEV-029 to DEV-033)
    └─> E2E tests, load tests, documentation complete

🎉 DEPLOYMENT COMPLETE
```

### 10.2 Milestone Checkpoints

| Milestone | Day | Deliverables | Success Criteria |
|-----------|-----|--------------|------------------|
| **M1: Infrastructure Ready** | 1 | Docker, user, directories | Ansible role works, Docker running |
| **M2: Backend Operational** | 4 | FastAPI backend in Docker | Health check passes, Redis consuming |
| **M3: Frontend Deployed** | 7 | Vite SPA in Docker (nginx) | UI accessible, static content loads |
| **M4: Integration Complete** | 9 | Full stack with Nginx | Events streaming, tools working |
| **M5: Production Ready** | 10 | Tests passing, docs complete | All acceptance criteria met |

---

## 11. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **AG-UI SDK compatibility** | Medium | High | Test with latest SDK version, review docs |
| **Redis Streams performance** | Low | Medium | Load test event streaming, tune buffer sizes |
| **Docker resource constraints** | Medium | Medium | Set resource limits, monitor usage |
| **Frontend build complexity** | Low | Low | Use multi-stage Docker build, cache layers |
| **Event transformation errors** | Medium | High | Comprehensive error handling, schema validation |
| **Network latency (SSE)** | Low | Medium | Keep-alive pings, connection pooling |

---

## 12. Success Criteria

### 12.1 Technical Acceptance

- [ ] All 3 Docker containers (frontend, backend, nginx) running healthy
- [ ] SSE event stream delivering events to frontend < 100ms latency
- [ ] All 7 MCP tools executable via AG-UI
- [ ] Knowledge graph visualization displaying nodes and edges
- [ ] Job tracking dashboard showing active/completed jobs
- [ ] Health endpoints returning "healthy" status
- [ ] No critical vulnerabilities in Docker images
- [ ] Resource usage < 4GB RAM, < 2 CPU cores
- [ ] 99%+ uptime over 24 hour test period

### 12.2 Functional Acceptance

- [ ] User can execute web crawl and see real-time progress
- [ ] User can ingest documents and track job status
- [ ] User can query LightRAG and see results + KG
- [ ] User can visualize and navigate knowledge graph
- [ ] User can curate KG (edit/merge/delete entities)
- [ ] User can view event timeline with filtering
- [ ] User can execute batch operations
- [ ] User receives error messages for failed operations

### 12.3 Performance Acceptance

- [ ] Page load < 2 seconds
- [ ] SSE connection establishes < 500ms
- [ ] Event delivery latency < 100ms
- [ ] Tool execution response < 5 seconds (excluding long-running jobs)
- [ ] Support 10+ concurrent users
- [ ] Handle 1000 events/minute

---

## 13. Deployment Playbook

### 13.1 Main Playbook

**File**: `playbooks/deploy-ag-ui.yml`

```yaml
---
# Deploy Shield AG-UI application on hx-dev-server

- name: Deploy Shield AG-UI (Power User Interface)
  hosts: hx-dev-server
  become: yes
  gather_facts: yes
  
  vars:
    ag_ui_app_name: "Shield AG-UI"
    ag_ui_frontend_port: 3001
    ag_ui_backend_port: 8002
  
  pre_tasks:
    - name: Verify server specifications
      ansible.builtin.assert:
        that:
          - ansible_distribution == "Ubuntu"
          - ansible_distribution_version is version('24.04', '>=')
          - ansible_memtotal_mb >= 8192  # 8GB minimum
          - ansible_mounts | selectattr('mount', 'equalto', '/') | map(attribute='size_available') | first > 53687091200  # 50GB
        fail_msg: "Server does not meet minimum requirements"
    
    - name: Test connectivity to all dependencies
      ansible.builtin.uri:
        url: "{{ item.url }}"
        method: GET
        status_code: [200, 404]  # 404 OK for some endpoints
        timeout: 5
      loop:
        - { name: "LiteLLM", url: "http://hx-litellm-server:4000/health" }
        - { name: "Orchestrator", url: "http://hx-orchestrator-server:8000/health" }
        - { name: "Qdrant", url: "http://hx-vectordb-server:6333" }
      register: connectivity_tests
      failed_when: false
    
    - name: Display connectivity results
      ansible.builtin.debug:
        msg: "{{ item.item.name }}: {{ 'OK' if item.status in [200, 404] else 'FAILED' }}"
      loop: "{{ connectivity_tests.results }}"
  
  roles:
    - role: ag_ui_app
      tags: ['ag-ui', 'frontend']
  
  post_tasks:
    - name: Wait for services to be ready
      ansible.builtin.wait_for:
        host: "{{ ansible_host }}"
        port: "{{ item }}"
        delay: 5
        timeout: 60
      loop:
        - "{{ ag_ui_frontend_port }}"
        - "{{ ag_ui_backend_port }}"
        - 80
    
    - name: Verify Docker containers are healthy
      ansible.builtin.shell: |
        docker ps --filter "name=shield-ag-ui" --format "table {{.Names}}\t{{.Status}}" | grep -c "healthy"
      register: healthy_containers
      retries: 5
      delay: 10
      until: healthy_containers.stdout | int >= 3
      failed_when: false
    
    - name: Test SSE event stream
      ansible.builtin.uri:
        url: "http://{{ ansible_host }}:{{ ag_ui_backend_port }}/events"
        method: GET
        timeout: 5
        return_content: yes
      register: sse_test
      failed_when: false
    
    - name: Display deployment summary
      ansible.builtin.debug:
        msg: |
          ╔════════════════════════════════════════════════════════════╗
          ║     Shield AG-UI Deployment Summary                        ║
          ╠════════════════════════════════════════════════════════════╣
          ║  Frontend URL: http://{{ ansible_host }}:{{ ag_ui_frontend_port }}
          ║  Backend API: http://{{ ansible_host }}:{{ ag_ui_backend_port }}
          ║  Nginx Proxy: http://{{ ansible_host }}
          ║  
          ║  Container Health: {{ healthy_containers.stdout | default('unknown') }}/3
          ║  SSE Stream: {{ 'OK' if sse_test.status == 200 else 'Check logs' }}
          ║  
          ║  Status: {{ 'READY ✅' if (healthy_containers.stdout | default(0) | int) == 3 else 'CHECK LOGS ⚠️' }}
          ╚════════════════════════════════════════════════════════════╝
```

---

## 14. Monitoring & Observability

### 14.1 Health Checks

**Container Health**:
```bash
# Check all containers
docker-compose -f /opt/ag-ui/docker-compose.yml ps

# Check logs
docker-compose -f /opt/ag-ui/docker-compose.yml logs -f backend

# Check specific container
docker exec shield-ag-ui-backend curl http://localhost:8002/health
```

### 14.2 Prometheus Metrics

**Backend Metrics** (expose at `/metrics`):
```python
from prometheus_client import Counter, Histogram, Gauge

# Event metrics
events_received = Counter('agui_events_received_total', 'Total events from Redis')
events_sent = Counter('agui_events_sent_total', 'Total events sent to clients')
event_latency = Histogram('agui_event_latency_seconds', 'Event processing latency')

# SSE metrics
sse_connections = Gauge('agui_sse_connections', 'Active SSE connections')
sse_errors = Counter('agui_sse_errors_total', 'SSE connection errors')

# Tool execution metrics
tool_calls = Counter('agui_tool_calls_total', 'Tool executions', ['tool_name', 'status'])
tool_latency = Histogram('agui_tool_latency_seconds', 'Tool execution time', ['tool_name'])
```

### 14.3 Logging Strategy

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

# Log event processing
logger.info(
    "event_processed",
    event_type=event.type,
    message_id=event.message_id,
    latency_ms=latency
)

# Log tool execution
logger.info(
    "tool_executed",
    tool_name=tool_name,
    job_id=job_id,
    duration_s=duration,
    status=status
)
```

---

## 15. Cost Estimate

### 15.1 Development Effort

| Phase | Tasks | Effort | Cost @ $100/hr |
|-------|-------|--------|----------------|
| **Phase 1: Foundation** | 5 | 4.5 hours | $450 |
| **Phase 2: Backend** | 7 | 18 hours | $1,800 |
| **Phase 3: Frontend** | 9 | 32 hours | $3,200 |
| **Phase 4: Integration** | 7 | 13 hours | $1,300 |
| **Phase 5: Testing** | 5 | 12 hours | $1,200 |
| **TOTAL** | **33** | **~80 hours** | **$8,000** |

### 15.2 Infrastructure Cost

**Additional Resources Needed**:
- hx-dev-server resources: Existing (no additional cost)
- Docker storage: ~10GB (existing disk)
- Network bandwidth: Negligible (local network)

**Total Infrastructure Cost**: $0 (uses existing infrastructure)

**Total Project Cost**: ~$8,000 (labor only)

---

## 16. Appendices

### Appendix A: AG-UI Event Types

**16 Standard AG-UI Events**:
1. `TEXT_MESSAGE_CONTENT` - Streaming text
2. `TOOL_CALL` - Tool invocation
3. `TOOL_RESULT` - Tool result
4. `STATE_UPDATE` - State changes
5. `PROGRESS_UPDATE` - Progress tracking
6. `MESSAGE_START` - Message beginning
7. `MESSAGE_END` - Message completion
8. `ERROR` - Error events
9. `GENERATIVE_UI_UPDATE` - Dynamic UI
10. `CONTEXT_UPDATE` - Context changes
11. `AGENT_STATE_MESSAGE` - Agent state
12. `TEXT_DELTA` - Text streaming delta
13. `TOOL_CALL_DELTA` - Tool call streaming
14. `COMPLETION_TOKEN_USAGE` - Token metrics
15. `PROMPT_TOKEN_USAGE` - Prompt metrics
16. `TOTAL_TOKEN_USAGE` - Total usage

### Appendix B: MCP Tools for AG-UI

| Tool | Purpose | AG-UI Access | HITL Required |
|------|---------|--------------|---------------|
| `crawl_web` | Web scraping | ✅ Full | No (power users trusted) |
| `ingest_doc` | Document processing | ✅ Full | No |
| `qdrant_find` | Vector search | ✅ Full | No |
| `qdrant_store` | Vector storage | ✅ Full | No |
| `lightrag_query` | Hybrid RAG | ✅ Full | No |
| `get_job_status` | Job tracking | ✅ Full | No |
| `health_check` | System health | ✅ Full | No |
| `kg_curate` | KG editing | ✅ Full | No (AG-UI exclusive) |

### Appendix C: Useful Commands

**Development**:
```bash
# Build and start locally
cd /opt/ag-ui
docker-compose up --build

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart frontend

# Execute command in container
docker exec -it shield-ag-ui-backend bash
```

**Deployment**:
```bash
# Deploy AG-UI
ansible-playbook -i inventory/prod.ini playbooks/deploy-ag-ui.yml

# Update only frontend
ansible-playbook -i inventory/prod.ini playbooks/deploy-ag-ui.yml --tags frontend

# Check deployment status
ansible hx-dev-server -i inventory/prod.ini -m shell -a "docker ps | grep ag-ui"
```

**Troubleshooting**:
```bash
# Check Redis connectivity
redis-cli -h hx-sqldb-server -p 6379 ping

# Check Redis Streams
redis-cli -h hx-sqldb-server -p 6379 XINFO STREAM shield:events

# Test SSE endpoint
curl -N http://hx-dev-server:8002/events

# Check container health
docker inspect shield-ag-ui-backend --format='{{.State.Health.Status}}'
```

---

## 17. SOLID Principles Application

### 17.1 Single Responsibility

- ✅ **Backend**: Only handles event transformation and SSE streaming
- ✅ **Frontend**: Only handles UI rendering and user interaction
- ✅ **Nginx**: Only handles reverse proxy and SSL termination
- ✅ **Each Ansible task file**: Handles one aspect of deployment

### 17.2 Open/Closed Principle

- ✅ Event transformation is extensible (new event types via mapping)
- ✅ Tool execution is abstracted (new tools via configuration)
- ✅ Frontend components are pluggable (new visualizations via imports)

### 17.3 Liskov Substitution

- ✅ AG-UI events implement standard interface
- ✅ Backend can be swapped with any AG-UI compatible server
- ✅ Frontend can consume events from any AG-UI backend

### 17.4 Interface Segregation

- ✅ Separate interfaces for: events, tools, state, monitoring
- ✅ Clients only depend on interfaces they use
- ✅ No monolithic API contract

### 17.5 Dependency Inversion

- ✅ Components depend on abstractions (AG-UI protocol) not concretions
- ✅ Redis, LiteLLM, Orchestrator are injectable dependencies
- ✅ Configuration via environment variables (dependency injection)

---

## 18. Next Steps After Review

### 18.1 Approval Checklist

- [ ] Architecture reviewed and approved
- [ ] Resource allocation confirmed (hx-dev-server specs)
- [ ] Timeline acceptable (10 development days)
- [ ] Cost approved (~$8,000 labor)
- [ ] Integration approach validated
- [ ] Security controls reviewed
- [ ] Testing strategy approved

### 18.2 Pre-Implementation

1. ✅ Create feature branch: `feature/ag-ui-deployment`
2. ✅ Setup Ansible role structure
3. ✅ Verify hx-dev-server specifications
4. ✅ Test Redis Streams on hx-sqldb-server
5. ✅ Review AG-UI SDK documentation
6. ✅ Create project tracking in TASK-TRACKER

### 18.3 Implementation Start

Once approved:
1. Create `roles/ag_ui_app/` structure
2. Begin with DEV-001 (Ansible role creation)
3. Follow phased approach (Day 1 → Day 10)
4. Daily updates to TASK-TRACKER.md
5. Weekly demos to stakeholders

---

## 19. Summary

### 19.1 What This Plan Delivers

✅ **Complete Ansible role** for AG-UI deployment  
✅ **Docker-based architecture** for easy management  
✅ **Full integration** with existing HX-Citadel infrastructure  
✅ **Real-time event streaming** via AG-UI protocol  
✅ **Advanced UI features** (KG viz, job tracking, curation)  
✅ **Production-ready code** following SOLID principles  
✅ **Comprehensive testing** (unit, integration, E2E, load)  
✅ **Complete documentation** for users and ops  

### 19.2 Key Benefits

- 🎯 **Power user productivity**: Advanced interface for LoB teams
- 🎯 **Real-time visibility**: Live event streaming and progress tracking
- 🎯 **Full tool access**: All 7 MCP tools + KG curation
- 🎯 **Operational excellence**: Docker orchestration, health checks, monitoring
- 🎯 **Maintainability**: Ansible automation, SOLID code, documentation
- 🎯 **Scalability**: Can add more frontends (CopilotKit, Dashboard) using same pattern

### 19.3 Timeline Summary

- **Total Duration**: 10 development days (2 weeks)
- **Total Tasks**: 33 tasks across 5 phases
- **Total Effort**: ~80 hours
- **Total Cost**: ~$8,000 (labor only)

---

## 20. Review & Approval

### 20.1 Stakeholder Review

**Technical Review**:
- [ ] Architecture Lead: ________________________ Date: ________
- [ ] DevOps Lead: _____________________________ Date: ________
- [ ] Security Lead: ___________________________ Date: ________

**Business Review**:
- [ ] Product Owner: ___________________________ Date: ________
- [ ] LoB Representative: ______________________ Date: ________

### 20.2 Decision

- [ ] **APPROVED** - Proceed with implementation
- [ ] **APPROVED WITH MODIFICATIONS** - Details: _______________________
- [ ] **DEFERRED** - Reason: ____________________
- [ ] **REJECTED** - Reason: _____________________

### 20.3 Sign-off

**Approval Date**: ________________  
**Implementation Start Date**: ________________  
**Target Completion Date**: ________________

---

**🎯 PLAN COMPLETE - READY FOR REVIEW**

**Document Version**: 1.0  
**Classification**: Internal - Technical Planning  
**Author**: AI Agent  
**Related Documents**:
- [HX-ARCHITECTURE.md](HX-ARCHITECTURE.md) - Master architecture
- [TASK-TRACKER.md](TASK-TRACKER.md) - Progress tracking
- [EXECUTIVE-BRIEFING.md](EXECUTIVE-BRIEFING.md) - Leadership summary

**Next**: Review, approve, and begin implementation 🚀
