# Ansible Best Practices for HX-Citadel

**Reference Source**: `tech_kb/ansible-devel` (Ansible Core 2.20.0.dev0)  
**Last Updated**: 2025-10-08  
**Status**: Mandatory Standards

---

## 🎯 Purpose

This document establishes **mandatory Ansible best practices** for the HX-Citadel project based on the official Ansible Core development repository. All playbooks, roles, and tasks must follow these standards.

**Rule**: When in doubt, reference `tech_kb/ansible-devel` - never guess!

---

## 📚 Reference Sources

### Primary References

1. **Ansible Core Source**: `/tech_kb/ansible-devel/`
2. **Module Library**: `/tech_kb/ansible-devel/lib/ansible/modules/`
3. **Module Utils**: `/tech_kb/ansible-devel/lib/ansible/module_utils/`
4. **Plugin Framework**: `/tech_kb/ansible-devel/lib/ansible/plugins/`
5. **Best Practices**: [Ansible Dev Guide](https://docs.ansible.com/ansible/devel/dev_guide/)

### Development Tools

- **Test Modules**: `tech_kb/ansible-devel/hacking/test-module.py`
- **Environment Setup**: `tech_kb/ansible-devel/hacking/env-setup`
- **Return Generator**: `tech_kb/ansible-devel/hacking/return_skeleton_generator.py`

---

## 🔧 Mandatory Module Standards

### 1. Always Use FQCN (Fully Qualified Collection Names)

**Rule**: NEVER use short module names. Always use `ansible.builtin.*` or collection FQCN.

❌ **WRONG**:
```yaml
- name: Install package
  apt:
    name: nginx
    state: present
```

✅ **CORRECT**:
```yaml
- name: Install package
  ansible.builtin.apt:
    name: nginx
    state: present
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/modules/` - all core modules

### 2. Module Syntax - Use YAML Dictionary Format

**Rule**: Use modern YAML dictionary format, not inline strings.

❌ **WRONG**:
```yaml
- service: name=nginx state=started
- locale_gen: "name={{ item }} state=present"
```

✅ **CORRECT**:
```yaml
- ansible.builtin.service:
    name: nginx
    state: started

- ansible.builtin.locale_gen:
    name: "{{ item }}"
    state: present
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/playbook/` - playbook parser

### 3. Use `loop` Instead of `with_items`

**Rule**: `with_*` keywords are legacy. Use `loop` for all iterations.

❌ **WRONG**:
```yaml
- ansible.builtin.apt:
    name: "{{ item }}"
    state: present
  with_items:
    - nginx
    - postgresql
```

✅ **CORRECT**:
```yaml
- ansible.builtin.apt:
    name: "{{ item }}"
    state: present
  loop:
    - nginx
    - postgresql
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/executor/` - task execution engine

---

## 📋 Playbook Structure Standards

### 1. Playbook Header Documentation

**Rule**: Every playbook must have a header with purpose, usage, and prerequisites.

✅ **CORRECT**:
```yaml
---
# ═══════════════════════════════════════════════════════════════════════════════
# PLAYBOOK NAME
# ═══════════════════════════════════════════════════════════════════════════════
# Purpose: Brief description of what this playbook does
# Usage: ansible-playbook -i inventory/prod.ini playbooks/example.yml
# 
# Prerequisites:
# - SSH connectivity to target hosts
# - Sudo/privilege escalation configured
# - Python interpreter available
#
# Safety:
# - Idempotent operations
# - Creates backups before modifications
# - Error handling with block/rescue/always
# ═══════════════════════════════════════════════════════════════════════════════

- name: Descriptive play name
  hosts: target_group
  become: yes
  gather_facts: yes
```

**Reference**: `tech_kb/ansible-devel/test/integration/` - integration test playbooks

### 2. Gather Facts Control

**Rule**: Explicitly set `gather_facts` based on needs.

```yaml
# If you need ansible_date_time, ansible_distribution, etc.
gather_facts: yes

# If you only need connectivity checks
gather_facts: no
```

**Why**: Gathering facts takes time and resources. Only gather when needed.

**Reference**: `tech_kb/ansible-devel/lib/ansible/executor/playbook_executor.py`

### 3. Error Handling - Block/Rescue/Always

**Rule**: Use block/rescue/always for robust error handling.

✅ **CORRECT**:
```yaml
tasks:
  - name: Critical operation with error handling
    block:
      - name: Check prerequisites
        ansible.builtin.stat:
          path: /etc/config
        register: config_exists
        
      - name: Backup existing config
        ansible.builtin.copy:
          src: /etc/config
          dest: /etc/config.backup
          remote_src: yes
        when: config_exists.stat.exists
        
      - name: Update configuration
        ansible.builtin.template:
          src: config.j2
          dest: /etc/config
          
    rescue:
      - name: Log failure
        ansible.builtin.debug:
          msg: "Configuration update failed on {{ inventory_hostname }}"
          
      - name: Restore backup if exists
        ansible.builtin.copy:
          src: /etc/config.backup
          dest: /etc/config
          remote_src: yes
        when: config_exists.stat.exists
        
    always:
      - name: Ensure service is running
        ansible.builtin.systemd:
          name: myservice
          state: started
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/playbook/block.py`

---

## 🎯 Task Best Practices

### 1. Idempotency

**Rule**: All tasks must be idempotent (safe to run multiple times).

✅ **CORRECT**:
```yaml
- name: Ensure directory exists
  ansible.builtin.file:
    path: /opt/app
    state: directory
    mode: "0755"
    
- name: Ensure package is installed
  ansible.builtin.apt:
    name: nginx
    state: present  # not 'latest' unless you mean it
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/modules/` - all core modules are idempotent

### 2. Use `changed_when` and `failed_when`

**Rule**: Control when tasks report changes or failures.

✅ **CORRECT**:
```yaml
- name: Check service status (read-only)
  ansible.builtin.command:
    cmd: systemctl status nginx
  register: service_status
  changed_when: false
  failed_when: false
  
- name: Run migration
  ansible.builtin.command:
    cmd: /opt/app/migrate.sh
  register: migration_result
  changed_when: "'Applied' in migration_result.stdout"
  failed_when: migration_result.rc != 0 and 'already applied' not in migration_result.stderr
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/executor/task_executor.py`

### 3. Conditional Execution

**Rule**: Use `when` conditions properly, understand variable evaluation.

✅ **CORRECT**:
```yaml
- name: Install on Debian/Ubuntu only
  ansible.builtin.apt:
    name: nginx
    state: present
  when: ansible_os_family == "Debian"

- name: Execute if variable is defined and true
  ansible.builtin.service:
    name: nginx
    state: started
  when: 
    - nginx_enabled is defined
    - nginx_enabled | bool
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/playbook/conditional.py`

---

## 🔐 Security Best Practices

### 1. Use `no_log` for Sensitive Data

**Rule**: Always use `no_log: true` for tasks handling passwords, keys, tokens.

✅ **CORRECT**:
```yaml
- name: Create database user
  community.postgresql.postgresql_user:
    name: "{{ db_user }}"
    password: "{{ db_password }}"
    db: "{{ db_name }}"
  become: yes
  become_user: postgres
  no_log: true
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/executor/task_executor.py`

### 2. Vault for Secrets

**Rule**: Use Ansible Vault for all sensitive data.

```bash
# Create encrypted vault
ansible-vault create group_vars/all/vault.yml

# Edit encrypted vault
ansible-vault edit group_vars/all/vault.yml

# Use in playbooks
ansible-playbook site.yml --ask-vault-pass
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/cli/vault.py`

### 3. Privilege Escalation

**Rule**: Use `become` appropriately, minimize scope.

✅ **CORRECT**:
```yaml
# Task-level escalation (preferred)
- name: Install system package
  ansible.builtin.apt:
    name: nginx
    state: present
  become: yes

# Play-level only when all tasks need it
- name: System configuration
  hosts: all
  become: yes
  tasks:
    # All tasks run as root
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/playbook/play_context.py`

---

## 📦 Variable Management

### 1. Variable Precedence

**Rule**: Understand and use variable precedence correctly.

**Order** (lowest to highest):
1. role defaults (`roles/*/defaults/main.yml`)
2. inventory vars
3. group_vars/all
4. group_vars/*
5. host_vars/*
6. play vars
7. task vars
8. extra vars (`-e` on command line)

**Reference**: `tech_kb/ansible-devel/lib/ansible/vars/`

### 2. Variable Naming

**Rule**: Use descriptive, namespaced variable names.

✅ **CORRECT**:
```yaml
# Role-specific variables (prefixed)
postgresql_version: "14"
postgresql_listen_address: "0.0.0.0"
postgresql_port: 5432

# Application variables (grouped)
app_name: "hx-citadel"
app_dir: "/opt/hx-citadel-shield"
app_user: "agent0"
```

❌ **WRONG**:
```yaml
# Generic, could conflict
version: "14"
port: 5432
user: "agent0"
```

### 3. Default Values with Filters

**Rule**: Use filters to provide safe defaults.

✅ **CORRECT**:
```yaml
- name: Use variable with default
  ansible.builtin.debug:
    msg: "Port: {{ app_port | default(8080) }}"

- name: Use with omit for optional parameters
  ansible.builtin.yum:
    name: postgresql
    enablerepo: "{{ postgresql_enablerepo | default(omit, true) }}"
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/plugins/filter/`

---

## 🧪 Testing Standards

### 1. Check Mode Support

**Rule**: Ensure tasks work in check mode (`--check`).

✅ **CORRECT**:
```yaml
- name: Task that supports check mode
  ansible.builtin.template:
    src: config.j2
    dest: /etc/config
  check_mode: yes  # Can be run in check mode

- name: Task that can't run in check mode
  ansible.builtin.command:
    cmd: /opt/app/migrate.sh
  check_mode: no  # Skip in check mode
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/executor/task_executor.py`

### 2. Testing Workflow

**Rule**: Always test before deploying to production.

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

### 3. Use Test Module Script

**Rule**: Test custom modules with the official test-module.py script.

```bash
# From tech_kb/ansible-devel
cd tech_kb/ansible-devel
source hacking/env-setup

# Test a module
./hacking/test-module.py -m /path/to/custom_module.py -a "arg1=value1"
```

**Reference**: `tech_kb/ansible-devel/hacking/test-module.py`

---

## 🎨 Template Best Practices

### 1. Jinja2 Templates

**Rule**: Use proper Jinja2 syntax and filters.

✅ **CORRECT**:
```jinja2
{# templates/config.j2 #}
# Configuration file for {{ app_name }}
# Generated by Ansible on {{ ansible_date_time.iso8601 }}

[server]
host = {{ app_host | default('0.0.0.0') }}
port = {{ app_port | default(8080) }}

[database]
url = postgresql://{{ db_user }}:{{ db_password }}@{{ db_host }}:{{ db_port }}/{{ db_name }}

{# Conditional sections #}
{% if app_debug | default(false) %}
[debug]
enabled = true
level = debug
{% endif %}

{# Loop over items #}
{% for item in app_allowed_hosts %}
allowed_host = {{ item }}
{% endfor %}
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/template/`

### 2. Template Validation

**Rule**: Validate templates before deployment.

✅ **CORRECT**:
```yaml
- name: Generate configuration
  ansible.builtin.template:
    src: config.j2
    dest: /etc/app/config.ini
    backup: yes
    validate: '/usr/bin/python3 -c "import configparser; configparser.ConfigParser().read(\"%s\")"'
```

---

## 📊 Performance Optimization

### 1. Minimize Fact Gathering

**Rule**: Only gather facts when needed.

```yaml
# Don't need facts
- hosts: all
  gather_facts: no
  tasks:
    - ansible.builtin.ping:

# Need facts
- hosts: all
  gather_facts: yes
  tasks:
    - ansible.builtin.debug:
        msg: "OS: {{ ansible_distribution }}"
```

### 2. Use Pipelining

**Rule**: Enable SSH pipelining for faster execution.

**In ansible.cfg**:
```ini
[ssh_connection]
pipelining = True
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/plugins/connection/ssh.py`

### 3. Parallel Execution

**Rule**: Use forks for parallel execution.

```bash
# Default is 5, increase for large fleets
ansible-playbook -i inventory/prod.ini site.yml --forks 10
```

**In ansible.cfg**:
```ini
[defaults]
forks = 10
```

---

## 🔍 Debugging Standards

### 1. Verbose Output

**Rule**: Use appropriate verbosity levels.

```bash
# Normal
ansible-playbook site.yml

# Basic verbose (-v)
ansible-playbook site.yml -v

# More verbose (-vv) - shows task results
ansible-playbook site.yml -vv

# Very verbose (-vvv) - shows connections
ansible-playbook site.yml -vvv

# Debug mode (-vvvv) - shows everything
ansible-playbook site.yml -vvvv
```

### 2. Debug Tasks

**Rule**: Use debug module effectively.

✅ **CORRECT**:
```yaml
- name: Show variable content
  ansible.builtin.debug:
    var: my_variable
    
- name: Show formatted message
  ansible.builtin.debug:
    msg: "Value is {{ my_variable }}"
    
- name: Conditional debug
  ansible.builtin.debug:
    msg: "This runs in debug mode"
  when: ansible_verbosity >= 2
```

**Reference**: `tech_kb/ansible-devel/lib/ansible/modules/debug.py`

---

## 📚 Documentation Standards

### 1. Role Documentation

**Rule**: Every role must have a README.md.

**Template**:
```markdown
# Role Name

## Description
Brief description of what this role does.

## Requirements
- Ansible 2.14+
- Python 3.10+
- Target OS: Ubuntu 22.04+

## Role Variables
| Variable | Default | Description |
|----------|---------|-------------|
| app_port | 8080 | Application port |
| app_debug | false | Enable debug mode |

## Dependencies
- role: geerlingguy.postgresql
- collection: community.general

## Example Playbook
\`\`\`yaml
- hosts: servers
  roles:
    - role: my-role
      vars:
        app_port: 9000
\`\`\`

## License
MIT

## Author
HX-Citadel Team
```

### 2. Task Comments

**Rule**: Comment complex tasks and logic.

✅ **CORRECT**:
```yaml
- name: Configure PostgreSQL (complex multi-line regex)
  ansible.builtin.lineinfile:
    path: /etc/postgresql/14/main/postgresql.conf
    # Match any variation of the parameter (commented or not)
    regexp: '^\s*#?\s*listen_addresses\s*='
    line: "listen_addresses = '{{ postgresql_listen_address }}'"
    backup: yes
  # Restart required for this change
  notify: restart postgresql
```

---

## ✅ Code Review Checklist

Before committing any Ansible code, verify:

- [ ] All modules use FQCN (`ansible.builtin.*` or collection name)
- [ ] No short module names (no `apt:`, use `ansible.builtin.apt:`)
- [ ] Using `loop` instead of `with_items`
- [ ] YAML dictionary format (not inline strings)
- [ ] `gather_facts` explicitly set
- [ ] Error handling with `block/rescue/always` for critical tasks
- [ ] `changed_when` and `failed_when` used appropriately
- [ ] `no_log: true` for sensitive data
- [ ] Variables have descriptive names
- [ ] Defaults provided with `default()` filter
- [ ] Playbook has header documentation
- [ ] Check mode support considered
- [ ] Idempotent operations
- [ ] Templates validated
- [ ] Tested with `--check` and `--diff`

---

## 🚫 Common Anti-Patterns to Avoid

### ❌ Don't Shell Out When Module Exists

**WRONG**:
```yaml
- ansible.builtin.shell: apt-get install nginx
```

**CORRECT**:
```yaml
- ansible.builtin.apt:
    name: nginx
    state: present
```

### ❌ Don't Use `command` for File Operations

**WRONG**:
```yaml
- ansible.builtin.command: mkdir -p /opt/app
```

**CORRECT**:
```yaml
- ansible.builtin.file:
    path: /opt/app
    state: directory
```

### ❌ Don't Ignore Errors Unless Necessary

**WRONG**:
```yaml
- ansible.builtin.command: risky_operation
  ignore_errors: yes
```

**CORRECT**:
```yaml
- ansible.builtin.command: risky_operation
  register: result
  failed_when: result.rc != 0 and 'expected_error' not in result.stderr
```

---

## 🔗 Quick Reference Links

### Official Documentation
- [Ansible Dev Guide](https://docs.ansible.com/ansible/devel/dev_guide/)
- [Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
- [Module Index](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html)

### Local References
- Ansible Core Source: `tech_kb/ansible-devel/`
- Module Examples: `tech_kb/ansible-devel/lib/ansible/modules/`
- Test Tools: `tech_kb/ansible-devel/hacking/`

---

## 📝 Decision Process

**When writing Ansible code:**

1. **Question**: "How should I do X?"
2. **Answer**: Check these in order:
   - ✅ This best practices document
   - ✅ `tech_kb/ansible-devel/lib/ansible/modules/` for module usage
   - ✅ Official Ansible documentation
   - ❌ DON'T guess or use outdated tutorials

3. **If unsure**: 
   - Reference the ansible-devel source code
   - Check how core modules implement similar functionality
   - Ask for review before committing

---

## 🎯 Enforcement

**All pull requests must**:
1. Follow these best practices
2. Pass `ansible-lint`
3. Pass `--check` mode
4. Include documentation
5. Have error handling
6. Use FQCN for all modules

**No exceptions.**

---

**Last Updated**: 2025-10-08  
**Review Cycle**: Quarterly or when Ansible version updates  
**Source**: `tech_kb/ansible-devel` (Ansible Core 2.20.0.dev0)

---

**Remember**: When in doubt, check `tech_kb/ansible-devel` - never guess! 🎯
