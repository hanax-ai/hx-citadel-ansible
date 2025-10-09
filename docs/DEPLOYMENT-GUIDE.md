# HX-Citadel Ansible Deployment Guide

**Version**: 1.0  
**Last Updated**: 2025-10-08  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Deployment Methods](#deployment-methods)
5. [Validation & Testing](#validation--testing)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)
8. [Best Practices](#best-practices)

---

## 🎯 Overview

This guide provides comprehensive procedures for deploying and maintaining the HX-Citadel infrastructure using Ansible automation.

### Infrastructure Components

| Layer | Hosts | Services |
|-------|-------|----------|
| **Database** | hx-sqldb-server | PostgreSQL, Redis |
| **Vector DB** | hx-vectordb-server | Qdrant |
| **LLM** | hx-ollama1, hx-ollama2 | Ollama |
| **API** | hx-litellm-server, hx-prisma-server | LiteLLM, Prisma |
| **Orchestrator** | hx-orchestrator-server | FastAPI, Observability |

---

## 🔧 Prerequisites

### 1. Control Node Requirements

- **OS**: Linux (Ubuntu 24.04 recommended)
- **Python**: 3.12+
- **Ansible**: 2.14-2.18
- **SSH**: Configured key-based authentication
- **Network**: Access to 192.168.10.0/24 subnet

### 2. SSH Configuration

```bash
# Ensure SSH agent is running
eval $(ssh-agent)

# Add your SSH key
ssh-add ~/.ssh/id_rsa

# Test connectivity (example)
ssh agent0@192.168.10.48
```

### 3. Sudo/Privilege Escalation

Ensure target hosts have passwordless sudo configured:

```bash
# On each target host
echo "agent0 ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/agent0
```

**OR** use `--ask-become-pass` flag during deployment.

### 4. Required Collections

```bash
# Install Ansible collections
ansible-galaxy collection install -r requirements.yml
```

---

## ✅ Pre-Deployment Checklist

### **CRITICAL: Always run pre-flight checks before deployment!**

```bash
# Run comprehensive pre-flight validation
ansible-playbook -i inventory/prod.ini playbooks/preflight-check.yml
```

### What Pre-flight Checks Validate

- ✅ SSH connectivity to all hosts
- ✅ Python interpreter availability
- ✅ Sudo/privilege escalation
- ✅ Disk space (warns if >80%)
- ✅ System facts gathering
- ✅ Network connectivity

### Expected Output

```
═══════════════════════════════════════════════════
Host: hx-sqldb-server (192.168.10.48)
═══════════════════════════════════════════════════
OS: Ubuntu 24.04
Python: Python 3.12.3
Sudo: PASS
Disk Usage: 45%
Memory: 16.0 GB
CPUs: 8
═══════════════════════════════════════════════════
```

---

## 🚀 Deployment Methods

### Method 1: Safe Deployment with Validation (RECOMMENDED)

This method includes automatic pre-flight checks, user confirmation, and post-deployment smoke tests.

```bash
# Full deployment with validation
ansible-playbook -i inventory/prod.ini playbooks/deploy-with-validation.yml
```

**Process Flow**:
1. **Stage 1**: Pre-flight validation
2. **User Confirmation**: Manual approval prompt
3. **Stage 2**: Infrastructure deployment
4. **Stage 3**: Post-deployment smoke tests

### Method 2: Standard Deployment

Deploy all components in dependency order:

```bash
# Deploy entire infrastructure
ansible-playbook -i inventory/prod.ini site.yml
```

### Method 3: Component-Specific Deployment

Deploy individual components using tags:

```bash
# Base setup only
ansible-playbook -i inventory/prod.ini site.yml --tags base

# Database layer only
ansible-playbook -i inventory/prod.ini site.yml --tags db

# LLM nodes only
ansible-playbook -i inventory/prod.ini site.yml --tags models

# Multiple components
ansible-playbook -i inventory/prod.ini site.yml --tags "db,vector,api"
```

### Method 4: Host-Limited Deployment

Deploy to specific hosts or groups:

```bash
# Deploy to single host
ansible-playbook -i inventory/prod.ini site.yml --limit hx-sqldb-server

# Deploy to specific group
ansible-playbook -i inventory/prod.ini site.yml --limit db_nodes

# Deploy to multiple hosts
ansible-playbook -i inventory/prod.ini site.yml --limit "hx-ollama1,hx-ollama2"
```

---

## 🧪 Validation & Testing

### Smoke Tests

Run comprehensive smoke tests after deployment:

```bash
# Run all smoke tests
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml

# Run specific smoke tests
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags database
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags vector
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml --tags llm
```

### Manual Verification

#### Check Service Status

```bash
# Check all systemd services
ansible all -i inventory/prod.ini -m shell -a "systemctl status postgresql redis qdrant ollama orchestrator" -b

# Check specific service
ansible db_nodes -i inventory/prod.ini -m systemd -a "name=postgresql state=started" -b
```

#### Verify API Endpoints

```bash
# Qdrant health
curl http://192.168.10.9:6333/healthz

# Ollama version
curl http://192.168.10.50:11434/api/version

# Orchestrator health
curl http://192.168.10.8:8080/healthz
```

#### Check Logs

```bash
# PostgreSQL logs
ansible db_nodes -i inventory/prod.ini -m shell -a "journalctl -u postgresql -n 50" -b

# Orchestrator logs
ansible orchestrator_nodes -i inventory/prod.ini -m shell -a "journalctl -u orchestrator -n 50" -b
```

---

## 🔍 Troubleshooting

### Common Issues & Solutions

#### Issue 1: SSH Connection Timeout

**Symptom**:
```
fatal: [hx-server]: UNREACHABLE! => {"msg": "Failed to connect to the host via ssh"}
```

**Solutions**:
1. Verify SSH agent is running: `ssh-add -l`
2. Test SSH manually: `ssh agent0@192.168.10.XX`
3. Check SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
4. Verify host is reachable: `ping 192.168.10.XX`

#### Issue 2: Privilege Escalation Timeout

**Symptom**:
```
fatal: [hx-server]: FAILED! => {"msg": "Timeout waiting for privilege escalation prompt"}
```

**Solutions**:
1. Configure passwordless sudo (see Prerequisites)
2. Use `--ask-become-pass` flag
3. Verify sudo access: `ssh agent0@host sudo whoami`

#### Issue 3: Python Interpreter Not Found

**Symptom**:
```
fatal: [hx-server]: FAILED! => {"msg": "/usr/bin/python3: not found"}
```

**Solutions**:
1. Install Python: `ansible all -i inventory/prod.ini -m raw -a "apt-get install -y python3" -b`
2. Set correct interpreter in inventory
3. Use `ansible_python_interpreter` variable

#### Issue 4: Disk Space Low

**Symptom**:
```
WARNING: Disk usage is 92% - critically high!
```

**Solutions**:
1. Clean apt cache: `ansible all -i inventory/prod.ini -m shell -a "apt-get clean" -b`
2. Remove old logs: `ansible all -i inventory/prod.ini -m shell -a "journalctl --vacuum-time=7d" -b`
3. Check large files: `ansible all -i inventory/prod.ini -m shell -a "du -h / | sort -rh | head -20" -b`

---

## 🔄 Rollback Procedures

### Service-Level Rollback

```bash
# Stop a service
ansible <host_group> -i inventory/prod.ini -m systemd -a "name=<service> state=stopped" -b

# Restart a service
ansible <host_group> -i inventory/prod.ini -m systemd -a "name=<service> state=restarted" -b

# Revert configuration file
ansible <host_group> -i inventory/prod.ini -m copy -a "src=/etc/config.backup dest=/etc/config remote_src=yes" -b
```

### Database Rollback

```bash
# PostgreSQL
ansible db_nodes -i inventory/prod.ini -m shell -a "sudo -u postgres psql -c 'DROP DATABASE hx_citadel;'" -b
ansible db_nodes -i inventory/prod.ini -m shell -a "sudo -u postgres psql -c 'CREATE DATABASE hx_citadel;'" -b

# Redis
ansible db_nodes -i inventory/prod.ini -m shell -a "redis-cli FLUSHALL" -b
```

### Full System Rollback

1. Stop all services
2. Restore configuration backups
3. Revert database changes
4. Restart services in dependency order

---

## 💡 Best Practices

### 1. Always Run Pre-flight Checks

```bash
# ALWAYS run before deployment
ansible-playbook -i inventory/prod.ini playbooks/preflight-check.yml
```

### 2. Use Check Mode for Testing

```bash
# Dry run - no changes made
ansible-playbook -i inventory/prod.ini site.yml --check
```

### 3. Use Diff Mode to See Changes

```bash
# Show differences before applying
ansible-playbook -i inventory/prod.ini site.yml --diff
```

### 4. Tag-Based Incremental Deployment

```bash
# Deploy only specific components
ansible-playbook -i inventory/prod.ini site.yml --tags "db,api" --limit hx-sqldb-server
```

### 5. Use Verbose Output for Debugging

```bash
# Verbose output (-v, -vv, -vvv, -vvvv)
ansible-playbook -i inventory/prod.ini site.yml -vv
```

### 6. Maintain Backups

- Configuration files are automatically backed up with timestamps
- Database backups should be scheduled separately
- Keep vault.yml encrypted and backed up securely

### 7. Document Changes

- Update `docs/CHANGELOG.md` after deployments
- Use git commits to track playbook changes
- Maintain status documents in `status/` directory

### 8. Test in Stages

1. Test on dev/test servers first
2. Validate with smoke tests
3. Deploy to production incrementally
4. Monitor logs and metrics

---

## 📊 Deployment Checklist Template

```markdown
## Deployment: [Component Name]
**Date**: YYYY-MM-DD
**Operator**: [Your Name]
**Inventory**: inventory/prod.ini

### Pre-Deployment
- [ ] Pre-flight checks passed
- [ ] Backups verified
- [ ] Maintenance window scheduled
- [ ] Team notified

### Deployment
- [ ] Playbook executed successfully
- [ ] No error messages in output
- [ ] All tasks marked as "ok" or "changed"

### Post-Deployment
- [ ] Smoke tests passed
- [ ] Services are running
- [ ] API endpoints responding
- [ ] Logs reviewed (no errors)
- [ ] Performance metrics normal

### Rollback (if needed)
- [ ] Rollback procedure documented
- [ ] Backup restoration tested
- [ ] Service recovery validated
```

---

## 🆘 Emergency Contacts

- **Infrastructure Team**: [Contact Info]
- **On-Call Engineer**: [Contact Info]
- **Escalation**: [Contact Info]

---

## 📚 Additional Resources

- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
- [HX-Citadel Architecture](./ARCHITECTURE.md)
- [Change Log](./CHANGELOG.md)
- [Host Inventory](../maintenance/host-inventory.yml)

---

**Remember**: "If it ain't broke, don't fix it" - but always validate before deploying! 🚀
