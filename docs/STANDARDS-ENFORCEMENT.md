# Standards Enforcement Policy

**Effective Date**: 2025-10-08  
**Authority**: Infrastructure Team  
**Status**: ⭐ MANDATORY

---

## 🎯 Purpose

This document establishes the **enforcement policy** for Ansible coding standards in the HX-Citadel project. All code must comply with standards based on the official Ansible Core development repository (`tech_kb/ansible-devel`).

---

## 📜 Core Principle

> **"Never guess - always reference official standards"**

When writing Ansible code, you must:
1. ✅ Reference `tech_kb/ansible-devel` for official implementations
2. ✅ Follow `docs/ANSIBLE-BEST-PRACTICES.md`
3. ✅ Use `docs/QUICK-REFERENCE.md` for common patterns
4. ❌ **NEVER** guess syntax or use outdated tutorials

---

## ⚖️ Mandatory Requirements

### 1. FQCN (Fully Qualified Collection Names)

**Rule**: ALL modules must use FQCN. NO SHORT NAMES.

**Enforcement**: 
- `.ansible-lint` configured with `fqcn-builtins: enable`
- CI/CD pipeline will fail if short names detected
- Code reviews will reject PRs with short names

**Examples**:
```yaml
# ❌ REJECTED
- apt: name=nginx state=present
- service: name=nginx state=started

# ✅ APPROVED
- ansible.builtin.apt:
    name: nginx
    state: present
- ansible.builtin.service:
    name: nginx
    state: started
```

### 2. Modern Syntax

**Rule**: Use modern YAML dict format and `loop` (not `with_*`).

**Enforcement**:
- Code reviews check for deprecated syntax
- ansible-lint warns on deprecated patterns
- Pre-commit hooks validate syntax

**Examples**:
```yaml
# ❌ REJECTED
- service: name=nginx state=started
- apt: "name={{ item }}"
  with_items:
    - nginx
    - postgresql

# ✅ APPROVED
- ansible.builtin.service:
    name: nginx
    state: started
- ansible.builtin.apt:
    name: "{{ item }}"
  loop:
    - nginx
    - postgresql
```

### 3. Error Handling

**Rule**: Critical operations must use `block/rescue/always`.

**Enforcement**:
- Code reviews check for error handling
- Deployment playbooks require error handling
- No `ignore_errors: yes` without justification

**Example**:
```yaml
# ✅ APPROVED
- name: Critical update
  block:
    - name: Backup config
      ansible.builtin.copy:
        src: /etc/config
        dest: /etc/config.backup
        remote_src: yes
        
    - name: Update config
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
    - name: Restart service
      ansible.builtin.systemd:
        name: myservice
        state: restarted
```

### 4. Documentation

**Rule**: All playbooks must have header documentation.

**Enforcement**:
- Template provided in `docs/QUICK-REFERENCE.md`
- Code reviews check for documentation
- Undocumented playbooks will be rejected

**Required Header**:
```yaml
---
# ═══════════════════════════════════════════════════════════════════════════════
# PLAYBOOK NAME
# ═══════════════════════════════════════════════════════════════════════════════
# Purpose: What this playbook does
# Usage: ansible-playbook -i inventory/prod.ini playbooks/example.yml
# 
# Prerequisites:
# - List requirements
#
# Safety:
# - Describe safety measures
# ═══════════════════════════════════════════════════════════════════════════════
```

### 5. Testing

**Rule**: All code must pass tests before deployment.

**Required Tests**:
```bash
# 1. Syntax check
ansible-playbook --syntax-check site.yml

# 2. Lint check
ansible-lint site.yml

# 3. Check mode
ansible-playbook -i inventory/prod.ini site.yml --check

# 4. Pre-flight validation
ansible-playbook -i inventory/prod.ini playbooks/preflight-check.yml
```

**Enforcement**:
- CI/CD pipeline runs all tests
- PRs must pass all checks
- No direct commits to main without passing tests

---

## 🔍 Code Review Checklist

Every PR must verify:

### Module Usage
- [ ] All modules use FQCN (`ansible.builtin.*` or collection name)
- [ ] No short module names (no `apt:`, `service:`, `file:`, etc.)
- [ ] YAML dictionary format used (not inline strings)
- [ ] `loop` used instead of `with_items`

### Syntax & Style
- [ ] Modern syntax (YAML dict, not inline)
- [ ] Proper indentation (2 spaces)
- [ ] Task names are descriptive
- [ ] Variables use descriptive names

### Error Handling
- [ ] `block/rescue/always` for critical operations
- [ ] `changed_when` used for command/shell tasks
- [ ] `failed_when` used appropriately
- [ ] No `ignore_errors` without justification

### Security
- [ ] `no_log: true` for sensitive data
- [ ] Passwords/tokens in vault files
- [ ] `become` used appropriately (minimal scope)

### Testing & Validation
- [ ] `gather_facts` explicitly set
- [ ] Idempotent operations
- [ ] Check mode support considered
- [ ] Tested with `--check --diff`

### Documentation
- [ ] Playbook header with purpose/usage
- [ ] Complex tasks have comments
- [ ] README updated if needed
- [ ] CHANGELOG entry added

---

## 🚫 Automatic Rejection Criteria

PRs will be **automatically rejected** if:

1. ❌ Short module names used (e.g., `apt:` instead of `ansible.builtin.apt:`)
2. ❌ ansible-lint fails with errors
3. ❌ Syntax check fails
4. ❌ No documentation header
5. ❌ Secrets in plain text (not vaulted)
6. ❌ No error handling for critical operations
7. ❌ Deprecated syntax (`with_items`, inline strings)

---

## ✅ Approval Process

### Step 1: Self-Check
```bash
# Developer runs before committing
ansible-playbook --syntax-check playbooks/myplaybook.yml
ansible-lint playbooks/myplaybook.yml
```

### Step 2: Pre-Commit Hook
```bash
# Automatically runs on git commit
# Validates syntax and lint
```

### Step 3: CI/CD Pipeline
```bash
# Runs on PR creation
# Full test suite including:
# - Syntax validation
# - Lint checks
# - Check mode execution
# - Integration tests (if applicable)
```

### Step 4: Code Review
```bash
# Human reviewer verifies:
# - Follows best practices
# - Proper documentation
# - Error handling
# - Security considerations
```

### Step 5: Approval & Merge
```bash
# PR approved only after:
# - All automated checks pass
# - Code review approval
# - Documentation updated
```

---

## 📚 Reference Materials

### Primary References
| Document | Purpose | Location |
|----------|---------|----------|
| **Best Practices** | Comprehensive standards guide | `docs/ANSIBLE-BEST-PRACTICES.md` |
| **Quick Reference** | Common patterns & quick lookup | `docs/QUICK-REFERENCE.md` |
| **Ansible Core Source** | Official implementation reference | `tech_kb/ansible-devel/` |
| **Deployment Guide** | Deployment procedures | `docs/DEPLOYMENT-GUIDE.md` |

### Code Examples
| Type | Location |
|------|----------|
| Core Modules | `tech_kb/ansible-devel/lib/ansible/modules/` |
| Module Utils | `tech_kb/ansible-devel/lib/ansible/module_utils/` |
| Plugins | `tech_kb/ansible-devel/lib/ansible/plugins/` |
| Integration Tests | `tech_kb/ansible-devel/test/integration/` |

---

## 🔧 Tools & Configuration

### Linting
- **File**: `.ansible-lint`
- **Profile**: Production-grade enforcement
- **FQCN**: Enforced (`fqcn-builtins: enable`)
- **Command**: `ansible-lint playbooks/`

### Editor Configuration
- **File**: `.editorconfig`
- **YAML Indent**: 2 spaces
- **Encoding**: UTF-8
- **Line Endings**: LF

### Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running Ansible syntax check..."
for file in $(git diff --cached --name-only | grep -E '\.ya?ml$'); do
    ansible-playbook --syntax-check "$file" || exit 1
done

echo "Running ansible-lint..."
ansible-lint || exit 1

echo "All checks passed!"
```

---

## 📊 Metrics & Reporting

### Quality Metrics
- **FQCN Compliance**: 100% required
- **Lint Pass Rate**: 100% required
- **Test Coverage**: All playbooks tested
- **Documentation**: All playbooks documented

### Monthly Review
- Review compliance statistics
- Update best practices if needed
- Address common violations
- Training for repeated issues

---

## 🎓 Training & Support

### For New Team Members
1. Read `docs/ANSIBLE-BEST-PRACTICES.md`
2. Review `docs/QUICK-REFERENCE.md`
3. Study examples in `tech_kb/ansible-devel/`
4. Practice with `--check` mode
5. Get code review feedback

### For Existing Team
1. Quarterly review of best practices
2. Updates when Ansible version changes
3. Share learnings from incidents
4. Document new patterns

### Getting Help
1. Check `docs/ANSIBLE-BEST-PRACTICES.md`
2. Review `tech_kb/ansible-devel/` source
3. Ask in team chat with specific questions
4. Request code review for guidance

---

## 🚨 Violations & Remediation

### Minor Violations
- **Examples**: Missing comment, inconsistent spacing
- **Action**: Fix in current PR
- **Timeline**: Before merge

### Major Violations
- **Examples**: Short module names, no error handling, no documentation
- **Action**: PR rejected, must fix before re-review
- **Timeline**: Fix and resubmit

### Critical Violations
- **Examples**: Secrets in plain text, destructive operations without safeguards
- **Action**: PR blocked, security review required
- **Timeline**: Must be reviewed by senior engineer

---

## 📅 Review & Updates

### Document Review
- **Frequency**: Quarterly or when Ansible updates
- **Owner**: Infrastructure Team Lead
- **Process**: Review, update, communicate changes

### Standards Updates
- **Trigger**: New Ansible version, incidents, feedback
- **Process**: Document change, update examples, train team
- **Notification**: All team members via email + chat

---

## 🎯 Success Criteria

**This policy is successful when**:

1. ✅ 100% of code uses FQCN
2. ✅ All PRs pass automated checks
3. ✅ Zero production incidents from bad Ansible code
4. ✅ Code reviews focus on logic, not syntax
5. ✅ New team members quickly learn standards
6. ✅ Codebase maintainability improves
7. ✅ Deployment confidence increases

---

## 📝 Amendments

| Date | Change | Reason |
|------|--------|--------|
| 2025-10-08 | Initial version | Establish standards based on ansible-devel reference |

---

## 🔗 Quick Links

- [Best Practices Guide](./ANSIBLE-BEST-PRACTICES.md)
- [Quick Reference Card](./QUICK-REFERENCE.md)
- [Deployment Guide](./DEPLOYMENT-GUIDE.md)
- [Implementation Summary](./IMPLEMENTATION-SUMMARY.md)
- [Ansible Core Reference](../tech_kb/ansible-devel/)

---

**Status**: ⭐ MANDATORY - No Exceptions  
**Enforcement**: CI/CD Pipeline + Code Review  
**Authority**: Infrastructure Team  
**Questions**: See team lead or reference materials

---

**Remember**: When in doubt, check `tech_kb/ansible-devel` - never guess! 🎯
