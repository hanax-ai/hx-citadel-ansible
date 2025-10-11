# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

HX-Citadel Ansible Infrastructure automates deployment and management of a 17-server AI fleet running the HX-Citadel RAG pipeline on Ubuntu 24.04. The control node is hx-devops-server (192.168.10.14).

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

# Verify API endpoints
curl http://192.168.10.9:6333/healthz          # Qdrant
curl http://192.168.10.50:11434/api/version    # Ollama
curl http://192.168.10.8:8080/healthz          # Orchestrator

# View service logs
ansible db_nodes -i inventory/prod.ini -m shell -a "journalctl -u postgresql -n 50" -b
```

## Architecture

### Multi-Layered Service Architecture

**Database Layer** (hx-sqldb-server - 192.168.10.48)
- PostgreSQL: Primary relational database
- Redis: Cache and message queue (with Redis Streams for event bus)

**Vector Database Layer** (hx-vectordb-server - 192.168.10.9)
- Qdrant: Vector similarity search and storage

**LLM Layer** (2 GPU nodes)
- hx-ollama1 (192.168.10.50): Primary LLM inference
- hx-ollama2 (192.168.10.52): Secondary LLM inference
- Model synchronization across both nodes

**API Gateway Layer**
- LiteLLM (hx-litellm-server - 192.168.10.46): API gateway
- Prisma ORM (hx-prisma-server - 192.168.10.47): Database middleware

**Orchestration Layer** (hx-orchestrator-server - 192.168.10.8)
- FastAPI orchestrator service
- Manages: LightRAG, LangGraph, Pydantic AI, CopilotKit
- Worker pool for async job processing
- Integration with all backend services

**Model Context Protocol** (hx-mcp1-server - 192.168.10.59)
- MCP server for model context management
- FastMCP-based implementation with Shield tools

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

- **Ansible Core Source**: `tech_kb/ansible-devel/` - Official Ansible 2.20 dev repository
- **Module Examples**: `tech_kb/ansible-devel/lib/ansible/modules/` - Core module implementations
- **Development Tools**: `tech_kb/ansible-devel/hacking/` - Testing utilities

**When in doubt, reference tech_kb/ansible-devel - never guess!**

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

## Known Issues and Fixes

All 45 critical issues have been resolved (see `CRITICAL_FIXES_REMAINING.md` for audit trail):
- ✅ Security: No password exposure in logs/process lists
- ✅ Runtime: All TypeError, NameError, AttributeError crashes fixed
- ✅ Performance: LLM healthcheck caching, concurrent embeddings processing
- ✅ Correctness: Service naming, variable definitions, privilege escalation

## Documentation

**Primary docs** (in `docs/`):
- `ANSIBLE-BEST-PRACTICES.md` - **MANDATORY** coding standards
- `DEPLOYMENT-GUIDE.md` - Comprehensive deployment procedures
- `QUICK-START.md` - Fast reference commands
- `IMPLEMENTATION-SUMMARY.md` - Safe deployment framework

**Operational docs**:
- `maintenance/host-inventory.yml` - Fleet documentation
- `status/*.md` - Deployment status snapshots (check for latest state)
- `templates/` - Documentation templates

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

## Ansible Configuration

Key settings from `ansible.cfg`:
- Default inventory: `./inventory/prod.ini`
- Fact caching: JSON file at `./.ansible_cache` (24h TTL)
- Vault password: `~/.ansible_vault_pass`
- SSH pipelining: Enabled for performance
- Control persistence: 60 minutes for faster repeated runs
