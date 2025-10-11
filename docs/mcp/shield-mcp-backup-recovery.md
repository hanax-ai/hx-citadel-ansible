# Shield MCP Server - Backup and Recovery Procedures

**Date:** 2025-01-07  
**Server:** hx-mcp1-server (192.168.10.59)  
**Service:** Shield MCP Server  
**RTO (Recovery Time Objective):** < 30 minutes  
**RPO (Recovery Point Objective):** < 24 hours

---

## Table of Contents

1. [Overview](#overview)
2. [Backup Strategy](#backup-strategy)
3. [What to Backup](#what-to-backup)
4. [Backup Procedures](#backup-procedures)
5. [Recovery Procedures](#recovery-procedures)
6. [Disaster Recovery Scenarios](#disaster-recovery-scenarios)
7. [Testing and Validation](#testing-and-validation)
8. [Automation](#automation)

---

## Overview

The Shield MCP Server requires backup of configuration, application code, environment settings, and Playwright browser installations. Since the server relies on external dependencies (Qdrant, Ollama, Orchestrator), those services have separate backup procedures.

### Backup Philosophy

- **Configuration as Code:** All configuration managed via Ansible (Git backup)
- **Stateless Application:** No application-specific data to backup
- **External Dependencies:** Qdrant vectors, Ollama models backed up separately
- **Fast Recovery:** Complete redeployment from Ansible in < 30 minutes

---

## Backup Strategy

### Tier 1: Git Repository (Primary)

**Frequency:** Continuous (every commit)  
**Location:** GitHub `hanax-ai/hx-citadel-ansible`  
**What:** Ansible playbooks, roles, templates, inventory

**Recovery Method:** Clone repository and redeploy

```bash
git clone https://github.com/hanax-ai/hx-citadel-ansible.git
ansible-playbook playbooks/deploy-base.yml playbooks/deploy-api.yml -i inventory/prod.ini --ask-vault-pass
```

### Tier 2: Daily Configuration Backup

**Frequency:** Daily at 02:00 UTC  
**Location:** hx-backup-server (192.168.10.200) `/backups/mcp-servers/`  
**Retention:** 30 days  
**What:** Configuration files, environment files, service definitions

### Tier 3: Weekly Full Backup

**Frequency:** Weekly (Sunday 03:00 UTC)  
**Location:** Off-site storage  
**Retention:** 12 weeks  
**What:** Complete server snapshot (optional)

---

## What to Backup

### Critical Files and Directories

#### 1. Application Directory

**Path:** `/opt/fastmcp/shield`

**Contents:**
- `shield_mcp_server.py` - Main server application
- `requirements-*.txt` - Python dependencies
- `.env` - Environment configuration
- `.playwright-browsers-installed` - Browser installation marker
- `logs/` - Application logs (optional)

#### 2. Virtual Environment (Recreatable)

**Path:** `/opt/fastmcp/shield/venv`

**Note:** Can be recreated from requirements.txt, backup optional

#### 3. Service Definition

**Path:** `/etc/systemd/system/shield-mcp-server.service`

**Contents:** Systemd service configuration

#### 4. Environment Configuration

**Path:** `/opt/fastmcp/shield/.env`

**Critical Variables:**
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `OLLAMA_BASE_URL`
- `ORCHESTRATOR_BASE_URL`
- `FASTMCP_PORT`

#### 5. Ansible Vault

**Path:** `group_vars/all/vault.yml` (in Git repo)

**Contents:**
- `vault_qdrant_api_key`
- Other encrypted variables

**Backup:** Stored in Git + encrypted vault backup

#### 6. Playwright Browsers

**Path:** `/home/fastmcp/.cache/ms-playwright/`

**Contents:**
- `chromium-*/` - Chromium browser
- `firefox-*/` - Firefox browser
- `webkit-*/` - WebKit browser (optional)

**Size:** ~500MB per browser

**Note:** Can be reinstalled via `playwright install`, backup optional for faster recovery

---

## Backup Procedures

### Manual Backup (Immediate)

```bash
# 1. Create backup directory
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/shield-mcp-backup-${BACKUP_DATE}"
mkdir -p "${BACKUP_DIR}"

# 2. Backup application directory
sudo tar -czf "${BACKUP_DIR}/fastmcp-app.tar.gz" \
  --exclude='venv' \
  --exclude='logs/*.log' \
  --exclude='__pycache__' \
  /opt/fastmcp/shield/

# 3. Backup service definition
sudo cp /etc/systemd/system/shield-mcp-server.service \
  "${BACKUP_DIR}/"

# 4. Backup environment file (encrypted)
sudo ansible-vault encrypt \
  --output="${BACKUP_DIR}/env.encrypted" \
  /opt/fastmcp/shield/.env

# 5. Backup Playwright browsers (optional)
sudo tar -czf "${BACKUP_DIR}/playwright-browsers.tar.gz" \
  /home/fastmcp/.cache/ms-playwright/

# 6. Create backup manifest
cat > "${BACKUP_DIR}/MANIFEST.txt" << EOF
Shield MCP Server Backup
========================
Date: ${BACKUP_DATE}
Server: $(hostname)
IP: $(hostname -I | awk '{print $1}')

Files Included:
- fastmcp-app.tar.gz (application code)
- shield-mcp-server.service (systemd service)
- env.encrypted (environment variables)
- playwright-browsers.tar.gz (browser binaries)

Python Version: $(python3 --version)
Service Status: $(systemctl is-active shield-mcp-server)

Recovery Commands:
  tar -xzf fastmcp-app.tar.gz -C /
  cp shield-mcp-server.service /etc/systemd/system/
  ansible-vault decrypt env.encrypted --output=/opt/fastmcp/shield/.env
  tar -xzf playwright-browsers.tar.gz -C /home/fastmcp/.cache/
EOF

# 7. Transfer to backup server
scp -r "${BACKUP_DIR}" hx-backup-server:/backups/mcp-servers/

# 8. Verify backup
ssh hx-backup-server "ls -lah /backups/mcp-servers/${BACKUP_DIR##*/}"
```

### Automated Daily Backup Script

**Path:** `/usr/local/bin/shield-mcp-backup.sh`

```bash
#!/bin/bash
# Shield MCP Server Automated Backup Script

set -euo pipefail

# Configuration
BACKUP_ROOT="/backups/local/shield-mcp"
BACKUP_SERVER="hx-backup-server"
BACKUP_REMOTE_PATH="/backups/mcp-servers"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d)
BACKUP_DIR="${BACKUP_ROOT}/${DATE}"

# Logging
LOG_FILE="/var/log/shield-mcp-backup.log"
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# Create backup directory
log "Starting backup to ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# 1. Backup application code (excluding venv)
log "Backing up application directory..."
tar -czf "${BACKUP_DIR}/fastmcp-app.tar.gz" \
  --exclude='venv' \
  --exclude='logs/*.log' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  /opt/fastmcp/shield/ 2>>"${LOG_FILE}"

# 2. Backup systemd service
log "Backing up systemd service..."
cp /etc/systemd/system/shield-mcp-server.service "${BACKUP_DIR}/"

# 3. Backup environment file (sensitive)
log "Backing up environment configuration..."
cp /opt/fastmcp/shield/.env "${BACKUP_DIR}/env.txt"
chmod 600 "${BACKUP_DIR}/env.txt"

# 4. Collect system information
log "Collecting system information..."
cat > "${BACKUP_DIR}/system-info.txt" << EOF
Hostname: $(hostname)
IP Address: $(hostname -I | awk '{print $1}')
Backup Date: $(date -Iseconds)
OS: $(lsb_release -d | cut -f2)
Python Version: $(python3 --version)
Service Status: $(systemctl is-active shield-mcp-server)
Service Enabled: $(systemctl is-enabled shield-mcp-server)

Disk Usage:
$(df -h /opt/fastmcp)

Installed Python Packages:
$(/opt/fastmcp/shield/venv/bin/pip freeze)
EOF

# 5. Create manifest
log "Creating backup manifest..."
cat > "${BACKUP_DIR}/MANIFEST.md" << EOF
# Shield MCP Backup Manifest

**Date:** $(date -Iseconds)
**Server:** $(hostname) ($(hostname -I | awk '{print $1}'))
**Backup ID:** ${DATE}

## Contents

| File | Size | Description |
|------|------|-------------|
| fastmcp-app.tar.gz | $(du -h "${BACKUP_DIR}/fastmcp-app.tar.gz" | cut -f1) | Application code and configs |
| shield-mcp-server.service | $(du -h "${BACKUP_DIR}/shield-mcp-server.service" | cut -f1) | Systemd service definition |
| env.txt | $(du -h "${BACKUP_DIR}/env.txt" | cut -f1) | Environment variables |
| system-info.txt | $(du -h "${BACKUP_DIR}/system-info.txt" | cut -f1) | System information |

## Recovery Command

\`\`\`bash
# On new/recovered server
cd /tmp
scp -r hx-backup-server:${BACKUP_REMOTE_PATH}/${DATE} .
cd ${DATE}
sudo tar -xzf fastmcp-app.tar.gz -C /
sudo cp shield-mcp-server.service /etc/systemd/system/
sudo cp env.txt /opt/fastmcp/shield/.env
sudo systemctl daemon-reload
sudo systemctl enable --now shield-mcp-server
\`\`\`
EOF

# 6. Calculate checksum
log "Calculating checksums..."
cd "${BACKUP_DIR}"
sha256sum * > checksums.sha256

# 7. Compress entire backup
log "Compressing backup..."
cd "${BACKUP_ROOT}"
tar -czf "${DATE}.tar.gz" "${DATE}/"

# 8. Transfer to backup server
log "Transferring to backup server..."
scp "${DATE}.tar.gz" "${BACKUP_SERVER}:${BACKUP_REMOTE_PATH}/" 2>>"${LOG_FILE}"

# 9. Verify remote backup
log "Verifying remote backup..."
ssh "${BACKUP_SERVER}" "ls -lh ${BACKUP_REMOTE_PATH}/${DATE}.tar.gz" 2>>"${LOG_FILE}"

# 10. Cleanup old local backups
log "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_ROOT}" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete

# 11. Cleanup old remote backups
log "Cleaning up remote backups..."
ssh "${BACKUP_SERVER}" "find ${BACKUP_REMOTE_PATH} -name '*.tar.gz' -mtime +${RETENTION_DAYS} -delete"

log "Backup completed successfully: ${DATE}.tar.gz"
```

### Cron Schedule

Add to `/etc/cron.d/shield-mcp-backup`:

```cron
# Shield MCP Server Daily Backup
# Runs at 02:00 UTC daily
0 2 * * * root /usr/local/bin/shield-mcp-backup.sh >> /var/log/shield-mcp-backup.log 2>&1
```

---

## Recovery Procedures

### Scenario 1: Configuration File Corruption

**Symptom:** Service fails to start due to bad config

**Recovery Time:** < 5 minutes

```bash
# 1. Stop service
sudo systemctl stop shield-mcp-server

# 2. Restore from latest backup
LATEST_BACKUP=$(ssh hx-backup-server "ls -t /backups/mcp-servers/*.tar.gz | head -1")
scp "hx-backup-server:${LATEST_BACKUP}" /tmp/

# 3. Extract configuration
cd /tmp
tar -xzf $(basename ${LATEST_BACKUP})
cd $(basename ${LATEST_BACKUP} .tar.gz)

# 4. Restore environment file
sudo cp env.txt /opt/fastmcp/shield/.env
sudo chown fastmcp:fastmcp /opt/fastmcp/shield/.env
sudo chmod 600 /opt/fastmcp/shield/.env

# 5. Restart service
sudo systemctl start shield-mcp-server
sudo systemctl status shield-mcp-server

# 6. Verify health
curl http://localhost:8081/health | jq .
```

### Scenario 2: Application Code Corruption

**Symptom:** Python errors, missing files

**Recovery Time:** < 10 minutes

```bash
# 1. Stop service
sudo systemctl stop shield-mcp-server

# 2. Backup current (corrupted) state
sudo mv /opt/fastmcp/shield /opt/fastmcp/shield.corrupted.$(date +%Y%m%d_%H%M%S)

# 3. Restore from backup
LATEST_BACKUP=$(ssh hx-backup-server "ls -t /backups/mcp-servers/*.tar.gz | head -1")
scp "hx-backup-server:${LATEST_BACKUP}" /tmp/
cd /tmp
tar -xzf $(basename ${LATEST_BACKUP})
cd $(basename ${LATEST_BACKUP} .tar.gz)

# 4. Extract application
sudo tar -xzf fastmcp-app.tar.gz -C /

# 5. Set permissions
sudo chown -R fastmcp:fastmcp /opt/fastmcp/shield
sudo chmod 755 /opt/fastmcp/shield
sudo chmod 600 /opt/fastmcp/shield/.env

# 6. Recreate virtual environment
cd /opt/fastmcp/shield
sudo -u fastmcp python3.12 -m venv venv
sudo -u fastmcp venv/bin/pip install --upgrade pip
sudo -u fastmcp venv/bin/pip install -r requirements-fastmcp.txt
sudo -u fastmcp venv/bin/pip install -r requirements-shield-tools.txt

# 7. Reinstall Playwright browsers
sudo -u fastmcp venv/bin/playwright install chromium firefox

# 8. Restart service
sudo systemctl daemon-reload
sudo systemctl start shield-mcp-server
sudo systemctl status shield-mcp-server

# 9. Verify health
curl http://localhost:8081/health | jq .
```

### Scenario 3: Complete Server Failure

**Symptom:** Server unresponsive, hardware failure

**Recovery Time:** < 30 minutes (new server)

```bash
# On new server (hx-mcp2-server or rebuilt hx-mcp1-server)

# 1. Clone Ansible repository
cd /tmp
git clone https://github.com/hanax-ai/hx-citadel-ansible.git
cd hx-citadel-ansible

# 2. Update inventory if needed
# If using new hostname, update inventory/prod.ini

# 3. Run base deployment
ansible-playbook playbooks/deploy-base.yml \
  -i inventory/prod.ini \
  -l hx-mcp1-server \
  --ask-vault-pass

# 4. Run MCP deployment
ansible-playbook playbooks/deploy-api.yml \
  -i inventory/prod.ini \
  -l hx-mcp1-server \
  --ask-vault-pass

# 5. Restore backed-up configuration (if needed)
# Pull latest backup from backup server
ssh hx-backup-server
LATEST=/backups/mcp-servers/$(ls -t *.tar.gz | head -1)
scp ${LATEST} hx-mcp1-server:/tmp/

# On hx-mcp1-server
cd /tmp
tar -xzf $(ls -t *.tar.gz | head -1)
cd $(basename $(ls -t *.tar.gz | head -1) .tar.gz)

# Compare and merge any custom configurations
diff env.txt /opt/fastmcp/shield/.env

# 6. Verify service
sudo systemctl status shield-mcp-server
curl http://localhost:8081/health | jq .

# 7. Update DNS/load balancer if needed
```

### Scenario 4: Ansible Playbook Recovery

**Symptom:** Lost Ansible repository, need to recreate

**Recovery Time:** < 5 minutes

```bash
# 1. Clone from GitHub (primary backup)
git clone https://github.com/hanax-ai/hx-citadel-ansible.git
cd hx-citadel-ansible

# 2. Verify vault password
echo "Major8859!" | ansible-vault view group_vars/all/vault.yml

# 3. Test playbook syntax
ansible-playbook playbooks/deploy-api.yml --syntax-check

# 4. Redeploy if needed
ansible-playbook playbooks/deploy-api.yml \
  -i inventory/prod.ini \
  -l hx-mcp1-server \
  --ask-vault-pass \
  --check  # Dry run first
```

---

## Disaster Recovery Scenarios

### DR Scenario Matrix

| Scenario | Impact | Recovery Time | Procedure |
|----------|--------|---------------|-----------|
| Config file corrupted | Service down | < 5 min | Restore from backup |
| App code corrupted | Service down | < 10 min | Extract from backup + restart |
| Virtual env corrupted | Service down | < 15 min | Recreate from requirements.txt |
| Playwright browsers missing | Tools fail | < 20 min | Reinstall via playwright |
| Systemd service missing | Service won't start | < 2 min | Copy from backup |
| Complete server loss | Service down | < 30 min | Redeploy via Ansible |
| Ansible repo lost | Cannot deploy | < 5 min | Clone from GitHub |
| Vault password lost | Cannot decrypt | Manual | Contact administrator |

### DR Testing Schedule

- **Monthly:** Test configuration restore (Scenario 1)
- **Quarterly:** Test full application restore (Scenario 2)
- **Semi-annually:** Test complete rebuild (Scenario 3)
- **Annually:** Test cross-region failover

---

## Testing and Validation

### Backup Validation Checklist

```bash
#!/bin/bash
# Backup Validation Script

BACKUP_DIR="/tmp/shield-mcp-backup-test"
LATEST_BACKUP=$(ssh hx-backup-server "ls -t /backups/mcp-servers/*.tar.gz | head -1")

echo "=== Shield MCP Backup Validation ==="
echo "Backup: ${LATEST_BACKUP}"

# 1. Download backup
echo "[1/7] Downloading backup..."
scp "hx-backup-server:${LATEST_BACKUP}" /tmp/
cd /tmp
tar -xzf $(basename ${LATEST_BACKUP})
cd $(basename ${LATEST_BACKUP} .tar.gz)

# 2. Verify checksums
echo "[2/7] Verifying checksums..."
sha256sum -c checksums.sha256 || exit 1

# 3. Check manifest exists
echo "[3/7] Checking manifest..."
[ -f MANIFEST.md ] || { echo "MANIFEST.md missing!"; exit 1; }

# 4. Verify application archive
echo "[4/7] Verifying application archive..."
tar -tzf fastmcp-app.tar.gz | grep -q "shield_mcp_server.py" || { echo "Main app file missing!"; exit 1; }

# 5. Verify service file
echo "[5/7] Verifying service definition..."
[ -f shield-mcp-server.service ] || { echo "Service file missing!"; exit 1; }
grep -q "ExecStart" shield-mcp-server.service || { echo "Invalid service file!"; exit 1; }

# 6. Verify environment file
echo "[6/7] Verifying environment file..."
[ -f env.txt ] || { echo "Environment file missing!"; exit 1; }
grep -q "QDRANT_URL" env.txt || { echo "Invalid environment file!"; exit 1; }

# 7. Verify system info
echo "[7/7] Verifying system information..."
[ -f system-info.txt ] || { echo "System info missing!"; exit 1; }

echo "✅ Backup validation PASSED"
echo "Backup contains all required files for recovery"
```

---

## Automation

### Ansible Recovery Playbook

Create `playbooks/recover-mcp-server.yml`:

```yaml
---
# Shield MCP Server Recovery Playbook
- name: Recover Shield MCP Server from backup
  hosts: mcp_servers
  become: yes
  vars:
    backup_source: "hx-backup-server:/backups/mcp-servers"
    recovery_mode: "{{ recovery_mode | default('configuration') }}"  # configuration, full, rebuild
  
  tasks:
    - name: Get latest backup filename
      ansible.builtin.shell: "ssh hx-backup-server 'ls -t /backups/mcp-servers/*.tar.gz | head -1'"
      register: latest_backup
      changed_when: false
      delegate_to: localhost

    - name: Display recovery information
      ansible.builtin.debug:
        msg: |
          Recovery Mode: {{ recovery_mode }}
          Latest Backup: {{ latest_backup.stdout }}
          Target Server: {{ ansible_hostname }}

    - name: Stop Shield MCP service
      ansible.builtin.systemd:
        name: shield-mcp-server
        state: stopped
      when: recovery_mode in ['configuration', 'full']

    - name: Download backup to server
      ansible.builtin.command: "scp hx-backup-server:{{ latest_backup.stdout }} /tmp/"
      args:
        creates: "/tmp/{{ latest_backup.stdout | basename }}"

    - name: Extract backup
      ansible.builtin.unarchive:
        src: "/tmp/{{ latest_backup.stdout | basename }}"
        dest: /tmp/
        remote_src: yes

    - name: Restore configuration file
      ansible.builtin.copy:
        src: "/tmp/{{ latest_backup.stdout | basename | regex_replace('\\.tar\\.gz$', '') }}/env.txt"
        dest: /opt/fastmcp/shield/.env
        owner: fastmcp
        group: fastmcp
        mode: '0600'
        remote_src: yes
      when: recovery_mode in ['configuration', 'full']

    - name: Restore application files
      ansible.builtin.unarchive:
        src: "/tmp/{{ latest_backup.stdout | basename | regex_replace('\\.tar\\.gz$', '') }}/fastmcp-app.tar.gz"
        dest: /
        remote_src: yes
      when: recovery_mode == 'full'

    - name: Restore systemd service
      ansible.builtin.copy:
        src: "/tmp/{{ latest_backup.stdout | basename | regex_replace('\\.tar\\.gz$', '') }}/shield-mcp-server.service"
        dest: /etc/systemd/system/shield-mcp-server.service
        remote_src: yes
      when: recovery_mode == 'full'
      notify: reload systemd

    - name: Start Shield MCP service
      ansible.builtin.systemd:
        name: shield-mcp-server
        state: started
        enabled: yes
      when: recovery_mode in ['configuration', 'full']

    - name: Wait for service to be ready
      ansible.builtin.uri:
        url: "http://localhost:8081/health"
        status_code: 200
        timeout: 30
      register: health_check
      retries: 6
      delay: 5
      until: health_check.status == 200

    - name: Display recovery status
      ansible.builtin.debug:
        msg: |
          ✅ Recovery completed successfully
          Service Status: {{ health_check.json.status }}
          Health Check: {{ health_check.json }}

  handlers:
    - name: reload systemd
      ansible.builtin.systemd:
        daemon_reload: yes
```

### Usage Examples

```bash
# Restore configuration only
ansible-playbook playbooks/recover-mcp-server.yml \
  -i inventory/prod.ini \
  -l hx-mcp1-server \
  -e "recovery_mode=configuration"

# Full restore (config + app + service)
ansible-playbook playbooks/recover-mcp-server.yml \
  -i inventory/prod.ini \
  -l hx-mcp1-server \
  -e "recovery_mode=full"

# Complete rebuild (from Ansible only)
ansible-playbook playbooks/deploy-base.yml playbooks/deploy-api.yml \
  -i inventory/prod.ini \
  -l hx-mcp1-server \
  --ask-vault-pass
```

---

## Summary

### Backup Tiers

1. **Git Repository (Primary):** All Ansible code, 100% recoverable
2. **Daily Backups:** Configuration files, 30-day retention
3. **Weekly Backups:** Full snapshots, 12-week retention

### Recovery Times

- **Configuration restore:** < 5 minutes
- **Application restore:** < 10 minutes
- **Complete rebuild:** < 30 minutes

### Key Files

- `/usr/local/bin/shield-mcp-backup.sh` - Automated backup script
- `/etc/cron.d/shield-mcp-backup` - Backup schedule
- `playbooks/recover-mcp-server.yml` - Ansible recovery playbook
- `docs/shield-mcp-backup-recovery.md` - This document

---

**Status:** ✅ Procedures Documented - Automation scripts ready for deployment

**Next Steps:**
1. Deploy backup script to server
2. Configure cron schedule
3. Test backup procedure
4. Validate recovery procedure
5. Document in runbooks
