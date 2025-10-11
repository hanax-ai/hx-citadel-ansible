# HX-Citadel Quick Start Guide

**TL;DR**: Fast deployment commands with safety built-in.

---

## 🚀 Quick Deployment Commands

### 1. Safe Deployment (RECOMMENDED)

```bash
# Full deployment with automatic validation
ansible-playbook -i inventory/prod.ini playbooks/deploy-with-validation.yml
```

**What it does**:
- ✅ Pre-flight validation
- ✅ User confirmation prompt
- ✅ Full deployment
- ✅ Post-deployment smoke tests

### 2. Pre-flight Check Only

```bash
# Validate infrastructure before any changes
ansible-playbook -i inventory/prod.ini playbooks/preflight-check.yml
```

### 3. Standard Deployment

```bash
# Deploy without interactive prompts
ansible-playbook -i inventory/prod.ini site.yml
```

### 4. Component-Specific Deployment

```bash
# Database only
ansible-playbook -i inventory/prod.ini site.yml --tags db

# LLM nodes only
ansible-playbook -i inventory/prod.ini site.yml --tags models

# API layer only
ansible-playbook -i inventory/prod.ini site.yml --tags api
```

---

## 🧪 Testing & Validation

```bash
# Run smoke tests
ansible-playbook -i inventory/prod.ini playbooks/smoke-tests.yml

# Check mode (dry run)
ansible-playbook -i inventory/prod.ini site.yml --check

# Show differences
ansible-playbook -i inventory/prod.ini site.yml --diff
```

---

## 🔧 Maintenance Tasks

```bash
# Update /etc/hosts across fleet
ansible-playbook -i inventory/prod.ini maintenance/update-hosts-file.yml

# Fix apt cache issues
ansible-playbook -i inventory/prod.ini maintenance/fix-apt.yml
```

---

## 📊 Monitoring & Status

```bash
# Check service status
ansible all -i inventory/prod.ini -m shell -a "systemctl status postgresql" -b

# View logs
ansible all -i inventory/prod.ini -m shell -a "journalctl -u postgresql -n 50" -b

# Ping all hosts
ansible all -i inventory/prod.ini -m ping
```

---

## ⚠️ IMPORTANT: Always Run Pre-flight Checks!

**Before any deployment**, always validate:

```bash
ansible-playbook -i inventory/prod.ini playbooks/preflight-check.yml
```

This prevents issues like:
- ❌ SSH connectivity failures
- ❌ Missing sudo access
- ❌ Disk space problems
- ❌ Python interpreter issues

---

## 📚 Full Documentation

See [DEPLOYMENT-GUIDE.md](./DEPLOYMENT-GUIDE.md) for comprehensive documentation.

---

**Remember**: Measure twice, deploy once! 🎯
