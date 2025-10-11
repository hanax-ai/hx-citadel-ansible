# Task T005: Configure Nginx Reverse Proxy

**Feature**: Shield AG-UI Nginx Configuration  
**Phase**: 3.4 Integration  
**Parallel**: No  
**Estimated Effort**: 1 hour  
**Prerequisites**: T004 (Docker Compose configuration)

## Task Description

Configure Nginx as a reverse proxy for the AG-UI application, providing SSL termination, load balancing, static asset serving, and WebSocket/SSE support for real-time events.

## Execution Flow

```
1. Create Nginx configuration template
   → Upstream definitions (frontend, backend)
   → Server blocks (HTTP, HTTPS)
   → Location blocks (/, /api/*, /events)
   → SSL configuration
2. Configure SSL certificates
   → Self-signed for dev (Let's Encrypt for prod)
   → Strong cipher suites
   → HSTS headers
3. Configure WebSocket/SSE support
   → Disable buffering for /events
   → Connection upgrade headers
   → Timeouts
4. Add security headers
   → X-Frame-Options, X-Content-Type-Options
   → CSP (Content Security Policy)
   → CORS headers
5. Configure static asset caching
6. Add health check endpoint
7. Create Ansible task file
8. Verify configuration
```

## Files to Create

### 1. roles/ag_ui_deployment/templates/nginx.conf.j2

```nginx
# Shield AG-UI Nginx Configuration
# Generated: {{ ansible_date_time.iso8601 }}
# Server: {{ ansible_hostname }}

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml application/atom+xml image/svg+xml 
               text/x-component text/x-cross-domain-policy;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=general_limit:10m rate=1000r/s;

    # Upstream definitions
    upstream frontend {
        server frontend:3001 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream backend {
        server backend:8002 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # HTTP server (redirect to HTTPS)
    server {
        listen 80;
        server_name {{ ansible_host }} {{ ansible_hostname }};

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Redirect all HTTP to HTTPS
        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name {{ ansible_host }} {{ ansible_hostname }};

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: ws:;" always;

        # Backend API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }

        # Server-Sent Events (SSE) endpoint
        location /events {
            proxy_pass http://backend/events;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection '';
            
            # CRITICAL: Disable buffering for SSE
            proxy_buffering off;
            proxy_cache off;
            
            # Keep connection alive
            proxy_read_timeout 3600s;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            
            # Prevent timeouts
            chunked_transfer_encoding on;
            tcp_nodelay on;
        }

        # Auth endpoints
        location /auth/ {
            limit_req zone=api_limit burst=10 nodelay;
            
            proxy_pass http://backend/auth/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Admin endpoints
        location /admin/ {
            limit_req zone=api_limit burst=5 nodelay;
            
            proxy_pass http://backend/admin/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check (no rate limit)
        location /health {
            access_log off;
            proxy_pass http://backend/health;
            proxy_http_version 1.1;
        }

        # Frontend static assets with caching
        location /_next/static/ {
            proxy_pass http://frontend/_next/static/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            
            # Cache static assets for 1 year
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # Frontend application (default)
        location / {
            limit_req zone=general_limit burst=50 nodelay;
            
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Next.js timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
```

### 2. Ansible Task: tasks/07-nginx-config.yml

```yaml
---
# Task: Deploy Nginx configuration

- name: Create Nginx configuration directory
  ansible.builtin.file:
    path: "{{ ag_ui_home }}/nginx"
    state: directory
    owner: "{{ ag_ui_user }}"
    group: "{{ ag_ui_group }}"
    mode: '0755'
  tags: [nginx, config]

- name: Create SSL directory
  ansible.builtin.file:
    path: "{{ ag_ui_home }}/nginx/ssl"
    state: directory
    owner: "{{ ag_ui_user }}"
    group: "{{ ag_ui_group }}"
    mode: '0700'
  tags: [nginx, ssl]

- name: Generate self-signed SSL certificate (dev only)
  ansible.builtin.command:
    cmd: >
      openssl req -x509 -nodes -days 365 -newkey rsa:2048
      -keyout {{ ag_ui_home }}/nginx/ssl/key.pem
      -out {{ ag_ui_home }}/nginx/ssl/cert.pem
      -subj "/C=US/ST=State/L=City/O=HX-Citadel/CN={{ ansible_host }}"
    creates: "{{ ag_ui_home }}/nginx/ssl/cert.pem"
  when: ag_ui_env == "development"
  tags: [nginx, ssl]

- name: Set SSL certificate permissions
  ansible.builtin.file:
    path: "{{ item }}"
    owner: "{{ ag_ui_user }}"
    group: "{{ ag_ui_group }}"
    mode: '0600'
  loop:
    - "{{ ag_ui_home }}/nginx/ssl/key.pem"
    - "{{ ag_ui_home }}/nginx/ssl/cert.pem"
  when: ag_ui_env == "development"
  tags: [nginx, ssl]

- name: Deploy Nginx configuration
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: "{{ ag_ui_home }}/nginx/nginx.conf"
    owner: "{{ ag_ui_user }}"
    group: "{{ ag_ui_group }}"
    mode: '0644'
    validate: 'docker run --rm -v %s:/etc/nginx/nginx.conf:ro nginx:alpine nginx -t -c /etc/nginx/nginx.conf'
  tags: [nginx, config]

- name: Display Nginx configuration summary
  ansible.builtin.debug:
    msg: |
      Nginx configuration deployed:
      - HTTP port: {{ ag_ui_nginx_http_port }}
      - HTTPS port: {{ ag_ui_nginx_https_port }}
      - SSL: Self-signed (dev) / Let's Encrypt (prod)
      - Upstreams: frontend:3001, backend:8002
      - SSE support: Enabled (/events)
      - Rate limiting: 100 req/s (API), 1000 req/s (general)
  tags: [nginx, config]
```

### 3. SSL Certificate Management Script

```bash
#!/bin/bash
# generate-ssl-cert.sh
# Generate self-signed SSL certificate for development

set -euo pipefail

CERT_DIR="${1:-/opt/ag-ui/nginx/ssl}"
HOSTNAME="${2:-$(hostname)}"

mkdir -p "$CERT_DIR"

echo "Generating self-signed SSL certificate for $HOSTNAME..."

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -subj "/C=US/ST=State/L=City/O=HX-Citadel/CN=$HOSTNAME"

chmod 600 "$CERT_DIR/key.pem" "$CERT_DIR/cert.pem"

echo "SSL certificate generated successfully!"
echo "Certificate: $CERT_DIR/cert.pem"
echo "Private key: $CERT_DIR/key.pem"
echo "Valid for: 365 days"
```

## Acceptance Criteria

- [x] Nginx configuration template created
- [x] HTTP → HTTPS redirect configured
- [x] SSL/TLS configured (TLS 1.2+)
- [x] Strong cipher suites configured
- [x] Security headers added (HSTS, CSP, X-Frame-Options)
- [x] Rate limiting configured (100 req/s API, 1000 req/s general)
- [x] SSE endpoint configured with buffering disabled
- [x] Backend API proxying configured
- [x] Frontend static asset caching configured
- [x] Health check endpoint exposed
- [x] Ansible task file created
- [x] Configuration validation in Ansible
- [x] SSL certificate generation (dev)

## Testing

```bash
# Validate Nginx configuration
docker run --rm -v /opt/ag-ui/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx:alpine nginx -t -c /etc/nginx/nginx.conf

# Start Nginx container
cd /opt/ag-ui/
docker compose up -d nginx

# Test HTTP → HTTPS redirect
curl -I http://192.168.10.12/
# Should return 301 redirect to https://

# Test HTTPS
curl -k -I https://192.168.10.12/
# Should return 200 OK

# Test health check
curl http://192.168.10.12/health
# Should return "healthy"

# Test backend API proxy
curl -k https://192.168.10.12/api/health
# Should proxy to backend

# Test SSE endpoint
curl -k -N https://192.168.10.12/events
# Should maintain connection (SSE stream)

# Check SSL certificate
openssl s_client -connect 192.168.10.12:443 -showcerts

# Test rate limiting
for i in {1..110}; do curl -k https://192.168.10.12/api/health; done
# Should get 429 Too Many Requests after 100 requests
```

## Security Features

### SSL/TLS Configuration
- **Protocols**: TLS 1.2, TLS 1.3 only (no SSLv3, TLS 1.0, TLS 1.1)
- **Ciphers**: Strong ciphers only (ECDHE with AES-GCM)
- **HSTS**: Enabled (1 year, includeSubDomains)
- **Session Cache**: 10 minutes

### Security Headers
- **Strict-Transport-Security**: Force HTTPS for 1 year
- **X-Frame-Options**: SAMEORIGIN (prevent clickjacking)
- **X-Content-Type-Options**: nosniff (prevent MIME sniffing)
- **X-XSS-Protection**: 1; mode=block
- **Referrer-Policy**: strict-origin-when-cross-origin
- **Content-Security-Policy**: Restrict resource loading

### Rate Limiting
- **API endpoints**: 100 requests/second per IP (burst: 20)
- **General endpoints**: 1000 requests/second per IP (burst: 50)
- **Auth endpoints**: 100 requests/second per IP (burst: 10)
- **Admin endpoints**: 100 requests/second per IP (burst: 5)

## SSE Configuration Details

Critical settings for Server-Sent Events:
```nginx
proxy_buffering off;        # Disable response buffering
proxy_cache off;            # Disable caching
proxy_read_timeout 3600s;   # Keep connection for 1 hour
chunked_transfer_encoding on;  # Support chunked responses
```

## Production Considerations

### Let's Encrypt SSL (Production)
```yaml
# In defaults/main.yml
ag_ui_ssl_email: "admin@example.com"
ag_ui_use_letsencrypt: true

# Use certbot for production
- name: Install certbot
  apt:
    name: certbot
    state: present

- name: Obtain Let's Encrypt certificate
  command: >
    certbot certonly --standalone
    --non-interactive --agree-tos
    --email {{ ag_ui_ssl_email }}
    -d {{ ansible_host }}
  when: ag_ui_use_letsencrypt
```

### Certificate Renewal
```bash
# Cron job for certificate renewal
0 3 * * 0 certbot renew --quiet && docker compose restart nginx
```

## Next Tasks

- T006: Create Unit Tests for Backend Services
- T007: Create Integration Tests for API Endpoints
- T008: Create E2E Tests with Playwright
- T010: Implement Authentication Service

## Notes

- Self-signed certificate for dev (Let's Encrypt for prod)
- SSE requires buffering disabled (`proxy_buffering off`)
- Rate limiting prevents abuse (adjust limits as needed)
- HSTS enforces HTTPS for all future requests
- CSP restricts resource loading for security
- Static assets cached for 1 year (Next.js builds)
- Health check on `/health` (no authentication)
- Nginx validates config before applying (Ansible)

## Related Documents

- [Architecture - Deployment Architecture](../SHIELD-AG-UI-ARCHITECTURE.md#5-deployment-architecture)
- [Implementation Plan - Nginx Configuration](../DEV-SERVER-AG-UI-IMPLEMENTATION-PLAN.md#67-nginx-reverse-proxy)

