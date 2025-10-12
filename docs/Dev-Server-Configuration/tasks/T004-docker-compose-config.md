# Task T004: Create Docker Compose Configuration

**Feature**: Shield AG-UI Deployment  
**Phase**: 3.4 Integration  
**Parallel**: No  
**Estimated Effort**: 2 hours  
**Prerequisites**: T001 (Ansible role), T002 (Backend), T003 (Frontend)

## Task Description

Create the Docker Compose configuration for orchestrating the 3-container AG-UI stack (frontend, backend, nginx) with proper networking, volumes, health checks, and environment variable management.

## Execution Flow

```
1. Create docker-compose.yml template
   → Define all 3 services (frontend, backend, nginx)
   → Configure networks
   → Configure volumes
   → Set environment variables
2. Create .env.template file
   → Document all required variables
   → Provide sensible defaults
3. Configure health checks
   → Frontend: HTTP GET /api/health
   → Backend: HTTP GET /health
   → Nginx: HTTP GET /
4. Set up depends_on with conditions
   → Nginx depends on frontend + backend
   → Frontend depends on backend
5. Configure restart policies
6. Verify configuration is production-ready
```

## Files to Create

### 1. roles/ag_ui_deployment/templates/docker-compose.yml.j2

```yaml
version: '3.8'

services:
  # Backend Service (FastAPI + Redis Consumer)
  backend:
    image: {{ ag_ui_backend_image }}:latest
    container_name: ag-ui-backend
    build:
      context: {{ ag_ui_home }}/backend
      dockerfile: Dockerfile
    ports:
      - "{{ ag_ui_backend_port }}:8002"
    environment:
      # Application
      APP_NAME: "shield-ag-ui-backend"
      ENV: "{{ ag_ui_env | default('production') }}"
      PORT: "8002"
      
      # External Services (FQDNs)
      LITELLM_URL: "{{ ag_ui_litellm_url }}"
      ORCHESTRATOR_URL: "{{ ag_ui_orchestrator_url }}"
      REDIS_URL: "{{ ag_ui_redis_url }}"
      QDRANT_URL: "{{ ag_ui_qdrant_url }}"
      
      # Redis Streams
      REDIS_STREAM_NAME: "{{ ag_ui_redis_stream_name }}"
      REDIS_CONSUMER_GROUP: "{{ ag_ui_redis_consumer_group }}"
      REDIS_CONSUMER_NAME: "{{ ag_ui_redis_consumer_name }}"
      
      # Authentication
      JWT_SECRET: "{{ ag_ui_jwt_secret }}"
      JWT_ALGORITHM: "HS256"
      ACCESS_TOKEN_EXPIRE_MINUTES: "{{ ag_ui_session_timeout // 60 }}"
      
      # Database
      DATABASE_URL: "postgresql://{{ ag_ui_db_user }}:{{ ag_ui_db_password }}@{{ hostvars[groups['database_nodes'][0]]['ansible_host'] }}:5432/{{ ag_ui_db_name }}"
      
      # LiteLLM API Key
      LITELLM_API_KEY: "{{ ag_ui_litellm_api_key }}"
      
      # CORS Origins
      CORS_ORIGINS: '["http://{{ ansible_host }}:{{ ag_ui_nginx_http_port }}", "http://{{ ansible_host }}:{{ ag_ui_frontend_port }}"]'
    volumes:
      - backend-data:/app/data
      - backend-logs:/app/logs
    networks:
      - ag-ui-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8002/health').raise_for_status()"]
      interval: {{ ag_ui_health_check_interval }}
      timeout: {{ ag_ui_health_check_timeout }}
      retries: {{ ag_ui_health_check_retries }}
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Frontend Service (Vite SPA - static)
  frontend:
    image: {{ ag_ui_frontend_image }}:latest
    container_name: ag-ui-frontend
    build:
      context: {{ ag_ui_home }}/frontend
      dockerfile: Dockerfile
    ports:
      - "{{ ag_ui_frontend_port }}:3001"
    environment:
      NODE_ENV: "production"
      PORT: "3001"
      NEXT_PUBLIC_BACKEND_URL: "http://backend:8002"
      NEXT_TELEMETRY_DISABLED: "1"
    volumes:
      - frontend-logs:/app/.next/logs
    networks:
      - ag-ui-network
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3001/api/health', (r) => {r.statusCode === 200 ? process.exit(0) : process.exit(1)})"]
      interval: {{ ag_ui_health_check_interval }}
      timeout: {{ ag_ui_health_check_timeout }}
      retries: {{ ag_ui_health_check_retries }}
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Nginx Reverse Proxy
  nginx:
    image: {{ ag_ui_nginx_image }}
    container_name: ag-ui-nginx
    ports:
      - "{{ ag_ui_nginx_http_port }}:80"
      - "{{ ag_ui_nginx_https_port }}:443"
    volumes:
      - {{ ag_ui_home }}/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - {{ ag_ui_home }}/nginx/ssl:/etc/nginx/ssl:ro
      - nginx-logs:/var/log/nginx
    networks:
      - ag-ui-network
    depends_on:
      frontend:
        condition: service_healthy
      backend:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/health"]
      interval: {{ ag_ui_health_check_interval }}
      timeout: {{ ag_ui_health_check_timeout }}
      retries: {{ ag_ui_health_check_retries }}
      start_period: 15s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  ag-ui-network:
    name: {{ ag_ui_docker_network }}
    driver: bridge

volumes:
  backend-data:
    name: ag-ui-backend-data
  backend-logs:
    name: ag-ui-backend-logs
  frontend-logs:
    name: ag-ui-frontend-logs
  nginx-logs:
    name: ag-ui-nginx-logs
```

### 2. roles/ag_ui_deployment/templates/.env.template.j2

```bash
# Shield AG-UI Environment Variables
# Generated: {{ ansible_date_time.iso8601 }}
# Server: {{ ansible_hostname }} ({{ ansible_host }})

# ==========================================
# Application Configuration
# ==========================================
APP_NAME=shield-ag-ui-backend
ENV=production

# ==========================================
# External Services (FQDNs)
# ==========================================
LITELLM_URL={{ ag_ui_litellm_url }}
ORCHESTRATOR_URL={{ ag_ui_orchestrator_url }}
REDIS_URL={{ ag_ui_redis_url }}
QDRANT_URL={{ ag_ui_qdrant_url }}

# ==========================================
# Redis Streams Configuration
# ==========================================
REDIS_STREAM_NAME={{ ag_ui_redis_stream_name }}
REDIS_CONSUMER_GROUP={{ ag_ui_redis_consumer_group }}
REDIS_CONSUMER_NAME={{ ag_ui_redis_consumer_name }}

# ==========================================
# Authentication & Security
# ==========================================
JWT_SECRET={{ ag_ui_jwt_secret }}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES={{ ag_ui_session_timeout // 60 }}
LITELLM_API_KEY={{ ag_ui_litellm_api_key }}

# ==========================================
# Database Configuration
# ==========================================
DATABASE_URL=postgresql://{{ ag_ui_db_user }}:{{ ag_ui_db_password }}@{{ hostvars[groups['database_nodes'][0]]['ansible_host'] }}:5432/{{ ag_ui_db_name }}

# ==========================================
# Frontend Configuration
# ==========================================
NEXT_PUBLIC_BACKEND_URL=http://{{ ansible_host }}:{{ ag_ui_backend_port }}
NEXT_TELEMETRY_DISABLED=1

# ==========================================
# Ports
# ==========================================
BACKEND_PORT={{ ag_ui_backend_port }}
FRONTEND_PORT={{ ag_ui_frontend_port }}
NGINX_HTTP_PORT={{ ag_ui_nginx_http_port }}
NGINX_HTTPS_PORT={{ ag_ui_nginx_https_port }}
```

### 3. Ansible Task: tasks/06-docker-compose.yml

```yaml
---
# Task: Deploy Docker Compose configuration

- name: Deploy Docker Compose configuration
  ansible.builtin.template:
    src: docker-compose.yml.j2
    dest: "{{ ag_ui_home }}/docker-compose.yml"
    owner: "{{ ag_ui_user }}"
    group: "{{ ag_ui_group }}"
    mode: '0644'
  tags: [docker, config]

- name: Deploy environment file
  ansible.builtin.template:
    src: .env.template.j2
    dest: "{{ ag_ui_home }}/.env"
    owner: "{{ ag_ui_user }}"
    group: "{{ ag_ui_group }}"
    mode: '0600'  # Sensitive file
  tags: [docker, config]
  no_log: true  # Don't log sensitive data

- name: Verify Docker Compose configuration
  ansible.builtin.command:
    cmd: docker compose config --quiet
    chdir: "{{ ag_ui_home }}"
  become: true
  become_user: "{{ ag_ui_user }}"
  changed_when: false
  tags: [docker, validate]

- name: Build Docker images
  ansible.builtin.command:
    cmd: docker compose build
    chdir: "{{ ag_ui_home }}"
  become: true
  become_user: "{{ ag_ui_user }}"
  register: docker_build
  changed_when: "'Building' in docker_build.stdout"
  tags: [docker, build]

- name: Display build summary
  ansible.builtin.debug:
    msg: |
      Docker images built successfully:
      - {{ ag_ui_backend_image }}:latest
      - {{ ag_ui_frontend_image }}:latest
      - {{ ag_ui_nginx_image }} (from Docker Hub)
  tags: [docker, build]
```

## Acceptance Criteria

- [x] docker-compose.yml template created
- [x] All 3 services defined (frontend, backend, nginx)
- [x] Docker network configured (bridge mode)
- [x] 4 volumes configured (backend-data, backend-logs, frontend-logs, nginx-logs)
- [x] Environment variables templated
- [x] .env.template created with documentation
- [x] Health checks configured for all services
- [x] depends_on with conditions (service_healthy)
- [x] Restart policies set (unless-stopped)
- [x] Logging configured (json-file driver, rotation)
- [x] FQDNs used (no hardcoded IPs)
- [x] Sensitive data protected (no_log, mode 0600)
- [x] Validation task (docker compose config)

## Testing

```bash
# Validate Docker Compose configuration
cd /opt/ag-ui/
docker compose config --quiet

# Build images
docker compose build

# Start services (detached)
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f nginx

# Test health checks
docker compose ps --format "{{.Service}}: {{.Status}}"

# Stop services
docker compose down

# Clean up (remove volumes)
docker compose down -v
```

## Service Dependencies

```
nginx
  ├── depends_on: frontend (healthy)
  └── depends_on: backend (healthy)

frontend
  └── depends_on: backend (healthy)

backend
  └── (no dependencies - starts first)
```

## Health Check Flow

```
1. Backend starts → health check every 30s
   → After 30s start_period, mark healthy if 3 consecutive successes
2. Frontend starts after backend healthy → health check every 30s
   → After 60s start_period, mark healthy if 3 consecutive successes
3. Nginx starts after frontend + backend healthy → health check every 30s
   → After 15s start_period, mark healthy if 3 consecutive successes
```

## Docker Network

```
ag-ui-network (bridge)
  ├── backend (172.20.0.2)
  ├── frontend (172.20.0.3)
  └── nginx (172.20.0.4)
```

## Volumes

- **backend-data**: Temporary data, job artifacts
- **backend-logs**: Application logs (JSON format)
- **frontend-logs**: Vite/nginx logs
- **nginx-logs**: Access and error logs

## Next Tasks

- T005: Implement Nginx Configuration
- T006: Create E2E Testing Suite
- T007: Implement Monitoring & Observability

## Notes

- Uses Docker Compose V2 (compose command, not docker-compose)
- Health checks with service_healthy condition ensure proper startup order
- All services restart automatically unless explicitly stopped
- Logs rotated automatically (10MB max, 3 files)
- Environment variables templated from Ansible (secure)
- Network name customizable via `ag_ui_docker_network` variable
- Volumes named for easy identification
- FQDNs used for all external service URLs

## Related Documents

- [Architecture - Deployment Architecture](../SHIELD-AG-UI-ARCHITECTURE.md#5-deployment-architecture)
- [Implementation Plan - Docker Configuration](../DEV-SERVER-AG-UI-IMPLEMENTATION-PLAN.md#63-docker-compose-configuration)

