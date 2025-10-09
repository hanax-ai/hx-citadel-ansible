# Component 1: Base System Setup
## Orchestrator Server Foundation - Ansible Deployment Plan

**Component:** Base System Setup  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Timeline:** Week 1, Days 1-2 (2-3 hours)  
**Priority:** ⭐ **CRITICAL - FOUNDATION**  
**Dependencies:** None (first deployment phase)

---

## Overview

This plan covers the base system setup for the Shield Orchestrator Server, including:

- Server provisioning and domain join
- Python 3.12 environment setup
- System dependencies installation
- Directory structure creation
- Service user configuration
- Virtual environment setup

**This is the foundation for all subsequent component deployments.**

---

## Ansible Role Structure

```
roles/orchestrator_base_setup/
├── defaults/
│   └── main.yml              # Default variables
├── tasks/
│   ├── main.yml              # Task orchestrator
│   ├── 01-system-packages.yml
│   ├── 02-service-user.yml
│   ├── 03-directories.yml
│   ├── 04-python-setup.yml
│   └── 05-validation.yml
├── templates/
│   └── (none for base setup)
├── handlers/
│   └── main.yml              # Handlers (if needed)
└── vars/
    └── main.yml              # Role variables
```

---

## defaults/main.yml

```yaml
---
# Orchestrator Base Configuration
orchestrator_service_user: "orchestrator"
orchestrator_service_group: "orchestrator"
orchestrator_user_uid: 1001
orchestrator_group_gid: 1001
orchestrator_user_home: "/home/orchestrator"
orchestrator_user_shell: "/bin/bash"

# Application directories
orchestrator_base_dir: "/opt/hx-citadel-shield"
orchestrator_app_dir: "/opt/hx-citadel-shield/orchestrator"
orchestrator_venv_dir: "/opt/hx-citadel-shield/orchestrator-venv"
orchestrator_data_dir: "/opt/hx-citadel-shield/data"
orchestrator_log_dir: "/var/log/hx-citadel/orchestrator"

# LightRAG data directories
lightrag_working_dir: "/opt/hx-citadel-shield/data/lightrag"
lightrag_cache_dir: "/opt/hx-citadel-shield/data/lightrag/cache"
lightrag_logs_dir: "/opt/hx-citadel-shield/data/lightrag/logs"
lightrag_checkpoints_dir: "/opt/hx-citadel-shield/data/lightrag/checkpoints"

# Python configuration
python_version: "3.12"
python_pip_version: "latest"

# System packages
base_packages:
  - python3.12
  - python3.12-venv
  - python3.12-dev
  - python3-pip
  - build-essential
  - libpq-dev        # PostgreSQL client
  - libssl-dev       # SSL/TLS
  - libffi-dev       # Foreign function interface
  - redis-tools      # Redis CLI
  - postgresql-client  # PostgreSQL CLI
  - curl
  - wget
  - git
  - jq
  - htop
  - vim
```

---

## tasks/main.yml

```yaml
---
# Main task orchestrator
- name: Include system packages installation
  ansible.builtin.import_tasks: 01-system-packages.yml
  tags: [base, packages]

- name: Include service user creation
  ansible.builtin.import_tasks: 02-service-user.yml
  tags: [base, user]

- name: Include directory structure creation
  ansible.builtin.import_tasks: 03-directories.yml
  tags: [base, directories]

- name: Include Python environment setup
  ansible.builtin.import_tasks: 04-python-setup.yml
  tags: [base, python]

- name: Include validation tasks
  ansible.builtin.import_tasks: 05-validation.yml
  tags: [base, validation]
```

---

## tasks/01-system-packages.yml

```yaml
---
# System package installation
- name: Update apt cache
  ansible.builtin.apt:
    update_cache: yes
    cache_valid_time: 3600
  become: yes
  tags: [packages]

- name: Install base system packages
  ansible.builtin.apt:
    name: "{{ base_packages }}"
    state: present
  become: yes
  tags: [packages]

- name: Verify Python 3.12 installation
  ansible.builtin.command: python3.12 --version
  register: python_version_check
  changed_when: false
  failed_when: "'Python 3.12' not in python_version_check.stdout"
  tags: [packages, validation]

- name: Display Python version
  ansible.builtin.debug:
    msg: "Installed: {{ python_version_check.stdout }}"
  tags: [packages]
```

---

## tasks/02-service-user.yml

```yaml
---
# Service user and group creation
- name: Create orchestrator group
  ansible.builtin.group:
    name: "{{ orchestrator_service_group }}"
    gid: "{{ orchestrator_group_gid }}"
    state: present
  become: yes
  tags: [user]

- name: Create orchestrator user
  ansible.builtin.user:
    name: "{{ orchestrator_service_user }}"
    uid: "{{ orchestrator_user_uid }}"
    group: "{{ orchestrator_service_group }}"
    home: "{{ orchestrator_user_home }}"
    shell: "{{ orchestrator_user_shell }}"
    create_home: yes
    comment: "Shield Orchestrator Service User"
    state: present
  become: yes
  tags: [user]

- name: Add orchestrator user to required groups
  ansible.builtin.user:
    name: "{{ orchestrator_service_user }}"
    groups: 
      - "{{ orchestrator_service_group }}"
    append: yes
  become: yes
  tags: [user]

- name: Set orchestrator user home permissions
  ansible.builtin.file:
    path: "{{ orchestrator_user_home }}"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0755"
    state: directory
  become: yes
  tags: [user]
```

---

## tasks/03-directories.yml

```yaml
---
# Directory structure creation
- name: Create base application directory
  ansible.builtin.file:
    path: "{{ orchestrator_base_dir }}"
    state: directory
    owner: root
    group: root
    mode: "0755"
  become: yes
  tags: [directories]

- name: Create orchestrator application directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0755"
  loop:
    - "{{ orchestrator_app_dir }}"
    - "{{ orchestrator_app_dir }}/config"
    - "{{ orchestrator_app_dir }}/models"
    - "{{ orchestrator_app_dir }}/services"
    - "{{ orchestrator_app_dir }}/agents"
    - "{{ orchestrator_app_dir }}/workflows"
    - "{{ orchestrator_app_dir }}/workers"
    - "{{ orchestrator_app_dir }}/api"
    - "{{ orchestrator_app_dir }}/database"
    - "{{ orchestrator_app_dir }}/utils"
    - "{{ orchestrator_app_dir }}/tests"
  become: yes
  tags: [directories]

- name: Create data directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0750"
  loop:
    - "{{ orchestrator_data_dir }}"
    - "{{ lightrag_working_dir }}"
    - "{{ lightrag_working_dir }}/vdb"
    - "{{ lightrag_cache_dir }}"
    - "{{ lightrag_cache_dir }}/entity_extraction"
    - "{{ lightrag_cache_dir }}/relationship_extraction"
    - "{{ lightrag_logs_dir }}"
    - "{{ lightrag_checkpoints_dir }}"
  become: yes
  tags: [directories]

- name: Create log directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0755"
  loop:
    - "{{ orchestrator_log_dir }}"
    - "{{ orchestrator_log_dir }}/api"
    - "{{ orchestrator_log_dir }}/workers"
    - "{{ orchestrator_log_dir }}/lightrag"
  become: yes
  tags: [directories]

- name: Verify directory ownership
  ansible.builtin.stat:
    path: "{{ orchestrator_app_dir }}"
  register: app_dir_stat
  failed_when: app_dir_stat.stat.pw_name != orchestrator_service_user
  tags: [directories, validation]
```

---

## tasks/04-python-setup.yml

```yaml
---
# Python virtual environment setup
- name: Ensure Python 3.12 is default
  ansible.builtin.alternatives:
    name: python3
    path: /usr/bin/python3.12
  become: yes
  tags: [python]

- name: Upgrade pip for Python 3.12
  ansible.builtin.pip:
    name: pip
    state: latest
    executable: pip3.12
  become: yes
  tags: [python]

- name: Create Python virtual environment
  ansible.builtin.command: "python3.12 -m venv {{ orchestrator_venv_dir }}"
  args:
    creates: "{{ orchestrator_venv_dir }}/bin/activate"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  tags: [python]

- name: Upgrade pip in virtual environment
  ansible.builtin.pip:
    name:
      - pip
      - setuptools
      - wheel
    state: latest
    virtualenv: "{{ orchestrator_venv_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  tags: [python]

- name: Install uv package manager
  ansible.builtin.pip:
    name: uv
    state: latest
    virtualenv: "{{ orchestrator_venv_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  tags: [python]

- name: Verify virtual environment
  ansible.builtin.stat:
    path: "{{ orchestrator_venv_dir }}/bin/python"
  register: venv_python
  failed_when: not venv_python.stat.exists
  tags: [python, validation]

- name: Display virtual environment info
  ansible.builtin.command: "{{ orchestrator_venv_dir }}/bin/python --version"
  register: venv_python_version
  changed_when: false
  tags: [python, validation]

- name: Show virtual environment Python version
  ansible.builtin.debug:
    msg: "Virtual environment Python: {{ venv_python_version.stdout }}"
  tags: [python]
```

---

## tasks/05-validation.yml

```yaml
---
# Validation tasks
- name: Verify service user exists
  ansible.builtin.getent:
    database: passwd
    key: "{{ orchestrator_service_user }}"
  register: orchestrator_user_check
  failed_when: orchestrator_user_check.ansible_facts.getent_passwd[orchestrator_service_user] is undefined
  tags: [validation]

- name: Verify all critical directories exist
  ansible.builtin.stat:
    path: "{{ item }}"
  register: dir_check
  failed_when: not dir_check.stat.exists or not dir_check.stat.isdir
  loop:
    - "{{ orchestrator_app_dir }}"
    - "{{ orchestrator_venv_dir }}"
    - "{{ orchestrator_data_dir }}"
    - "{{ lightrag_working_dir }}"
    - "{{ orchestrator_log_dir }}"
  tags: [validation]

- name: Verify Python 3.12 in virtual environment
  ansible.builtin.command: "{{ orchestrator_venv_dir }}/bin/python --version"
  register: venv_python_check
  changed_when: false
  failed_when: "'Python 3.12' not in venv_python_check.stdout"
  tags: [validation]

- name: Verify pip in virtual environment
  ansible.builtin.command: "{{ orchestrator_venv_dir }}/bin/pip --version"
  register: venv_pip_check
  changed_when: false
  failed_when: venv_pip_check.rc != 0
  tags: [validation]

- name: Display validation summary
  ansible.builtin.debug:
    msg:
      - "✅ Service user: {{ orchestrator_service_user }} (uid: {{ orchestrator_user_uid }})"
      - "✅ Application directory: {{ orchestrator_app_dir }}"
      - "✅ Virtual environment: {{ orchestrator_venv_dir }}"
      - "✅ Python version: {{ venv_python_check.stdout }}"
      - "✅ pip version: {{ venv_pip_check.stdout }}"
      - "✅ Base system setup complete!"
  tags: [validation]
```

---

## Playbook Integration

**File:** `playbooks/deploy-orchestrator-base.yml`

```yaml
---
- name: Deploy Orchestrator Base System
  hosts: hx-orchestrator-server
  become: yes
  gather_facts: yes
  
  roles:
    - base-setup              # Existing role (if needed)
    - ca_trust               # HX Root CA installation
    - orchestrator_base_setup  # NEW ROLE
  
  tags:
    - orchestrator
    - base
    - foundation
```

---

## Validation Commands

```bash
# Run deployment
ansible-playbook playbooks/deploy-orchestrator-base.yml \
  -i inventory/prod.ini \
  -l hx-orchestrator-server \
  --check --diff

# Execute deployment
ansible-playbook playbooks/deploy-orchestrator-base.yml \
  -i inventory/prod.ini \
  -l hx-orchestrator-server

# Verify on server
ssh agent0@192.168.10.8 "
  # Check user
  id orchestrator
  
  # Check directories
  ls -la /opt/hx-citadel-shield/
  ls -la /opt/hx-citadel-shield/orchestrator/
  
  # Check Python
  /opt/hx-citadel-shield/orchestrator-venv/bin/python --version
  /opt/hx-citadel-shield/orchestrator-venv/bin/pip list
"
```

---

## Enhanced Features (Production Improvements)

The base-setup role has been enhanced with additional production-ready features:

### 1. Log Rotation (Task: 06-logrotate.yml)

**Purpose:** Automatic log file management to prevent disk space issues

**Variables:**

```yaml
logrotate_enabled: true              # Enable/disable logrotate
logrotate_retention_days: 30         # Days to keep logs
logrotate_rotation_size: "100M"      # Size threshold for rotation
```

**Features:**

- Daily log rotation with compression
- Separate retention for error logs (60 days)
- Post-rotation service reload hooks
- Syntax validation during deployment

### 2. Sudo Configuration (Task: 07-sudo.yml)

**Purpose:** Passwordless service management for service user

**Variables:**

```yaml
sudo_enabled: true                   # Enable/disable sudo config
```

**Features:**

- Service start/stop/restart/reload permissions
- Journal log viewing capabilities
- Service status checking
- Validated sudoers configuration

### 3. Convenience Scripts (Task: 08-convenience-scripts.yml)

**Purpose:** Developer experience enhancements

**Variables:**

```yaml
convenience_scripts_enabled: true    # Enable/disable convenience features
```

**Features:**

- Shell aliases (shield-activate, shield-logs, shield-status, etc.)
- Environment variables ($SHIELD_HOME, $SHIELD_LOGS)
- Quick activation script (`activate-shield.sh`)
- Service management menu (`manage-services.sh`)
- Auto-completion friendly navigation

### 4. Health Check Script (Task: 09-health-check.yml)

**Purpose:** Automated system health monitoring

**Variables:**

```yaml
health_check_enabled: true           # Enable/disable health checks
health_check_cron_enabled: false     # Enable cron-based automation
health_check_disk_threshold: 80      # Disk usage warning (%)
health_check_memory_threshold: 85    # Memory usage warning (%)
health_check_cpu_threshold: 90       # CPU usage warning (%)
```

**Features:**

- Comprehensive system checks (disk, memory, CPU, network)
- Service status monitoring
- Directory and Python environment validation
- Color-coded output with status codes
- Optional cron-based automation (every 15 minutes)

**Usage:**

```bash
# Manual execution
{{ app_dir }}/scripts/health-check.sh

# Cron mode (automated)
{{ app_dir }}/scripts/health-check.sh --cron
```


---

## Success Criteria

```yaml
✅ Infrastructure:
   • Service user created (orchestrator:orchestrator)
   • Home directory: /home/orchestrator
   • UID/GID: 1001/1001

✅ Directories:
   • Application: /opt/hx-citadel-shield/orchestrator
   • Virtual environment: /opt/hx-citadel-shield/orchestrator-venv
   • Data: /opt/hx-citadel-shield/data
   • LightRAG: /opt/hx-citadel-shield/data/lightrag
   • Logs: /var/log/hx-citadel/orchestrator

✅ Python:
   • Python 3.12.3 installed
   • Virtual environment created
   • pip upgraded to latest
   • uv package manager installed

✅ Permissions:
   • All directories owned by orchestrator:orchestrator
   • Proper modes (0755 for app, 0750 for data)
   • Service user can write to all required paths

✅ Enhanced Features:
   • Logrotate configured for log management
   • Sudo permissions for service management
   • Convenience scripts and aliases installed
   • Health check monitoring deployed
   • All optional features validated
```

---

## Timeline

**Estimated Time:** 2-3 hours

```yaml
Task Breakdown:
  • System packages: 30 minutes
  • Service user creation: 15 minutes
  • Directory creation: 15 minutes
  • Python environment: 30 minutes
  • Validation: 15 minutes
  • Buffer: 45 minutes

Total: 2.5 hours
```

---

## Next Component

**After base system setup is complete, proceed to:**

→ **Component 2: FastAPI Framework** (`02-fastapi-framework-plan.md`)

---

**Base System Setup Plan Complete!** ✅
**Ready for Ansible deployment!** 🚀

