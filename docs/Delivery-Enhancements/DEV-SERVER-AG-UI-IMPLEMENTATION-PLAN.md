# Dev Server AG-UI Implementation Plan
## Shield AG-UI: Power User Interface Deployment

**Version**: 1.0  
**Date**: October 11, 2025  
**Status**: 🔵 **PLANNING - REVIEW REQUIRED**  
**Prepared By**: AI Agent  
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

Deploy **shield-ag-ui** on hx-dev-server to provide Line-of-Business (LoB) power users with an advanced, real-time interface to the HX-Citadel Shield RAG pipeline. This application will leverage the AG-UI protocol for agent-user interaction, providing real-time event streaming, knowledge graph visualization, and advanced tool controls.

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
│  │  │  shield-ag-ui (Port 3001)                        │ │ │
│  │  │  Technology: Next.js 14 + React 18               │ │ │
│  │  │  Framework: AG-UI Protocol + TypeScript SDK      │ │ │
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

**Frontend (shield-ag-ui)**:
- Next.js 14 (React framework with SSR)
- React 18 (UI framework)
- AG-UI TypeScript SDK (@ag-ui/core, @ag-ui/react)
- Zustand (state management)
- Zod (schema validation)
- D3.js (knowledge graph visualization)
- TailwindCSS (styling)

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

### 3.1 Server Specifications

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
- ✅ Node.js 20.x+ (for Next.js builds)
- ✅ Python 3.12+ (for backend)

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
- shield-ag-ui:latest (Next.js app)
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
    │   ├── 04-frontend-build.yml       # Next.js build
    │   ├── 05-backend-setup.yml        # FastAPI backend
    │   ├── 06-docker-compose.yml       # Docker orchestration
    │   ├── 07-nginx-config.yml         # Reverse proxy
    │   └── 08-service-start.yml        # Start services
    ├── templates/
    │   ├── docker-compose.yml.j2       # Docker Compose config
    │   ├── Dockerfile.frontend.j2      # Next.js Dockerfile
    │   ├── Dockerfile.backend.j2       # FastAPI Dockerfile
    │   ├── nginx-ag-ui.conf.j2         # Nginx site config
    │   ├── backend-main.py.j2          # FastAPI application
    │   ├── backend-redis-consumer.py.j2 # Redis Streams consumer
    │   ├── frontend-env.local.j2       # Next.js environment
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

# Frontend configuration
ag_ui_app_name: "Shield AG-UI"
ag_ui_app_description: "Power User Interface for HX-Citadel Shield"
ag_ui_node_version: "20"
ag_ui_next_version: "14"

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

