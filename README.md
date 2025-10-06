# HX-Citadel Ansible Project

## Overview
Modular Ansible deployment for 15-server AI fleet (Ubuntu 24.04, RAG pipeline). Control node: hx-devops-server.

## Prereqs (Run on Control Node)
- Ansible 2.14+ (sudo apt install ansible)
- SSH keys to all nodes (ansible all -m ping)
- Git clone: git clone https://github.com/your-org/hx-citadel-ansible.git && cd hx-citadel-ansible

## Structure
- inventory/: INI files for hosts/groups
- group_vars/: Shared vars (e.g., all.yml for commons)
- host_vars/: Per-host overrides
- roles/: Modular tasks (e.g., base-setup, postgresql)
- playbooks/: Independent deploys (e.g., deploy-orchestrator.yml)
- site.yml: Orchestrates all

## Usage
1. Dry-run: ansible-playbook -i inventory/prod.ini site.yml --check --diff
2. Tagged: ansible-playbook -i inventory/prod.ini playbooks/deploy-db.yml --tags deps
3. Vault: ansible-vault create group_vars/all/vault.yml (for secrets)

## Verification
- Post-run: ansible all -m setup | grep ansible_date_time
- Health: curl http://hx-orchestrator-server:8000/health

Gaps Closed: Idempotent installs, env secrets, health endpoints, model syncs.
