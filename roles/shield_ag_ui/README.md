# Ansible Role: shield_ag_ui

Deploy Shield AG-UI (power user interface) to dev-server using Docker.

## Requirements

- Ansible 2.12+
- Target server: Ubuntu 24.04
- Docker 24.x
- Docker Compose V2

## Role Variables

See `defaults/main.yml` for all available variables.

Key variables:
- `shield_ag_ui_frontend_port`: Frontend application port (default: 3001)
- `shield_ag_ui_backend_port`: Backend API port (default: 8002)
- `shield_ag_ui_litellm_url`: LiteLLM gateway URL
- `shield_ag_ui_orchestrator_url`: Orchestrator API URL
- `shield_ag_ui_redis_url`: Redis Streams URL

## Dependencies

- Docker installed on target server
- Access to external services (LiteLLM, Orchestrator, Redis, Qdrant)

## Example Playbook

```yaml
- hosts: dev_servers
  roles:
    - role: shield_ag_ui
      vars:
        shield_ag_ui_frontend_port: 3001
        shield_ag_ui_backend_port: 8002
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
