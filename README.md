# HX-Citadel Ansible Project

## Overview

Modular Ansible deployment for 15-server AI fleet (Ubuntu 24.04, RAG pipeline). Control node: hx-devops-server.

## Prereqs (Run on Control Node)

- Ansible 9+ (`sudo apt install ansible`)
- SSH keys to all nodes (`ansible all -m ping`)
- Git clone: `git clone https://github.com/hanax-ai/hx-citadel-ansible.git && cd hx-citadel-ansible`
- Install Galaxy deps: `ansible-galaxy install -r requirements.yml`

## Structure

- `inventory/`: INI files for hosts/groups
- `group_vars/`: Shared vars (e.g., `all/main.yml` for commons)
- `host_vars/`: Per-host overrides
- `roles/`: Modular tasks (e.g., `base-setup`, `postgresql`)
- `playbooks/`: Independent deploys (e.g., `deploy-orchestrator.yml`)
- `site.yml`: Orchestrates all

## Usage

1. Dry-run: `ansible-playbook site.yml --check --diff --ask-vault-pass`
2. Tagged: `ansible-playbook playbooks/deploy-db.yml --limit hx-sqldb-server --tags db`
3. Vault: `ansible-vault encrypt group_vars/all/vault.yml` (store secrets like `orch_secret`, `db_password`)

## Verification

- Post-run: `ansible all -m setup | grep ansible_date_time`
- Health: `curl <http://hx-orchestrator-server:8000/health>`
- Models: `ansible llm_nodes -m shell -a "ollama list"`

Gaps Closed: Idempotent installs, env secrets, health endpoints, model syncs.
