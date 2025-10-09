# HX-Citadel Ansible Infrastructure

**Automated deployment and management for HX-Citadel AI infrastructure**

## 🎯 Overview

Production-ready Ansible automation for deploying and managing a 17-server AI fleet running the HX-Citadel RAG pipeline on Ubuntu 24.04. Control node: hx-devops-server (192.168.10.14).

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
│   └── fastapi/            # Orchestration API
├── inventory/              # Infrastructure inventory
│   ├── prod.ini            # Production hosts
│   └── hx-qwui.ini         # Qdrant UI
├── group_vars/             # Group variables
├── host_vars/              # Host-specific variables
├── maintenance/            # Maintenance playbooks
│   ├── update-hosts-file.yml
│   ├── fix-apt.yml
│   └── host-inventory.yml  # Fleet documentation
├── docs/                   # Documentation
│   ├── QUICK-START.md      # Quick reference
│   ├── DEPLOYMENT-GUIDE.md # Comprehensive guide
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

# Verify API endpoints
curl http://192.168.10.9:6333/healthz          # Qdrant
curl http://192.168.10.50:11434/api/version    # Ollama
curl http://192.168.10.8:8080/healthz          # Orchestrator

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
```

---

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK-START.md)** - Fast deployment commands
- **[Deployment Guide](docs/DEPLOYMENT-GUIDE.md)** - Comprehensive procedures
- **[Ansible Best Practices](docs/ANSIBLE-BEST-PRACTICES.md)** - ⭐ **MANDATORY** coding standards
- **[Implementation Summary](docs/IMPLEMENTATION-SUMMARY.md)** - Safe deployment framework
- **[Change Log](docs/CHANGELOG.md)** - Version history
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
| hx-mcp1-server | 192.168.10.59 | MCP Server | Model Context |

**Total Fleet**: 17 servers | **Network**: 192.168.10.0/24

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

- ✅ **Idempotent deployments** - Safe to re-run
- ✅ **FQCN compliance** - Modern Ansible best practices
- ✅ **Environment secrets** - Vault encryption
- ✅ **Health endpoints** - Automated validation
- ✅ **Model synchronization** - LLM fleet management
- ✅ **Comprehensive testing** - Pre-flight + smoke tests
- ✅ **Error resilience** - Graceful failure handling

---

## 📧 Support

- **Infrastructure Team**: [Contact Info]
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/hanax-ai/hx-citadel-ansible/issues)

---

## 📜 License

[Your License Here]

---

**Remember**: "Measure twice, deploy once!" 🎯
