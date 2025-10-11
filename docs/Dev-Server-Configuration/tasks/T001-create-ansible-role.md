# Task T001: Create Ansible Role Structure

**Feature**: Shield AG-UI Deployment  
**Phase**: 3.1 Setup  
**Parallel**: No  
**Estimated Effort**: 1 hour  
**Prerequisites**: None (first task)

## Task Description

Create the complete Ansible role structure for deploying the Shield AG-UI application to hx-dev-server (192.168.10.12).

## Execution Flow

```
1. Create role directory structure
   → roles/ag_ui_deployment/
   → defaults/, tasks/, templates/, files/, handlers/
2. Create main task file structure
   → tasks/main.yml (orchestrator)
   → tasks/01-prerequisites.yml
   → tasks/02-user-setup.yml
   → tasks/03-directories.yml
   → tasks/04-frontend-build.yml
   → tasks/05-backend-setup.yml
   → tasks/06-docker-compose.yml
   → tasks/07-nginx-config.yml
   → tasks/08-service-start.yml
3. Create defaults/main.yml with variables
4. Create README.md for role documentation
5. Verify structure matches Ansible best practices
```

## Files to Create

### 1. Role Directory Structure
```
roles/ag_ui_deployment/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-prerequisites.yml
│   ├── 02-user-setup.yml
│   ├── 03-directories.yml
│   ├── 04-frontend-build.yml
│   ├── 05-backend-setup.yml
│   ├── 06-docker-compose.yml
│   ├── 07-nginx-config.yml
│   └── 08-service-start.yml
├── templates/
│   ├── docker-compose.yml.j2
│   ├── nginx.conf.j2
│   ├── backend.Dockerfile.j2
│   └── frontend.Dockerfile.j2
├── files/
├── handlers/
│   └── main.yml
└── README.md
```

### 2. defaults/main.yml

```yaml
---
# Shield AG-UI Deployment Variables

# Target server
ag_ui_user: "agui"
ag_ui_group: "agui"
ag_ui_home: "/opt/ag-ui"

# Application configuration
ag_ui_app_name: "shield-ag-ui"
ag_ui_frontend_port: 3001
ag_ui_backend_port: 8002
ag_ui_nginx_http_port: 80
ag_ui_nginx_https_port: 443

# Docker configuration
ag_ui_docker_network: "ag-ui-network"
ag_ui_frontend_image: "shield-ag-ui-frontend"
ag_ui_backend_image: "shield-ag-ui-backend"
ag_ui_nginx_image: "nginx:alpine"

# External service URLs (FQDNs)
ag_ui_litellm_url: "http://{{ hostvars[groups['llm_gateway_nodes'][0]]['ansible_host'] }}:4000"
ag_ui_orchestrator_url: "http://{{ hostvars[groups['orchestrator_nodes'][0]]['ansible_host'] }}:8000"
ag_ui_redis_url: "redis://{{ hostvars[groups['database_nodes'][0]]['ansible_host'] }}:6379"
ag_ui_qdrant_url: "http://{{ hostvars[groups['vectordb_nodes'][0]]['ansible_host'] }}:6333"

# Redis Streams configuration
ag_ui_redis_stream_name: "shield:events"
ag_ui_redis_consumer_group: "ag-ui-clients"
ag_ui_redis_consumer_name: "{{ ansible_hostname }}"

# Authentication configuration
ag_ui_jwt_secret: "{{ lookup('password', '/dev/null length=64 chars=ascii_letters,digits') }}"
ag_ui_session_timeout: 1800  # 30 minutes in seconds

# Monitoring
ag_ui_health_check_interval: "30s"
ag_ui_health_check_timeout: "10s"
ag_ui_health_check_retries: 3
```

### 3. tasks/main.yml

```yaml
---
# Main task orchestrator for Shield AG-UI deployment

- name: Display deployment information
  ansible.builtin.debug:
    msg: |
      ╔════════════════════════════════════════════════════════════╗
      ║        Shield AG-UI Deployment Starting                    ║
      ╠════════════════════════════════════════════════════════════╣
      ║  Target: {{ ansible_hostname }} ({{ ansible_host }})
      ║  Frontend Port: {{ ag_ui_frontend_port }}
      ║  Backend Port: {{ ag_ui_backend_port }}
      ║  Nginx HTTP: {{ ag_ui_nginx_http_port }}
      ║  LiteLLM: {{ ag_ui_litellm_url }}
      ║  Orchestrator: {{ ag_ui_orchestrator_url }}
      ║  Redis: {{ ag_ui_redis_url }}
      ╚════════════════════════════════════════════════════════════╝

- name: Phase 1 - Prerequisites
  ansible.builtin.include_tasks: 01-prerequisites.yml
  tags: [prerequisites, setup]

- name: Phase 2 - User Setup
  ansible.builtin.include_tasks: 02-user-setup.yml
  tags: [user, setup]

- name: Phase 3 - Directories
  ansible.builtin.include_tasks: 03-directories.yml
  tags: [directories, setup]

- name: Phase 4 - Frontend Build
  ansible.builtin.include_tasks: 04-frontend-build.yml
  tags: [frontend, build]

- name: Phase 5 - Backend Setup
  ansible.builtin.include_tasks: 05-backend-setup.yml
  tags: [backend, build]

- name: Phase 6 - Docker Compose
  ansible.builtin.include_tasks: 06-docker-compose.yml
  tags: [docker, deployment]

- name: Phase 7 - Nginx Configuration
  ansible.builtin.include_tasks: 07-nginx-config.yml
  tags: [nginx, deployment]

- name: Phase 8 - Service Start
  ansible.builtin.include_tasks: 08-service-start.yml
  tags: [service, deployment]

- name: Display deployment success
  ansible.builtin.debug:
    msg: |
      ╔════════════════════════════════════════════════════════════╗
      ║        Shield AG-UI Deployment Complete! ✅                ║
      ╠════════════════════════════════════════════════════════════╣
      ║  Frontend: http://{{ ansible_host }}:{{ ag_ui_frontend_port }}
      ║  Backend: http://{{ ansible_host }}:{{ ag_ui_backend_port }}
      ║  Nginx: http://{{ ansible_host }}:{{ ag_ui_nginx_http_port }}
      ║  Access: http://{{ ansible_host }}/
      ╚════════════════════════════════════════════════════════════╝
```

### 4. README.md

```markdown
# Ansible Role: ag_ui_deployment

Deploy Shield AG-UI (power user interface) to dev-server using Docker.

## Requirements

- Ansible 2.12+
- Target server: Ubuntu 24.04
- Docker 24.x
- Docker Compose V2

## Role Variables

See `defaults/main.yml` for all available variables.

Key variables:
- `ag_ui_frontend_port`: Frontend application port (default: 3001)
- `ag_ui_backend_port`: Backend API port (default: 8002)
- `ag_ui_litellm_url`: LiteLLM gateway URL
- `ag_ui_orchestrator_url`: Orchestrator API URL
- `ag_ui_redis_url`: Redis Streams URL

## Dependencies

- Docker installed on target server
- Access to external services (LiteLLM, Orchestrator, Redis, Qdrant)

## Example Playbook

```yaml
- hosts: dev_servers
  roles:
    - role: ag_ui_deployment
      vars:
        ag_ui_frontend_port: 3001
        ag_ui_backend_port: 8002
```

## Tags

- `setup`: Run setup tasks only
- `build`: Run build tasks only
- `deployment`: Run deployment tasks only
- `prerequisites`, `user`, `directories`, `frontend`, `backend`, `docker`, `nginx`, `service`

## License

Proprietary

## Author

HX-Citadel Shield Team
```

## Acceptance Criteria

- [x] Role directory structure created
- [x] All task files created (8 task files)
- [x] defaults/main.yml with all variables
- [x] README.md documentation
- [x] handlers/main.yml created
- [x] Structure follows Ansible best practices
- [x] All file paths use FQDNs (no hardcoded IPs)

## Testing

```bash
# Verify role structure
ansible-galaxy role init --init-path roles/ ag_ui_deployment --offline
tree roles/ag_ui_deployment/

# Lint role
ansible-lint roles/ag_ui_deployment/

# Dry run
ansible-playbook playbooks/deploy-ag-ui.yml --check --diff
```

## Next Tasks

- T002: Implement prerequisites task file
- T003: Implement user setup task file
- T004: Implement directories task file

## Notes

- Use `ansible_host` for external service URLs (FQDN policy)
- All secrets should use Ansible Vault in production
- Default JWT secret is generated - override in production
- Docker network name: `ag-ui-network`

## Related Documents

- [Implementation Plan](../DEV-SERVER-AG-UI-IMPLEMENTATION-PLAN.md)
- [Architecture](../SHIELD-AG-UI-ARCHITECTURE.md)
- [Specification](../SHIELD-AG-UI-SPECIFICATION.md)

