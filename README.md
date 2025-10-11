# HX-Citadel Ansible Infrastructure

**Automated deployment and management for HX-Citadel AI infrastructure**

[![Phase 1](https://img.shields.io/badge/Phase%201-Complete-brightgreen)](docs/Delivery-Enhancements/TASK-TRACKER.md)
[![Production Ready](https://img.shields.io/badge/Production%20Ready-85%25-blue)](docs/Delivery-Enhancements/EXECUTIVE-BRIEFING.md)
[![MCP Tools](https://img.shields.io/badge/MCP%20Tools-7%20Operational-success)](docs/MCP_TOOLS_REFERENCE.md)

## 🎯 Overview

Production-ready Ansible automation for deploying and managing a 17-server AI fleet running the HX-Citadel RAG pipeline on Ubuntu 24.04. Control node: hx-devops-server (192.168.10.14).

**Latest Achievement (Oct 11, 2025)**: Phase 1 Complete - 21/21 critical tasks delivered, MCP Server operational with 7 tools, circuit breaker protection, and comprehensive error handling.

## 🚀 Quick Start

### Prerequisites

- **Ansible**: 2.14-2.18 (`sudo apt install ansible`)
- **Python**: 3.12+
- **SSH**: Key-based authentication configured
- **Sudo**: Privilege escalation on target hosts

### Installation

```bash
# Clone repository
git clone https://github.com/hanax-ai/hx-citadel-ansible.git
cd hx-citadel-ansible

# Install Galaxy dependencies
ansible-galaxy install -r requirements.yml

# Verify connectivity
ansible all -i inventory/prod.ini -m ping
```

### Safe Deployment (Recommended)

```bash
# Deploy with automatic validation and smoke tests
ansible-playbook -i inventory/prod.ini playbooks/deploy-with-validation.yml
```

### Pre-flight Validation

**ALWAYS run before deployment:**

```bash
# Validate infrastructure readiness
ansible-playbook -i inventory/prod.ini playbooks/preflight-check.yml
```

## 📂 Project Structure

```
hx-citadel-ansible/
├── playbooks/              # Deployment playbooks
│   ├── deploy-*.yml        # Component deployments
│   ├── preflight-check.yml # Pre-deployment validation
│   ├── deploy-with-validation.yml  # Safe deployment wrapper
│   └── smoke-tests.yml     # Post-deployment tests
├── roles/                  # Ansible roles
│   ├── base-setup/         # Base system configuration
│   ├── postgresql/         # PostgreSQL database
│   ├── redis/              # Redis cache
│   ├── qdrant/             # Vector database
│   ├── ollama/             # LLM inference
│   ├── litellm/            # API gateway
│   ├── prisma/             # ORM middleware
│   ├── fastapi/            # Orchestration API
│   └── fastmcp_server/     # MCP Server (7 tools) ✨
├── inventory/              # Infrastructure inventory
│   ├── prod.ini            # Production hosts
│   └── hx-qwui.ini         # Qdrant UI
├── group_vars/             # Group variables
├── host_vars/              # Host-specific variables
├── tests/                  # Test procedures & scripts ✨
│   ├── TEST-*.md           # Test documentation
│   ├── test-*.py           # Test scripts
│   └── *.sh                # Validation scripts
├── maintenance/            # Maintenance playbooks
│   ├── update-hosts-file.yml
│   ├── fix-apt.yml
│   └── host-inventory.yml  # Fleet documentation
├── docs/                   # Documentation
│   ├── QUICK-START.md      # Quick reference
│   ├── DEPLOYMENT-GUIDE.md # Comprehensive guide
│   ├── MCP_TOOLS_REFERENCE.md  # MCP tools documentation ✨
│   ├── Delivery-Enhancements/  # Implementation tracking ✨
│   │   ├── TASK-TRACKER.md     # Progress tracking
│   │   ├── EXECUTIVE-BRIEFING.md  # Leadership summary
│   │   └── *.md                # Implementation docs
│   └── CHANGELOG.md        # Version history
├── status/                 # Deployment status reports
├── configuration/          # Service configurations
├── templates/              # Documentation templates
└── site.yml                # Main orchestrator
```

## 📋 Usage Examples

### Standard Deployment

```bash
# Deploy entire infrastructure
ansible-playbook -i inventory/prod.ini site.yml

# Dry run (no changes)
ansible-playbook -i inventory/prod.ini site.yml --check --diff

# With vault password
ansible-playbook -i inventory/prod.ini site.yml --ask-vault-pass
```

### Component-Specific Deployment

```bash
# Database layer only
ansible-playbook -i inventory/prod.ini site.yml --tags db

# LLM nodes only
ansible-playbook -i inventory/prod.ini site.yml --tags models

# API layer only
ansible-playbook -i inventory/prod.ini site.yml --tags api

# MCP Server (NEW - Phase 1) ✨
ansible-playbook -i inventory/prod.ini playbooks/deploy-mcp-server.yml
```

### Host-Limited Deployment

```bash
# Single host
ansible-playbook -i inventory/prod.ini site.yml --limit hx-sqldb-server

# Specific group
ansible-playbook -i inventory/prod.ini site.yml --limit db_nodes

# Qdrant UI (separate inventory)
ansible-playbook -i inventory/hx-qwui.ini playbooks/deploy-qdrant-ui.yml
```

### Maintenance Tasks

```bash
# Update /etc/hosts across fleet
ansible-playbook -i inventory/prod.ini maintenance/update-hosts-file.yml

# Fix apt cache issues
ansible-playbook -i inventory/prod.ini maintenance/fix-apt.yml
```

## 🧪 Testing & Verification

### Smoke Tests

```bash
# Run all post-deployment tests
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml

# Specific component tests
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags database
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags vector
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags llm
```

### Manual Verification

```bash
# Check service status
ansible all -i inventory/prod.ini -m systemd -a "name=postgresql" -b

# Verify API endpoints (use FQDNs for consistency)
curl http://hx-vectordb-server:6333/healthz           # Qdrant
curl http://hx-ollama1:11434/api/version              # Ollama
curl http://hx-orchestrator-server:8080/healthz       # Orchestrator
curl http://hx-mcp1-server:8081/health                # MCP Server ✨

# MCP Server Health Check (includes circuit breaker metrics) ✨
curl http://hx-mcp1-server:8081/health | jq

# List LLM models
ansible llm_nodes -i inventory/prod.ini -m shell -a "ollama list"

# Check system facts
ansible all -i inventory/prod.ini -m setup | grep ansible_date_time
```

### View Logs

```bash
# PostgreSQL logs
ansible db_nodes -i inventory/prod.ini -m shell -a "journalctl -u postgresql -n 50" -b

# Orchestrator logs
ansible orchestrator_nodes -i inventory/prod.ini -m shell -a "journalctl -u orchestrator -n 50" -b

# MCP Server logs (includes circuit breaker events) ✨
ansible hx-mcp1-server -i inventory/prod.ini -m shell -a "journalctl -u shield-mcp-server -n 50" -b
```

---

## 📚 Documentation

### Core Guides
- **[Quick Start Guide](docs/QUICK-START.md)** - Fast deployment commands
- **[Deployment Guide](docs/DEPLOYMENT-GUIDE.md)** - Comprehensive procedures
- **[Ansible Best Practices](docs/ANSIBLE-BEST-PRACTICES.md)** - ⭐ **MANDATORY** coding standards
- **[Implementation Summary](docs/IMPLEMENTATION-SUMMARY.md)** - Safe deployment framework
- **[Change Log](docs/CHANGELOG.md)** - Version history

### Phase 1 Deliverables ✨ (NEW)
- **[MCP Tools Reference](docs/MCP_TOOLS_REFERENCE.md)** - Complete MCP tools documentation
- **[Task Tracker](docs/Delivery-Enhancements/TASK-TRACKER.md)** - Implementation progress (21/59 tasks)
- **[Executive Briefing](docs/Delivery-Enhancements/EXECUTIVE-BRIEFING.md)** - Leadership summary (85% ready)
- **[Test Procedures](tests/)** - Comprehensive test documentation

### Infrastructure
- **[Host Inventory](maintenance/host-inventory.yml)** - Fleet documentation
- **Status Reports**: `status/` - Deployment status snapshots
- **Configurations**: `configuration/` - Service configuration references
- **Templates**: `templates/` - Documentation standards

### 📖 Reference Materials

- **Ansible Core Source**: `tech_kb/ansible-devel/` - Official Ansible development repository
- **Module Examples**: `tech_kb/ansible-devel/lib/ansible/modules/` - Core module implementations
- **Development Tools**: `tech_kb/ansible-devel/hacking/` - Testing and development utilities

---

## 🏗️ Infrastructure Fleet

| Host | IP | Services | Role |
|------|-----|----------|------|
| hx-sqldb-server | 192.168.10.48 | PostgreSQL, Redis | Database |
| hx-vectordb-server | 192.168.10.9 | Qdrant | Vector DB |
| hx-ollama1 | 192.168.10.50 | Ollama | LLM (GPU) |
| hx-ollama2 | 192.168.10.52 | Ollama | LLM (GPU) |
| hx-litellm-server | 192.168.10.46 | LiteLLM | API Gateway |
| hx-prisma-server | 192.168.10.47 | Prisma ORM | Middleware |
| hx-orchestrator-server | 192.168.10.8 | FastAPI | Orchestration |
| hx-qwebui-server | 192.168.10.53 | Qdrant Web UI | Management |
| hx-mcp1-server | 192.168.10.59 | MCP Server (7 tools) ✨ | Model Context Protocol |

**Total Fleet**: 17 servers | **Network**: 192.168.10.0/24

### MCP Server Features ✨ (Phase 1 Complete)
- **7 Operational Tools**: `crawl_web`, `ingest_doc`, `qdrant_find`, `qdrant_store`, `lightrag_query`, `get_job_status`, `health_check`
- **Circuit Breaker Protection**: 10x faster failure handling (< 1ms fast-fail vs 30s timeout)
- **HTTP 202 Async Pattern**: Long-running task support with job status tracking
- **Error Handling**: Comprehensive block/rescue/always patterns in deployment
- **Structured Logging**: Complete observability with metrics
- **Service Status**: Active & stable at `hx-mcp1-server:8081`

---

## 💡 Best Practices

1. **Always run pre-flight checks** before deployment
2. Use **--check** mode for dry runs
3. Review **--diff** output before applying
4. Deploy **incrementally** with tags
5. Test on **dev/test** servers first
6. Monitor **logs** after deployment
7. Keep **vault files encrypted**
8. Document **all changes** in CHANGELOG

---

## ⚠️ Safety Features

- ✅ **Pre-flight validation** - Check connectivity, sudo, disk space
- ✅ **Error handling** - Block/rescue/always patterns
- ✅ **Idempotent operations** - Safe to run multiple times
- ✅ **Backup creation** - Auto-backup before modifications
- ✅ **Smoke tests** - Post-deployment validation
- ✅ **User confirmation** - Interactive deployment approval

---

## 🆘 Troubleshooting

### Quick Fixes

```bash
# SSH connectivity issues
ssh-add ~/.ssh/id_rsa
ansible all -i inventory/prod.ini -m ping

# Privilege escalation issues
ansible-playbook -i inventory/prod.ini site.yml --ask-become-pass

# Service not starting
ansible <host> -i inventory/prod.ini -m shell -a "journalctl -u <service> -n 100" -b
```

See [DEPLOYMENT-GUIDE.md](docs/DEPLOYMENT-GUIDE.md) for detailed troubleshooting.

---

## 🎓 Key Achievements

### Infrastructure (Established)
- ✅ **Idempotent deployments** - Safe to re-run
- ✅ **FQCN compliance** - Modern Ansible best practices
- ✅ **Environment secrets** - Vault encryption
- ✅ **Health endpoints** - Automated validation
- ✅ **Model synchronization** - LLM fleet management
- ✅ **Comprehensive testing** - Pre-flight + smoke tests
- ✅ **Error resilience** - Graceful failure handling

### Phase 1 - Critical Fixes ✨ (Complete - Oct 11, 2025)
- ✅ **MCP Server Deployed** - 7 production-ready tools (~1,125 LOC)
- ✅ **Circuit Breaker Pattern** - PyBreaker integration, 10x performance on failures
- ✅ **HTTP 202 Async Pattern** - Job status tracking for long-running tasks
- ✅ **Error Handling Framework** - 4 block/rescue/always patterns in Ansible
- ✅ **SOLID Principles** - Quality-first implementation throughout
- ✅ **FQDN Policy Enforced** - Pre-commit hooks prevent localhost/IP hardcoding
- ✅ **Production Ready** - 85% complete, stable service at hx-mcp1-server:8081

### Phase 2 - Roadmap (18 tasks remaining)
- ⏭️ **Type Hints Migration** - 95%+ coverage with mypy validation
- ⏭️ **Automated Testing** - Unit tests, integration tests, CI/CD pipeline
- ⏭️ **Documentation** - API reference, architecture diagrams, runbooks
- ⏭️ **Monitoring & Alerting** - Grafana dashboards, Prometheus alerts

---

## 📊 Current Status & Progress

### Overall Progress: 36% Complete (21/59 tasks)

| Phase | Status | Tasks | Completion | Target Date |
|-------|--------|-------|------------|-------------|
| **Phase 1: Critical Fixes** | ✅ **COMPLETE** | 21/21 | 100% 🎉 | Oct 11, 2025 ✅ |
| **Phase 2: Quality Improvements** | ⏭️ In Progress | 0/18 | 0% | TBD |
| **Phase 3: Production Hardening** | ⏭️ Pending | 0/20 | 0% | TBD |

### Sprint Breakdown (Phase 1)
- ✅ **Sprint 1.1**: MCP Tool Implementations (12/12, 100%)
- ✅ **Sprint 1.2**: Circuit Breakers (7/7, 100%)
- ✅ **Sprint 1.3**: HTTP 202 Async Pattern (1/1, 100%)
- ✅ **Sprint 1.4**: Error Handling Framework (1/1, 100%)

### Production Readiness Metrics
| Component | Status | Readiness |
|-----------|--------|-----------|
| Layer 4 (Orchestrator) | ✅ Deployed | 90% |
| Layer 3 (MCP Server) | ✅ Deployed | 100% |
| Testing Infrastructure | ⚠️ Partial | 15% |
| Error Handling | ✅ Complete | 100% |
| Resilience Patterns | ✅ Deployed | 100% |
| **Overall** | ⚠️ In Progress | **85%** |

**Tracking**: See [Task Tracker](docs/Delivery-Enhancements/TASK-TRACKER.md) for detailed progress

---

## 📧 Support

- **Infrastructure Team**: [Contact Info]
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/hanax-ai/hx-citadel-ansible/issues)

---

## 📜 License

[Your License Here]

---

**🎉 Phase 1 Complete! Quality-first, SOLID principles, zero shortcuts.** 🚀

**Remember**: "Measure twice, deploy once!" 🎯
