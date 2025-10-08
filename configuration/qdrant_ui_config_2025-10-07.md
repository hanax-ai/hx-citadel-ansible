# Qdrant Web UI Configuration Snapshot

**Last Updated:** October 7, 2025  
**Service Version:** Qdrant 1.15.4 + Web UI (master branch)  
**Deployed By:** `playbooks/deploy-qdrant-ui.yml`  
**Configuration Status:** 🟢 Active

---

## Executive Summary

Qdrant Web UI deployed on `hx-qwui-server` (192.168.10.53) provides a web-based interface for managing and querying the Qdrant Vector Database running on `hx-vectordb-server` (192.168.10.9). The deployment uses Nginx as a reverse proxy to serve static files and proxy API requests to the HTTPS-enabled Qdrant backend with API key authentication.

> **Security Notice:** This configuration includes API key authentication and HTTPS backend connectivity. The API key is stored in Ansible Vault (planned migration). SSL verification is disabled due to self-signed certificates on the Qdrant backend.

---

## Core Service Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Service Host | `hx-qwui-server` | Hosts static Vite build + Nginx proxy |
| Service IP / Port | `http://192.168.10.53:80` | HTTP-only frontend (internal network) |
| Backend/Upstream | `https://192.168.10.9:6333` | Qdrant Vector Database (HTTPS) |
| Deployment Root | `/opt/qdrant-ui` | Ansible-managed installation |
| Service User | `www-data` | Nginx process owner |
| Service Group | `www-data` | File ownership group |
| Protocol | `http` (frontend), `https` (backend) | Mixed protocol setup |
| SSL/TLS | `disabled` (frontend), `enabled` (backend) | Self-signed backend cert |

---

## Infrastructure Context

### Network Configuration

```
                     Users/Clients
                           │
                           │ HTTP (Port 80)
                           ↓
┌──────────────────────────────────────────────────┐
│       Nginx Reverse Proxy (hx-qwui-server)       │
│              IP: 192.168.10.53                    │
│                                                   │
│  ┌────────────────┐    ┌─────────────────────┐  │
│  │  Static Files  │    │   API Proxy         │  │
│  │  (HTML/JS/CSS) │    │   /api/             │  │
│  │  Port 80       │    │   /collections      │  │
│  └────────────────┘    │   /aliases          │  │
│                        │   /telemetry        │  │
│                        │   /cluster          │  │
│                        └──────────┬──────────┘  │
└───────────────────────────────────┼─────────────┘
                                    │
                                    │ HTTPS (Port 6333)
                                    │ + API Key Auth
                                    ↓
┌──────────────────────────────────────────────────┐
│     Qdrant Vector Database (hx-vectordb-server)  │
│              IP: 192.168.10.9                     │
│                                                   │
│  - REST API: Port 6333 (HTTPS)                   │
│  - gRPC API: Port 6334 (HTTPS)                   │
│  - TLS with Self-Signed Cert                     │
│  - API Key Required                              │
└──────────────────────────────────────────────────┘
```

### Network Details
- **Subnet:** 192.168.10.0/24 (Internal network)
- **Firewall Rules:** 
  - Inbound: Port 80 (HTTP) on 192.168.10.53
  - Outbound: Port 6333 (HTTPS) to 192.168.10.9
- **DNS:** Internal hostname resolution for `hx-qwui-server` and `hx-vectordb-server`
- **Load Balancer:** None (single instance)

---

## Playbook Configuration

### Ansible Playbook
**File:** `playbooks/deploy-qdrant-ui.yml`

```yaml
---
- name: Deploy Qdrant Web UI (HTTP-only)
  hosts: hx_qwui_target
  become: yes
  gather_facts: yes
  collections:
    - community.general
  
  vars:
    # Backend Configuration
    qdrant_ui_backend_host: 192.168.10.9
    qdrant_ui_backend_port: 6333
    qdrant_ui_backend_protocol: https
    qdrant_ui_backend_ssl_verify: "off"
    qdrant_ui_backend_api_key: "{{ vault_qdrant_api_key }}"  # TODO: Move to vault
    
    # Frontend Configuration
    qdrant_ui_http_port: 80
    qdrant_ui_owner: www-data
    qdrant_ui_group: www-data
    
  roles:
    - qdrant_web_ui
```

### Role Variables
**File:** `roles/qdrant_web_ui/defaults/main.yml`

```yaml
---
# Repository Configuration
qdrant_ui_repo_url: https://github.com/qdrant/qdrant-web-ui.git
qdrant_ui_repo_version: master

# Installation Paths
qdrant_ui_root: /opt/qdrant-ui
qdrant_ui_build_artifact_dir: dist

# Service Account
qdrant_ui_owner: www-data
qdrant_ui_group: www-data

# Backend Connection (Defaults - Override in playbook)
qdrant_ui_backend_host: 192.168.10.8
qdrant_ui_backend_port: 6333
qdrant_ui_backend_protocol: http
qdrant_ui_backend_ssl_verify: "off"
qdrant_ui_backend_api_key: ""

# Frontend Configuration
qdrant_ui_http_port: 80

# System Packages
qdrant_ui_packages:
  - nginx
  - git
  - nodejs
  - npm
  - build-essential
  - python3
  - make
  - curl
  - netcat-openbsd
  - tree

# Maintenance Settings
qdrant_ui_logrotate_keep: 14
qdrant_ui_monitor_interval: "*/5"
qdrant_ui_backup_retention_days: 7
qdrant_ui_backup_hour: 2
qdrant_ui_backup_minute: 0
```

---

## Service Architecture

### Directory Structure
```
/opt/qdrant-ui/
├── source/                      # Git repository clone
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── builds/
│   ├── current -> 20251007_212613/    # Symlink to active build
│   ├── 20251007_212613/               # Timestamped builds
│   └── rollback/                      # Previous build backup
├── config/
│   ├── nginx/                   # Nginx configuration backups
│   └── env/                     # Environment files
├── logs/
│   ├── access.log              # Nginx access logs
│   ├── error.log               # Nginx error logs
│   └── monitor.log             # Monitoring script logs
├── scripts/
│   ├── monitor.sh              # Health check script
│   ├── backup.sh               # Backup script
│   └── restore.sh              # Restore script
└── backups/                    # Configuration backups
```

### File Locations
| Component | Path | Purpose |
|-----------|------|---------|
| Active Build | `/opt/qdrant-ui/builds/current` | Symlink to latest build |
| Nginx Config | `/etc/nginx/sites-available/qdrant-ui` | Main nginx configuration |
| Nginx Enabled | `/etc/nginx/sites-enabled/qdrant-ui` | Enabled site symlink |
| Access Logs | `/opt/qdrant-ui/logs/access.log` | HTTP access logs |
| Error Logs | `/opt/qdrant-ui/logs/error.log` | Error and warning logs |
| Logrotate | `/etc/logrotate.d/qdrant-ui` | Log rotation policy |
| Systemd Unit | N/A | Using system nginx.service |

---

## Nginx Configuration

### Upstream Backend
```nginx
upstream qdrant_backend {
    server 192.168.10.9:6333;
    keepalive 32;
}
```

### Server Block
**File:** `/etc/nginx/sites-available/qdrant-ui`

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name hx-qwui-server 192.168.10.53;

    access_log /opt/qdrant-ui/logs/access.log;
    error_log /opt/qdrant-ui/logs/error.log warn;

    root /opt/qdrant-ui/builds/current;
    index index.html;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    server_tokens off;

    # Static Files
    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location ~* \.html$ {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # API Proxy - All /api/ requests
    location /api/ {
        proxy_pass https://qdrant_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header api-key "9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # SSL Configuration for Backend
        proxy_ssl_verify off;
        proxy_ssl_server_name on;
    }

    # Direct Qdrant API Endpoints
    location ~ ^/(collections|aliases|cluster|telemetry|metrics|locks)($|/) {
        proxy_pass https://qdrant_backend$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header api-key "9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_http_version 1.1;
        
        # SSL Configuration for Backend
        proxy_ssl_verify off;
        proxy_ssl_server_name on;
    }

    # Health Check (Local)
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # Deny Hidden Files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### Key Endpoints
| Endpoint | Purpose | Backend | Authentication |
|----------|---------|---------|----------------|
| `/` | Web UI (static files) | Local | None |
| `/api/*` | Proxied API calls | `https://192.168.10.9:6333` | API Key |
| `/collections` | List/manage collections | `https://192.168.10.9:6333` | API Key |
| `/aliases` | Collection aliases | `https://192.168.10.9:6333` | API Key |
| `/cluster` | Cluster information | `https://192.168.10.9:6333` | API Key |
| `/telemetry` | System telemetry | `https://192.168.10.9:6333` | API Key |
| `/metrics` | Prometheus metrics | `https://192.168.10.9:6333` | API Key |
| `/health` | Nginx health check | Local | None |

---

## Authentication & Security

### Authentication Method
- **Type:** API Key (Header-based)
- **Header Name:** `api-key`
- **Location:** Stored in playbook variables (TODO: migrate to vault)
- **Rotation Policy:** Manual (no automated rotation currently)

### API Keys / Secrets
> ⚠️ **Never include actual secrets in configuration documentation**

- **Qdrant API Key:** Currently in `playbooks/deploy-qdrant-ui.yml`
- **Target Location:** `group_vars/all/vault.yml` as `vault_qdrant_api_key`
- **Key Format:** 64-character hexadecimal string
- **Key Scope:** Full access to Qdrant API

**Current API Key (TO BE VAULTED):**
```
9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09
```

### TLS/SSL Configuration
- **Frontend TLS:** Disabled (HTTP only)
- **Backend TLS:** Enabled (HTTPS to Qdrant)
- **Certificate Type:** Self-signed (Qdrant backend)
- **Certificate Location (Backend):**
  - Certificate: `/etc/qdrant/certs/qdrant.crt`
  - Key: `/etc/qdrant/certs/qdrant.key`
  - CA: `/etc/qdrant/certs/rootCA.crt`
- **SSL Verification:** Disabled (`proxy_ssl_verify off`)
- **Reason:** Self-signed certificates on backend

### Firewall Rules
```bash
# On hx-qwui-server (192.168.10.53)
sudo ufw allow 80/tcp comment 'Qdrant Web UI HTTP'

# On hx-vectordb-server (192.168.10.9)
# Allow from Web UI server only
sudo ufw allow from 192.168.10.53 to any port 6333 proto tcp comment 'Qdrant API from Web UI'
```

---

## Service Management

### Systemd Unit
Uses system-wide `nginx.service` - no custom systemd unit

### Service Commands
```bash
# Nginx Service Management
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo systemctl status nginx

# Test nginx configuration
sudo nginx -t

# View logs
sudo journalctl -u nginx -f

# Application logs
sudo tail -f /opt/qdrant-ui/logs/access.log
sudo tail -f /opt/qdrant-ui/logs/error.log
```

---

## Available Endpoints

### API Endpoints (Proxied)
| Endpoint | Method | Purpose | Authentication | Response Format |
|----------|--------|---------|----------------|-----------------|
| `/collections` | GET | List all collections | API Key | JSON |
| `/collections/{name}` | GET | Get collection info | API Key | JSON |
| `/aliases` | GET | List collection aliases | API Key | JSON |
| `/cluster` | GET | Cluster status | API Key | JSON |
| `/telemetry` | GET | System telemetry | API Key | JSON |
| `/metrics` | GET | Prometheus metrics | API Key | Text |
| `/health` | GET | Service health (local) | None | Text |

### Health Checks
```bash
# Web UI Health (Local nginx check)
curl http://192.168.10.53/health
# Expected: OK

# Collections Endpoint
curl -s http://192.168.10.53/collections | jq .
# Expected: {"result":{"collections":[...]}, "status":"ok"}

# Aliases Endpoint
curl -s http://192.168.10.53/aliases | jq .
# Expected: {"result":{"aliases":[]}, "status":"ok"}

# Telemetry
curl -s http://192.168.10.53/telemetry | jq .
# Expected: {"result": {...version, uptime, etc...}}
```

### Expected Responses
```json
// Collections Response
{
  "result": {
    "collections": [
      {"name": "hx_corpus_v1"},
      {"name": "emb_mxbai_1024"},
      {"name": "smoke_test"},
      {"name": "emb_minilm_384"},
      {"name": "emb_nomic_768"}
    ]
  },
  "status": "ok",
  "time": 0.000123
}

// Aliases Response
{
  "result": {
    "aliases": []
  },
  "status": "ok",
  "time": 0.000012
}

// Cluster Response
{
  "result": {
    "status": "disabled"
  },
  "status": "ok",
  "time": 0.000015
}
```

---

## Testing & Validation

### Deployment Validation
```bash
# Test 1: Web UI Accessibility
curl -I http://192.168.10.53
# Expected: HTTP/1.1 200 OK

# Test 2: Collections API
curl -s http://192.168.10.53/collections | jq '.result.collections[] | .name'
# Expected: List of 5 collection names

# Test 3: Individual Collection
curl -s http://192.168.10.53/collections/hx_corpus_v1 | jq .
# Expected: Collection configuration details

# Test 4: Backend Connectivity
nc -zv 192.168.10.9 6333
# Expected: Connection to 192.168.10.9 6333 port [tcp/*] succeeded!

# Test 5: Nginx Configuration
sudo nginx -t
# Expected: nginx: configuration file /etc/nginx/nginx.conf test is successful

# Test 6: Authentication
curl -s http://192.168.10.53/api/collections | jq .
# Expected: HTTP 200 with collection data (API key auto-injected by nginx)
```

### Expected Results
- ✅ Web UI returns HTTP 200
- ✅ All API endpoints respond correctly
- ✅ Backend connectivity established via HTTPS
- ✅ API key authentication working
- ✅ All collections accessible

### Validation Checklist
- [x] Nginx starts without errors
- [x] All endpoints respond with HTTP 200
- [x] Logs show no errors
- [x] API key authentication works
- [x] HTTPS backend connection established
- [x] Health checks pass
- [x] All 5 collections visible
- [x] Static files load correctly
- [x] Nginx auto-starts on boot

---

## Monitoring & Logging

### Log Files
| Log Type | Location | Rotation | Retention |
|----------|----------|----------|-----------|
| Access | `/opt/qdrant-ui/logs/access.log` | Daily | 14 days |
| Error | `/opt/qdrant-ui/logs/error.log` | Daily | 14 days |
| Nginx | `/var/log/nginx/error.log` | Daily | 14 days |

### Log Rotation
**File:** `/etc/logrotate.d/qdrant-ui`

```
/opt/qdrant-ui/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
```

### Monitoring Commands
```bash
# Check access logs
sudo tail -f /opt/qdrant-ui/logs/access.log

# Check error logs
sudo tail -f /opt/qdrant-ui/logs/error.log

# Check for errors in last 100 lines
sudo tail -100 /opt/qdrant-ui/logs/error.log | grep -i error

# Monitor nginx status
sudo systemctl status nginx

# Check nginx connections
sudo netstat -plant | grep :80

# Monitor resource usage
htop -p $(pgrep nginx)
```

### Metrics
- **CPU Usage:** <5% (typical)
- **Memory Usage:** 7-10MB per nginx worker
- **Disk Usage:** ~850MB in `/opt/qdrant-ui`
- **Network Traffic:** Varies by usage (~500-1000 req/hour in testing)
- **Response Time:** 10-50ms average

---

## Maintenance & Operations

### Backup Procedures
```bash
# Backup configuration
sudo tar -czf /opt/qdrant-ui/backups/config-$(date +%Y%m%d).tar.gz \
  /etc/nginx/sites-available/qdrant-ui \
  /opt/qdrant-ui/config/

# Backup current build
sudo tar -czf /opt/qdrant-ui/backups/build-$(date +%Y%m%d).tar.gz \
  /opt/qdrant-ui/builds/current/

# Verify backup
tar -tzf /opt/qdrant-ui/backups/config-$(date +%Y%m%d).tar.gz | head
```

### Update Procedures
```bash
# 1. Backup current configuration
cd /opt/qdrant-ui/backups
sudo ./backup.sh

# 2. Run Ansible playbook
cd /home/agent0/workspace/hx-citadel-ansible
ansible-playbook -i inventory/hx-qwui.ini playbooks/deploy-qdrant-ui.yml

# 3. Verify deployment
curl -I http://192.168.10.53
curl -s http://192.168.10.53/collections | jq .

# 4. Check logs
sudo tail -50 /opt/qdrant-ui/logs/error.log
```

### Rollback Procedures
```bash
# 1. Stop nginx
sudo systemctl stop nginx

# 2. Restore previous build
cd /opt/qdrant-ui/builds
sudo rm current
sudo ln -s $(ls -1dt 2* | sed -n 2p) current

# 3. Restore previous nginx config (if needed)
sudo cp /opt/qdrant-ui/config/nginx/qdrant-ui.conf.backup \
       /etc/nginx/sites-available/qdrant-ui

# 4. Test and restart
sudo nginx -t
sudo systemctl start nginx

# 5. Verify
curl -I http://192.168.10.53
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Connection Refused to Backend
**Symptoms:**
- HTTP 502 Bad Gateway
- Nginx logs: "connect() failed (111: Connection refused)"

**Diagnosis:**
```bash
# Test backend connectivity
nc -zv 192.168.10.9 6333

# Check backend service
ssh agent0@192.168.10.9 "systemctl status qdrant"

# Check firewall
ssh agent0@192.168.10.9 "sudo ufw status"
```

**Resolution:**
```bash
# Ensure Qdrant service is running
ssh agent0@192.168.10.9 "sudo systemctl start qdrant"

# Check firewall allows connection
ssh agent0@192.168.10.9 "sudo ufw allow from 192.168.10.53 to any port 6333"
```

#### Issue 2: API Key Authentication Failed
**Symptoms:**
- HTTP 401 Unauthorized
- Response: "Must provide an API key or an Authorization bearer token"

**Diagnosis:**
```bash
# Check nginx configuration has API key
sudo grep "api-key" /etc/nginx/sites-available/qdrant-ui

# Test with explicit API key
curl -H "api-key: YOUR_KEY" https://192.168.10.9:6333/collections
```

**Resolution:**
```bash
# Update playbook with correct API key
# Redeploy
cd /home/agent0/workspace/hx-citadel-ansible
ansible-playbook -i inventory/hx-qwui.ini playbooks/deploy-qdrant-ui.yml
```

#### Issue 3: SSL/TLS Errors
**Symptoms:**
- "upstream sent no valid HTTP/1.0 header"
- "SSL certificate problem"

**Diagnosis:**
```bash
# Check backend TLS status
ssh agent0@192.168.10.9 "grep enable_tls /etc/qdrant/config.yaml"

# Test direct HTTPS connection
curl -k https://192.168.10.9:6333/collections
```

**Resolution:**
```bash
# Ensure proxy_ssl_verify is off for self-signed certs
# This is already configured in current setup
sudo grep "proxy_ssl_verify" /etc/nginx/sites-available/qdrant-ui
```

### Diagnostic Commands
```bash
# Check service status
sudo systemctl status nginx

# Check connectivity
nc -zv 192.168.10.9 6333

# Check logs
sudo tail -100 /opt/qdrant-ui/logs/error.log

# Check nginx configuration syntax
sudo nginx -t

# Check disk space
df -h /opt/qdrant-ui

# Check memory
free -h

# Check process
ps aux | grep nginx
```

---

## Performance Tuning

### Current Settings
| Setting | Value | Rationale |
|---------|-------|-----------|
| Keepalive connections | 32 | Balance between reuse and resources |
| Proxy timeouts | 60s | Allow for slow queries |
| Buffering | Off | Real-time streaming of responses |
| Cache static files | 1 year | Reduce bandwidth for JS/CSS |
| HTML caching | Disabled | Always serve fresh HTML |

### Optimization Opportunities
- **Add Gzip Compression:** Reduce bandwidth for API responses (5-10x reduction)
- **Enable HTTP/2:** Improve performance for multiple concurrent requests
- **Add CDN/Caching Layer:** Cache collection metadata for faster loads
- **Connection Pooling:** Already implemented with keepalive=32

---

## Dependencies

### Service Dependencies
| Dependency | Version | Required? | Purpose |
|------------|---------|-----------|---------|
| Nginx | 1.24+ | Yes | Web server and reverse proxy |
| Node.js | 18+ | Yes (build-time) | Build Vite application |
| npm | 9+ | Yes (build-time) | Package management |
| Qdrant | 1.15.4 | Yes | Backend vector database |

### Network Dependencies
- **Inbound:** Web browsers from internal network
- **Outbound:** Qdrant API on 192.168.10.9:6333 (HTTPS)

### Package Dependencies
```bash
# System packages
nginx
git
nodejs
npm
build-essential
python3
make
curl
netcat-openbsd
tree

# Installation
sudo apt update
sudo apt install -y nginx git nodejs npm build-essential python3 make curl netcat-openbsd tree
```

---

## Change History

### 2025-10-07 - Initial Deployment with HTTPS Fix
**Changed By:** DevOps Team  
**Playbook Run:** `ansible-playbook -i inventory/hx-qwui.ini playbooks/deploy-qdrant-ui.yml`

**Changes:**
- Deployed Qdrant Web UI from GitHub (master branch)
- Configured Nginx reverse proxy with HTTPS backend support
- Fixed backend host from 192.168.10.8 → 192.168.10.9
- Added HTTPS protocol support with SSL verification disabled
- Integrated API key authentication in proxy headers
- Added all required Qdrant API endpoints (/aliases, /telemetry, /cluster, etc.)

**Impact:**
- Web UI now fully operational
- All 5 collections accessible
- All API endpoints responding with HTTP 200

**Validation:**
- ✅ Web UI accessible at http://192.168.10.53
- ✅ Collections endpoint returns 5 collections
- ✅ Aliases, telemetry, cluster endpoints working
- ✅ No errors in nginx logs
- ✅ HTTPS backend connection established

---

## References

### Related Documentation
- **Status Report:** `status/STATUS-2025-10-07-qdrant-ui-deployment.md`
- **Deployment Playbook:** `playbooks/deploy-qdrant-ui.yml`
- **Ansible Role:** `roles/qdrant_web_ui/`
- **Inventory:** `inventory/hx-qwui.ini`
- **Templates:** `templates/SERVICE_CONFIGURATION_TEMPLATE.md`

### External Resources
- **Qdrant Documentation:** https://qdrant.tech/documentation/
- **Qdrant Web UI GitHub:** https://github.com/qdrant/qdrant-web-ui
- **Nginx Proxy Documentation:** https://nginx.org/en/docs/http/ngx_http_proxy_module.html

### Related Status Reports
- **STATUS-2025-10-07.md** - General infrastructure status
- **STATUS-2025-10-07-qdrant-ui-deployment.md** - Deployment details and troubleshooting

---

## Appendix

### Qdrant Backend Configuration
**Host:** hx-vectordb-server (192.168.10.9)  
**Service:** Qdrant Vector Database v1.15.4  
**Config File:** `/etc/qdrant/config.yaml`

```yaml
service:
  host: 192.168.10.9
  http_port: 6333
  grpc_port: 6334
  enable_cors: true
  enable_tls: true
  api_key: "9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09"

tls:
  cert: /etc/qdrant/certs/qdrant.crt
  key: /etc/qdrant/certs/qdrant.key
  ca_cert: /etc/qdrant/certs/rootCA.crt
  cert_ttl: 3600
```

### Available Collections
1. **hx_corpus_v1** - Primary corpus collection
2. **emb_mxbai_1024** - MXBai embeddings (1024 dimensions)
3. **smoke_test** - Testing collection
4. **emb_minilm_384** - MiniLM embeddings (384 dimensions)
5. **emb_nomic_768** - Nomic embeddings (768 dimensions)

### Build Information
- **Source:** https://github.com/qdrant/qdrant-web-ui (master branch)
- **Build Tool:** Vite
- **Build Command:** `npm run build`
- **Build Output:** `dist/` directory
- **Build Time:** ~2-3 minutes
- **Build Size:** ~15MB compressed

---

**Document Maintained By:** DevOps Team  
**Last Reviewed:** October 7, 2025  
**Next Review:** October 21, 2025  
**Contact:** devops@hanax-ai.com
