# FQDN Policy Documentation

This directory contains FQDN (Fully Qualified Domain Name) policy documentation, fleet analysis, and action items for the HX-Citadel infrastructure.

---

## 📁 Active Documentation

### Primary Reference
- **fqdn_assessment.md** (21 KB) - **📖 READ THIS FIRST**
  - Comprehensive fleet analysis (17 hosts)
  - Network topology and service dependencies
  - Complete FQDN/IP mappings
  - Policy framework and enforcement
  - Mermaid diagrams for visualization
  - **Status**: ✅ Current (October 12, 2025)

### Action Items
- **FQDN-BACKLOG.md** - Issues and improvement backlog
  - 7 tracked items (2 high, 4 medium, 1 low)
  - Server access inconsistency (awaiting identification)
  - Documentation sync tasks
  - Enhancement opportunities

### Directory Guide
- **README.md** (this file) - Quick navigation and policy summary

---

## 📦 Archived Documentation

See `archive/` subdirectory for historical documents:
- Original policy documentation (October 10, 2025)
- Violation detection report (35 violations found)
- Remediation completion report (all violations fixed)

**Note**: Archive contains point-in-time snapshots. Refer to `fqdn_assessment.md` for current state.

---

## 🎯 FQDN Policy Summary

### Policy Statement

**All infrastructure references must use FQDNs, not IPs or localhost.**

**Prohibited**:
- `localhost` or `127.0.0.1` or `::1`
- Direct IP addresses like `192.168.10.x`
- Hostname without domain (e.g., `hx-orchestrator-server`)

**Required**:
- Fully qualified domain names (e.g., `hx-orchestrator-server.dev-test.hana-x.ai`)
- Use FQDN variables from `group_vars/all/fqdn_map.yml`

### Enforcement

✅ **Pre-commit hooks** - Block commits with violations  
✅ **Ansible guardrails** - Fail playbooks with violations  
✅ **Scanner tool** - `scripts/check-fqdn.sh` for manual audits  
✅ **Allowlist** - `.fqdn-allowlist` for legitimate exceptions

### Fleet Overview

**Domain**: `dev-test.hana-x.ai`  
**Total Hosts**: 17  
**IP Range**: `192.168.10.2` - `192.168.10.59`  
**Violations**: 0 (all remediated)

---

## 🚀 Quick Start

### Check FQDN Compliance
```bash
# Scan entire repository
bash scripts/check-fqdn.sh .

# Check specific directory
bash scripts/check-fqdn.sh roles/
```

### View Fleet Inventory
```bash
# FQDN mappings
cat group_vars/all/fqdn_map.yml

# Visualize fleet
# See fqdn_assessment.md for Mermaid diagrams
```

### Test DNS Resolution
```bash
# Test single host
nslookup hx-orchestrator-server.dev-test.hana-x.ai

# Test all hosts
for host in hx-{dc,ca,orchestrator,vectordb,webui,qwebui,dev,test,devops,metrics,fs,litellm,prisma,sqldb,ollama{1,2},mcp1}-server; do
  echo "$host:" && nslookup "$host.dev-test.hana-x.ai" | grep Address | tail -1
done
```

---

## 📊 Key Files Reference

| File | Purpose |
|------|---------|
| `group_vars/all/fqdn_map.yml` | Fleet FQDN/IP mappings (single source of truth) |
| `scripts/check-fqdn.sh` | FQDN policy scanner tool |
| `.pre-commit-config.yaml` | Git hook configuration |
| `.fqdn-allowlist` | Legitimate localhost exceptions |
| `fqdn_assessment.md` | Comprehensive fleet analysis |
| `FQDN-BACKLOG.md` | Action items and improvements |

---

## ⚠️ Important Notes

1. **Server Access Issue**: Two servers have different authentication compared to fleet standard
   - **Status**: BLOCKED - awaiting server identification
   - **Tracked**: FQDN-BACKLOG.md #2

2. **Documentation Sync**: Playbooks may have evolved beyond documentation
   - **Action**: Audit needed
   - **Tracked**: FQDN-BACKLOG.md #1

3. **Policy Exceptions**: See `.fqdn-allowlist` for legitimate localhost usage
   - Test files and local development configs only

---

**Last Updated**: October 12, 2025  
**Next Review**: When fleet changes or new hosts added  
**Contact**: DevOps Team

