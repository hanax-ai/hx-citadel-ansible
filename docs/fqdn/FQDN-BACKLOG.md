# FQDN Fleet - Issues & Action Items Backlog

**Created**: October 12, 2025  
**Source**: fqdn_assessment.md comprehensive review  
**Status**: ✅ **Migrated to GitHub Issues**  
**Priority Matrix**: 🔴 Critical | 🟡 High | 🟠 Medium | 🔵 Low

---

## 🔗 GitHub Issues

**All backlog items have been migrated to GitHub Issues for tracking:**

- **Issue #5**: 🔴 SECURITY: Remove StrictHostKeyChecking (Critical)
- **Issue #18**: 🔴 FQDN VIOLATION: Hardcoded IP in redis_additional_bind_ip (Critical)
- **Issue #9**: 📝 FQDN Documentation Sync (High)
- **Issue #12**: 📝 SERVICE_PORTS.md creation (Medium)
- **Issue #13**: 🔄 Diagram automation (Medium)
- **Issue #14**: 📊 Health check dashboard (Medium)
- **Issue #15**: 🚨 Disaster recovery docs (Medium)

**View all FQDN issues**: `gh issue list --label fqdn`

**This document remains as reference documentation and implementation guide.**

---

## Critical Issues 🔴

### None Identified
✅ All critical FQDN policy violations have been remediated  
✅ Zero violations in production code  
✅ Automated enforcement in place

---

## High Priority Issues 🟡

### 1. Documentation Synchronization ⚠️

**Issue**: Fleet documentation may be outdated compared to current playbooks

**Impact**: Medium  
**Effort**: Low  
**Priority**: 🟡 High

**Details**:
- User reported that playbooks may have evolved beyond documentation
- Fleet inventory in docs may not match actual deployed configuration
- No automated sync between code and docs

**Action Items**:

1. **Audit playbooks against fleet inventory**:
   ```bash
   # Extract hosts from playbooks
   grep -r "hosts:" playbooks/ | sort -u
   
   # Compare with fqdn_map.yml
   diff <(grep -r "hosts:" playbooks/ | cut -d: -f3 | sort -u) \
        <(yq '.hx_hosts_fqdn | keys' group_vars/all/fqdn_map.yml)
   ```

2. **Add validation task** to playbooks:
   ```yaml
   - name: Validate all playbook hosts have FQDN mappings
     assert:
       that: item in hx_hosts_fqdn.keys()
       fail_msg: "Host {{ item }} not found in fqdn_map.yml"
     loop: "{{ groups['all'] }}"
   ```

3. **Document update process**:
   - When adding new host → Update `fqdn_map.yml` first
   - When removing host → Update playbooks, then `fqdn_map.yml`
   - Run FQDN scanner after any fleet changes

**Assigned**: Unassigned  
**Target**: Sprint TBD  
**Blocked**: No

---

### 2. Server Access Inconsistency 🔐

**Issue**: Two servers have different SSH authentication compared to the rest of the fleet

**Impact**: High (operational complexity, security risk)  
**Effort**: Medium  
**Priority**: 🟡 High

**Affected Servers**:
- **hx-qwebui-server** (192.168.10.53)
- **hx-mcp1-server** (192.168.10.59)

**Current Configuration** (from `inventory/prod.ini`):

**Standard Fleet Configuration:**
```ini
[all:vars]
ansible_user=agent0
ansible_ssh_private_key_file=~/.ssh/id_rsa
```

**Non-Standard Configuration:**
```ini
# Lines 24-25 in inventory/prod.ini
hx-qwebui-server  ansible_ssh_private_key_file=~/.ssh/id_ed25519 ansible_ssh_common_args='-o StrictHostKeyChecking=no'
hx-mcp1-server    ansible_ssh_private_key_file=~/.ssh/id_ed25519 ansible_ssh_common_args='-o StrictHostKeyChecking=no'
```

**Differences Identified**:

1. **SSH Key Type**: 
   - Fleet standard: RSA (`~/.ssh/id_rsa`)
   - These servers: Ed25519 (`~/.ssh/id_ed25519`)
   
2. **Host Key Verification**:
   - Fleet standard: StrictHostKeyChecking enabled (secure)
   - These servers: **`-o StrictHostKeyChecking=no`** ⚠️ **SECURITY RISK**

**Security Concerns**:

🔴 **Critical**: `StrictHostKeyChecking=no` disables MITM protection
- Vulnerable to man-in-the-middle attacks
- Does not validate host identity
- **Should only be used in initial setup, never in production**

**Potential Root Causes**:

- **Likely**: Recently added servers (Oct 2025) with temporary workaround
- **Possible**: Different initial setup process
- **Possible**: Host key mismatch that was bypassed instead of resolved

**Remediation Plan**:

**Phase 1: Immediate (Security Fix)**
1. **Remove StrictHostKeyChecking=no**:
   ```bash
   # SSH to each server and add to known_hosts properly
   ssh-keyscan hx-qwebui-server.dev-test.hana-x.ai >> ~/.ssh/known_hosts
   ssh-keyscan hx-mcp1-server.dev-test.hana-x.ai >> ~/.ssh/known_hosts
   ```

2. **Update inventory/prod.ini**:
   ```ini
   hx-qwebui-server ansible_host=192.168.10.53 ansible_ssh_private_key_file=~/.ssh/id_ed25519
   hx-mcp1-server   ansible_host=192.168.10.59 ansible_ssh_private_key_file=~/.ssh/id_ed25519
   ```

**Phase 2: Standardization (Optional)**
1. **Assess**: Why Ed25519 vs RSA?
   - Ed25519 is actually better (more secure, faster)
   - Could standardize entire fleet to Ed25519
   - Or just accept two key types

2. **Options**:
   - **Option A**: Migrate these 2 servers to RSA key (matches fleet)
   - **Option B**: Migrate entire fleet to Ed25519 (better security)
   - **Option C**: Accept mixed keys, just remove StrictHostKeyChecking

**Recommended**: **Phase 1 immediately** (remove security risk), **Phase 2 decide later** (standardization can wait)

**Testing Plan**:
```bash
# Test connectivity with proper host key checking
ansible hx-qwebui-server -i inventory/prod.ini -m ping
ansible hx-mcp1-server -i inventory/prod.ini -m ping

# Verify no StrictHostKeyChecking bypass needed
ansible hx-qwebui-server,hx-mcp1-server -i inventory/prod.ini -m shell -a "whoami"
```

**Assigned**: Unassigned  
**Target**: **IMMEDIATE** (Security issue)  
**Blocked**: No (ready for execution)

---

## Medium Priority Issues 🟠

### 3. Missing Service Ports Documentation 📝

**Issue**: Port numbers scattered across templates with no central reference

**Impact**: Medium  
**Effort**: Low  
**Priority**: 🟠 Medium

**Details**:
- Port numbers exist in role templates but not centrally documented
- Makes troubleshooting and firewall configuration difficult
- No single source of truth for service ports

**Recommended Solution**:

Create `docs/fqdn/SERVICE_PORTS.md`:

```markdown
# HX-Citadel Service Ports Reference

| Service | Host | Port | Protocol | Purpose |
|---------|------|------|----------|---------|
| FastAPI Orchestrator | hx-orchestrator-server | 8000 | HTTP | Main API |
| LiteLLM Gateway | hx-litellm-server | 4000 | HTTP | LLM Proxy |
| Qdrant Vector DB | hx-vectordb-server | 6333 | HTTPS | Vector Search |
| Qdrant Web UI | hx-qwebui-server | 6333 | HTTPS | Admin UI |
| PostgreSQL | hx-sqldb-server | 5432 | TCP | Database |
| Redis | hx-sqldb-server | 6379 | TCP | Cache/Queue |
| Ollama 1 | hx-ollama1 | 11434 | HTTP | LLM Inference |
| Ollama 2 | hx-ollama2 | 11434 | HTTP | LLM Inference |
| MCP Server | hx-mcp1-server | 3000 | HTTP | MCP Protocol |
| Prometheus | hx-metrics-server | 9090 | HTTP | Metrics |
| Grafana | hx-metrics-server | 3000 | HTTP | Dashboards |
```

**Assigned**: Unassigned  
**Target**: Next sprint  
**Blocked**: No

---

### 4. Network Diagram Automation 🔄

**Issue**: Mermaid diagrams are manually created and may become outdated

**Impact**: Low  
**Effort**: Medium  
**Priority**: 🟠 Medium

**Details**:
- Current diagrams created manually
- Risk of drift from actual configuration
- Time-consuming to maintain

**Recommended Solution**:

Create Python script to generate diagrams from `fqdn_map.yml`:

```python
#!/usr/bin/env python3
"""Generate fleet network diagram from fqdn_map.yml"""

import yaml
from pathlib import Path

def generate_mermaid_diagram(fqdn_map_path):
    with open(fqdn_map_path) as f:
        data = yaml.safe_load(f)
    
    # Generate mermaid graph from hx_hosts_fqdn and hx_hosts_ip
    # Output to docs/fqdn/FLEET_DIAGRAM.md
    pass

if __name__ == "__main__":
    generate_mermaid_diagram("group_vars/all/fqdn_map.yml")
```

**Assigned**: Unassigned  
**Target**: Q1 2026  
**Blocked**: No

---

### 5. Fleet Health Check Dashboard 📊

**Issue**: No centralized view of fleet health

**Impact**: Medium  
**Effort**: High  
**Priority**: 🟠 Medium

**Details**:
- No automated health monitoring playbook
- Manual verification required for each service
- No historical health data

**Recommended Solution**:

Create `playbooks/fleet-health-check.yml`:

```yaml
---
- name: HX-Citadel Fleet Health Check
  hosts: all
  gather_facts: yes
  tasks:
    - name: Check DNS resolution
      command: "nslookup {{ inventory_hostname }}.{{ hx_domain }}"
      register: dns_check
      
    - name: Check service ports
      wait_for:
        host: "{{ inventory_hostname }}.{{ hx_domain }}"
        port: "{{ item }}"
        timeout: 5
      loop: "{{ service_ports | default([]) }}"
      
    - name: Generate health report
      template:
        src: health-report.md.j2
        dest: /tmp/fleet-health-{{ ansible_date_time.date }}.md
      delegate_to: localhost
      run_once: yes
```

**Assigned**: Unassigned  
**Target**: Q1 2026  
**Blocked**: No (depends on SERVICE_PORTS.md)

---

### 6. Disaster Recovery Documentation 🚨

**Issue**: No documented procedure for fleet-wide IP changes

**Impact**: High (if needed)  
**Effort**: Low  
**Priority**: 🟠 Medium

**Details**:
- FQDN architecture allows IP changes without code changes
- But procedure is not documented
- Critical for disaster recovery scenarios

**Recommended Solution**:

Create `docs/fqdn/DISASTER_RECOVERY.md`:

```markdown
# Fleet IP Change Procedure

## Scenario: Subnet Migration (192.168.10.x → 10.0.0.x)

1. Update DNS records on hx-dc-server
2. Update `group_vars/all/fqdn_map.yml` (hx_hosts_ip only)
3. Run playbooks (FQDNs remain unchanged)
4. Verify services with health checks
5. Update monitoring dashboards

**Key Insight**: FQDN-based architecture means IP changes
require NO code changes, only DNS and variable updates.
```

**Assigned**: Unassigned  
**Target**: Q4 2025  
**Blocked**: No

---

## Low Priority Issues 🔵

### 7. Automated Fleet Inventory Updates

**Issue**: No CI/CD integration to validate fleet inventory changes

**Impact**: Low  
**Effort**: Medium  
**Priority**: 🔵 Low

**Assigned**: Unassigned  
**Target**: Q1 2026

---

## Completed Items ✅

1. ✅ **FQDN Policy Definition** - Complete
2. ✅ **Violation Detection & Remediation** - Complete (Zero violations)
3. ✅ **Pre-commit Hook Enforcement** - Implemented and active
4. ✅ **Fleet Inventory Documentation** - Comprehensive (needs sync check)
5. ✅ **Ansible Variable Structure** - Single source of truth established

---

## Issue Summary

| Priority | Open | Blocked | Total |
|----------|------|---------|-------|
| 🔴 Critical | 0 | 0 | 0 |
| 🟡 High | 2 | 1 | 2 |
| 🟠 Medium | 4 | 0 | 4 |
| 🔵 Low | 1 | 0 | 1 |
| **Total** | **7** | **1** | **7** |

---

## Next Steps

### Immediate (This Sprint)
1. 🟡 **Identify the 2 servers with different access** (BLOCKED - needs user input)
2. 🟡 Audit playbooks vs fqdn_map.yml for sync issues

### Short-Term (Next Sprint)
1. 🟠 Create SERVICE_PORTS.md reference document
2. 🟠 Create DISASTER_RECOVERY.md procedures

### Long-Term (Q1 2026)
1. 🟠 Implement automated diagram generation
2. 🟠 Create fleet health check dashboard
3. 🔵 Add CI/CD fleet inventory validation

---

## Notes

- All action items extracted from fqdn_assessment.md
- Assessment rating: 🟢 Excellent - Production-ready with minor gaps
- Focus on operational improvements, not critical fixes
- FQDN policy is mature and well-enforced

---

**Backlog Owner**: DevOps Team  
**Last Updated**: October 12, 2025  
**Review Frequency**: Quarterly or when fleet changes occur

