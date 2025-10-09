# Ansible Quick Reference Card

**For**: HX-Citadel Project  
**Source**: `tech_kb/ansible-devel` (Ansible Core 2.20.0.dev0)  
**Rule**: Never guess - always reference official standards!

---

## ✅ Module Usage Checklist

```yaml
# ✅ ALWAYS DO THIS
- name: Descriptive task name
  ansible.builtin.module_name:        # FQCN required
    parameter: value                   # YAML dict format
    state: present                     # Explicit state
  loop:                                # Modern loop syntax
    - item1
    - item2
  when: condition                      # Clear conditions
  register: result                     # Capture output
  changed_when: false                  # Control reporting
  failed_when: false                   # Control failures
  become: yes                          # Explicit privilege
  no_log: true                         # For sensitive data
```

---

## 🚫 Common Mistakes

| ❌ WRONG | ✅ CORRECT |
|----------|-----------|
| `apt:` | `ansible.builtin.apt:` |
| `service: name=nginx state=started` | `ansible.builtin.service:`<br>`  name: nginx`<br>`  state: started` |
| `with_items:` | `loop:` |
| `gather_facts: no` (when you need facts) | `gather_facts: yes` |
| `ignore_errors: yes` | `failed_when: result.rc != 0 and 'ok' not in result.stderr` |
| `command: mkdir /opt/app` | `ansible.builtin.file: path=/opt/app state=directory` |

---

## 📋 Playbook Template

```yaml
---
# ═══════════════════════════════════════════════════════════════════════════════
# PLAYBOOK NAME
# ═══════════════════════════════════════════════════════════════════════════════
# Purpose: What this does
# Usage: ansible-playbook -i inventory/prod.ini playbooks/example.yml
# Prerequisites: SSH, sudo, Python
# Safety: Idempotent, backs up, error handling
# ═══════════════════════════════════════════════════════════════════════════════

- name: Play name
  hosts: target_group
  become: yes
  gather_facts: yes
  tags:
    - tag1
    - tag2
  
  tasks:
    - name: Task with error handling
      block:
        - name: Main task
          ansible.builtin.module:
            parameter: value
            
      rescue:
        - name: Handle error
          ansible.builtin.debug:
            msg: "Failed"
            
      always:
        - name: Cleanup
          ansible.builtin.debug:
            msg: "Done"
```

---

## 🧪 Testing Commands

```bash
# Syntax check
ansible-playbook --syntax-check site.yml

# Lint check
ansible-lint site.yml

# Check mode (dry run)
ansible-playbook -i inventory/prod.ini site.yml --check

# With diff
ansible-playbook -i inventory/prod.ini site.yml --check --diff

# Limited to one host
ansible-playbook -i inventory/prod.ini site.yml --limit hx-test-server

# Verbose
ansible-playbook -i inventory/prod.ini site.yml -vv
```

---

## 🔧 Common Patterns

### File Operations

```yaml
# Create directory
- ansible.builtin.file:
    path: /opt/app
    state: directory
    owner: agent0
    group: agent0
    mode: "0755"

# Copy file
- ansible.builtin.copy:
    src: local/file
    dest: /remote/file
    backup: yes
    
# Template
- ansible.builtin.template:
    src: config.j2
    dest: /etc/config
    backup: yes
    validate: 'check_command %s'
```

### Package Management

```yaml
# Install package
- ansible.builtin.apt:
    name: nginx
    state: present
    update_cache: yes

# Multiple packages
- ansible.builtin.apt:
    name:
      - nginx
      - postgresql
    state: present
```

### Service Management

```yaml
# Start service
- ansible.builtin.systemd:
    name: nginx
    state: started
    enabled: yes
    daemon_reload: yes
```

### Command Execution

```yaml
# Run command (idempotent)
- ansible.builtin.command:
    cmd: /opt/app/script.sh
  args:
    creates: /opt/app/.initialized
  register: result
  changed_when: "'Created' in result.stdout"
```

---

## 🔐 Security Patterns

```yaml
# Sensitive data
- community.postgresql.postgresql_user:
    name: "{{ db_user }}"
    password: "{{ db_password }}"
  become: yes
  become_user: postgres
  no_log: true

# Vault usage
# In group_vars/all/vault.yml (encrypted):
vault_db_password: "secret123"

# In playbook:
db_password: "{{ vault_db_password }}"
```

---

## 📊 Variables

```yaml
# Role defaults (roles/*/defaults/main.yml)
app_port: 8080

# With defaults
port: "{{ app_port | default(8080) }}"

# Optional parameters
enablerepo: "{{ repo_name | default(omit, true) }}"

# Conditional
when:
  - variable is defined
  - variable | bool
  - ansible_os_family == "Debian"
```

---

## 🎯 Where to Look

| Need | Look Here |
|------|-----------|
| Module syntax | `tech_kb/ansible-devel/lib/ansible/modules/` |
| Test module | `tech_kb/ansible-devel/hacking/test-module.py` |
| Best practices | `docs/ANSIBLE-BEST-PRACTICES.md` |
| Examples | `tech_kb/ansible-devel/test/integration/` |
| Filters | `tech_kb/ansible-devel/lib/ansible/plugins/filter/` |

---

## ⚡ Quick Commands

```bash
# Test connectivity
ansible all -i inventory/prod.ini -m ping

# Check service status
ansible all -i inventory/prod.ini -m systemd -a "name=postgresql" -b

# Run ad-hoc command
ansible all -i inventory/prod.ini -m shell -a "uptime" -b

# Gather facts
ansible all -i inventory/prod.ini -m setup

# Copy file to all hosts
ansible all -i inventory/prod.ini -m copy -a "src=/local/file dest=/remote/file" -b
```

---

## 🎓 Remember

1. **Always FQCN** - `ansible.builtin.*`
2. **Always test** - `--check --diff`
3. **Always error handle** - `block/rescue/always`
4. **Always document** - Comments and headers
5. **Always idempotent** - Safe to re-run
6. **Never guess** - Check `tech_kb/ansible-devel`

---

**Full Guide**: [ANSIBLE-BEST-PRACTICES.md](./ANSIBLE-BEST-PRACTICES.md)  
**When in doubt**: Check `tech_kb/ansible-devel` 🎯
