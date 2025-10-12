# Ansible Infrastructure - Issues & Action Items Backlog

**Created**: October 12, 2025  
**Source**: ansible_infra_assessment.md comprehensive review  
**Assessment**: Comprehensive infrastructure analysis (1,808 lines)  
**Status**: ✅ **Migrated to GitHub Issues**  
**Priority Matrix**: 🔴 Critical | 🟡 High | 🟠 Medium | 🔵 Low

---

## 🔗 GitHub Issues

**All backlog items have been migrated to GitHub Issues for tracking:**

### Critical Security Issues 🔴
- **Issue #20**: 🔴 SECURITY: Vault file management - vault.yml.broken
- **Issue #21**: 🔴 SECURITY: Multiple critical hardening issues
  - Disabled host_key_checking in ansible.cfg
  - PostgreSQL listening on 0.0.0.0
  - Redis without authentication (commented out!)
  - Related to #5 (StrictHostKeyChecking)
  - Related to #18 (Redis IP hardcoding)

### High Priority Items 🟡
- **Issue #22**: 📚 Create README.md for all 24 roles
- **Issue #23**: 🔄 Create rollback/recovery playbooks

### Medium Priority Items 🟠
- **Issue #24**: 🏗️ Separate inventory files (dev/staging/prod)
- **Issue #25**: 📊 Implement monitoring and alerting

**View all deployment issues**: `gh issue list --label enhancement,security`

**This document remains as reference documentation and implementation guide.**

---

## Critical Findings Summary

### 1. Vault Management Crisis 🔴

**Status**: CRITICAL - vault.yml.broken file exists

**Issues:**
- Unclear what caused vault failure
- No documented recovery procedures
- Risk of permanent secret loss

**Tracked in**: Issue #20

---

### 2. Security Hardening Required 🔴

**Multiple vulnerabilities identified:**

#### A. Disabled Host Key Checking
```ini
# ansible.cfg
host_key_checking = False  # MITM vulnerability
```

#### B. PostgreSQL Too Permissive
```yaml
# group_vars/db_nodes.yml
postgresql_listen_address: "0.0.0.0"  # Exposed to network
```

#### C. Redis No Authentication
```yaml
# group_vars/db_nodes.yml
# redis_requirepass: "CHANGEME_STRONG"  # Commented out!
```

**Tracked in**: Issue #21

---

### 3. Missing Role Documentation 📚

**Issue**: 0 of 24 roles have proper README.md files

**Impact:**
- Difficult onboarding
- No variable documentation
- Maintenance challenges

**Tracked in**: Issue #22

---

### 4. No Rollback Procedures 🔄

**Missing playbooks:**
- Orchestrator rollback
- Database rollback (PostgreSQL/Redis)
- Service recovery procedures
- Full fleet recovery

**Tracked in**: Issue #23

---

### 5. No Environment Separation 🏗️

**Issue**: Single inventory/prod.ini for all environments

**Risk**: Accidental production deployment

**Tracked in**: Issue #24

---

### 6. No Monitoring Configuration 📊

**Missing:**
- Prometheus exporters
- Grafana dashboards
- Alert rules
- Health monitoring

**Tracked in**: Issue #25

---

## Assessment Highlights

### Overall Rating
**7.5/10** - Well-architected but needs security hardening and operational tooling

### Strengths ✅
1. **Excellent FQDN-based design** (prevents IP hardcoding)
2. **Well-structured role hierarchy** (24 specialized roles)
3. **Comprehensive variable layering** (global → group → host)
4. **Modular playbook design** (clear deployment stages)
5. **Strong testing framework**
6. **Good documentation coverage**

### Critical Gaps 🔴
1. **Vault management issues** (vault.yml.broken)
2. **Security vulnerabilities** (4 critical findings)
3. **No rollback procedures** (except MCP)
4. **Missing role documentation** (0 of 24)

### Medium Gaps 🟠
1. Environment inventory separation
2. Monitoring/alerting setup
3. Template version control
4. Role dependency documentation

---

## Statistics

**Repository Size:**
- Total YAML Files: 217
- Custom Roles: 24
- Galaxy Roles: 2
- Playbooks: 26
- Inventory Files: 2
- Scripts: 9
- Test Files: 20+

**Fleet Size:**
- Managed Hosts: 17
- Host Groups: 8
- Network: 192.168.10.0/24
- Domain: dev-test.hana-x.ai

---

## Priority Recommendations

### Immediate (This Week) 🔴
1. ✅ Investigate and fix vault.yml.broken (Issue #20)
2. ✅ Enable host_key_checking in ansible.cfg (Issue #21)
3. ✅ Configure Redis authentication (Issue #21)
4. ✅ Restrict PostgreSQL listen address (Issue #21)

### Short-Term (This Month) 🟡
1. ✅ Create rollback playbooks (Issue #23)
2. ✅ Document all 24 roles with READMEs (Issue #22)

### Long-Term (Next Quarter) 🟠
1. ✅ Separate dev/staging/prod inventories (Issue #24)
2. ✅ Implement monitoring (Issue #25)

---

## Related Issues

**Also see:**
- docs/fqdn/FQDN-BACKLOG.md (7 FQDN-related issues)
- tests/TEST-BACKLOG.md (8 testing-related issues)

**Total Open Issues**: 18+ across all backlogs

---

## Quick Commands

```bash
# View all security issues
gh issue list --label security

# View all deployment-related
gh issue list --label enhancement | grep -E "rollback|vault|inventory|monitoring"

# View critical infrastructure issues
gh issue list --label priority:critical | grep -v testing
```

---

**Backlog Owner**: Infrastructure/DevOps Team  
**Last Updated**: October 12, 2025  
**Next Review**: After security issues resolved  
**Source**: ansible_infra_assessment.md (1,808 lines, 34 recommendations)

