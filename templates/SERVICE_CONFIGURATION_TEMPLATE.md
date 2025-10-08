# SERVICE CONFIGURATION TEMPLATE

> **Template Version:** 1.0  
> **Last Updated:** October 8, 2025  
> **Purpose:** Document service configurations deployed via Ansible

---

## NAMING CONVENTIONS

### File Naming
- **Format:** `[SERVICE_NAME]_config_YYYY-MM-DD.md`
- **Examples:** 
  - `qdrant_ui_config_2025-10-08.md`
  - `postgresql_config_2025-10-08.md`
  - `ollama_config_2025-10-08.md`
- **Location:** `configuration/` directory in project root

### Version Control
- Create new configuration file when significant changes occur
- Reference the date in the filename to track configuration evolution
- Keep previous configurations for rollback reference

---

## DOCUMENT STRUCTURE

```markdown
# [Service Name] Configuration Snapshot

**Last Updated:** [Date]  
**Service Version:** [Version Number]  
**Deployed By:** [Playbook Name]  
**Configuration Status:** 🟢 Active | 🟡 Testing | 🔴 Deprecated

---

## Executive Summary

[2-3 sentence overview of what this service does and its role in the infrastructure]

> **Security Notice:** [Any security considerations, API keys, certificates, etc.]

---

## Core Service Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Service Host | `[hostname]` | [Description] |
| Service IP / Port | `[protocol://ip:port]` | [Access method] |
| Backend/Upstream | `[backend details]` | [If applicable] |
| Deployment Root | `[path]` | [Installation directory] |
| Service User | `[username]` | [User running the service] |
| Service Group | `[groupname]` | [Group ownership] |
| Protocol | `http/https/tcp/udp` | [Communication protocol] |
| SSL/TLS | `enabled/disabled` | [Certificate details] |

---

## Infrastructure Context

### Network Configuration
```
┌─────────────────────────────────────┐
│  Client Layer                        │
│  [Client description]                │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Service Layer                       │
│  [Service Name] on [Host]            │
│  IP: [IP Address]                    │
│  Port(s): [Ports]                    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Backend/Database Layer              │
│  [Backend service details]           │
└─────────────────────────────────────┘
```

### Network Details
- **Subnet:** [Network range]
- **Firewall Rules:** [Port access rules]
- **DNS:** [DNS configuration if applicable]
- **Load Balancer:** [If applicable]

---

## Playbook Configuration

### Ansible Playbook
**File:** `playbooks/[playbook-name].yml`

```yaml
---
- name: [Playbook Description]
  hosts: [target_group]
  become: yes
  gather_facts: yes
  collections:
    - [required collections]
  
  vars:
    # Service Configuration
    service_host: [value]
    service_port: [value]
    service_protocol: [http/https]
    
    # Backend Configuration (if applicable)
    backend_host: [value]
    backend_port: [value]
    backend_protocol: [http/https]
    backend_ssl_verify: [on/off]
    
    # Authentication (reference vault, don't expose secrets)
    service_api_key: "{{ vault_service_api_key }}"
    
    # Application Settings
    app_root: [path]
    app_user: [username]
    app_group: [groupname]
    
  roles:
    - [role_name]
```

### Role Variables
**File:** `roles/[role-name]/defaults/main.yml`

```yaml
---
# Default variables (can be overridden in playbook)
service_version: [version]
service_port: [port]
service_root: [path]
# ... additional defaults
```

---

## Service Architecture

### Directory Structure
```
[service_root]/
├── [component]/
│   ├── [subcomponent]/
│   └── ...
├── config/
│   ├── [config files]
│   └── ...
├── logs/
│   ├── access.log
│   ├── error.log
│   └── ...
├── scripts/
│   ├── [maintenance scripts]
│   └── ...
└── [other directories]
```

### File Locations
| Component | Path | Purpose |
|-----------|------|---------|
| Configuration | `[path]` | [Description] |
| Logs | `[path]` | [Description] |
| Data | `[path]` | [Description] |
| Scripts | `[path]` | [Description] |
| Systemd Unit | `[path]` | [Description] |

---

## Configuration Files

### Main Configuration
**File:** `[path/to/config]`

```[format]
# Configuration content
# Document key settings and their values
[key]: [value]
[key]: [value]
```

**Key Settings:**
- **[Setting 1]:** `[value]` - [Description and purpose]
- **[Setting 2]:** `[value]` - [Description and purpose]
- **[Setting 3]:** `[value]` - [Description and purpose]

### Additional Configuration Files
List any additional configuration files with their purpose:

1. **[filename]** - [Purpose]
2. **[filename]** - [Purpose]

---

## Nginx/Reverse Proxy Configuration

> **Note:** Include this section if service uses a reverse proxy

### Upstream Configuration
```nginx
upstream [backend_name] {
    server [host]:[port];
    keepalive [number];
}
```

### Server Block
```nginx
server {
    listen [port];
    server_name [hostname] [ip];
    
    # Proxy configuration
    location [path] {
        proxy_pass [protocol://upstream];
        proxy_set_header Host $host;
        # ... additional proxy settings
    }
}
```

### Key Endpoints
| Endpoint | Purpose | Backend | Notes |
|----------|---------|---------|-------|
| `/[path]` | [Purpose] | `[backend]` | [Notes] |
| `/[path]` | [Purpose] | `[backend]` | [Notes] |

---

## Authentication & Security

### Authentication Method
- **Type:** [API Key / OAuth / Basic Auth / Certificate / None]
- **Location:** [Where credentials are stored - reference vault]
- **Rotation Policy:** [Frequency and procedure]

### API Keys / Secrets
> ⚠️ **Never include actual secrets in configuration documentation**

- **Service API Key:** Stored in `group_vars/all/vault.yml` as `vault_[service]_api_key`
- **Database Credentials:** Stored in `group_vars/all/vault.yml` as `vault_[db]_credentials`
- **Certificate Paths:** 
  - Certificate: `[path]`
  - Key: `[path]`
  - CA Certificate: `[path]`

### TLS/SSL Configuration
- **TLS Enabled:** [Yes/No]
- **Certificate Type:** [Self-signed / CA-signed / Let's Encrypt]
- **Certificate Expiry:** [Date]
- **SSL Verification:** [On/Off]
- **Supported Protocols:** [TLS 1.2, TLS 1.3, etc.]

### Firewall Rules
```bash
# Incoming traffic
[command to configure firewall]

# Outgoing traffic (if applicable)
[command to configure firewall]
```

---

## Service Management

### Systemd Unit
**File:** `/etc/systemd/system/[service-name].service`

```ini
[Unit]
Description=[Service Description]
After=[dependencies]

[Service]
Type=[type]
User=[user]
Group=[group]
WorkingDirectory=[path]
ExecStart=[command]
ExecReload=[command]
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Service Commands
```bash
# Start service
sudo systemctl start [service-name]

# Stop service
sudo systemctl stop [service-name]

# Restart service
sudo systemctl restart [service-name]

# Check status
sudo systemctl status [service-name]

# Enable on boot
sudo systemctl enable [service-name]

# View logs
sudo journalctl -u [service-name] -f
```

---

## Available Endpoints

### API Endpoints
| Endpoint | Method | Purpose | Authentication | Response |
|----------|--------|---------|----------------|----------|
| `/[path]` | GET | [Purpose] | [Required?] | [Format] |
| `/[path]` | POST | [Purpose] | [Required?] | [Format] |
| `/[path]` | PUT | [Purpose] | [Required?] | [Format] |

### Health Checks
```bash
# Service health
curl [protocol]://[host]:[port]/health

# Detailed status
curl [protocol]://[host]:[port]/status

# Metrics (if available)
curl [protocol]://[host]:[port]/metrics
```

### Expected Responses
```json
// Health check response
{
  "status": "ok",
  "version": "[version]",
  "timestamp": "[timestamp]"
}
```

---

## Testing & Validation

### Deployment Validation
```bash
# Test 1: Service accessibility
curl -I [protocol]://[host]:[port]

# Test 2: API endpoint
curl -s [protocol]://[host]:[port]/[endpoint]

# Test 3: Backend connectivity (if applicable)
curl -s [protocol]://[host]:[port]/[backend-test-endpoint]

# Test 4: Authentication (with API key)
curl -H "Authorization: Bearer [token]" [protocol]://[host]:[port]/[endpoint]
```

### Expected Results
- ✅ Service returns HTTP 200
- ✅ API endpoints respond correctly
- ✅ Backend connectivity established
- ✅ Authentication working

### Validation Checklist
- [ ] Service starts without errors
- [ ] All endpoints respond correctly
- [ ] Logs show no errors
- [ ] Authentication works
- [ ] Backend connections established
- [ ] Health checks pass
- [ ] Firewall rules allow traffic
- [ ] Service auto-starts on boot

---

## Monitoring & Logging

### Log Files
| Log Type | Location | Rotation | Retention |
|----------|----------|----------|-----------|
| Access | `[path]` | [Policy] | [Days] |
| Error | `[path]` | [Policy] | [Days] |
| Application | `[path]` | [Policy] | [Days] |

### Log Rotation
**File:** `/etc/logrotate.d/[service-name]`

```
[log-path] {
    daily
    rotate [days]
    compress
    delaycompress
    notifempty
    create [permissions] [user] [group]
}
```

### Monitoring Commands
```bash
# Check logs
sudo tail -f [log-path]

# Check for errors
sudo grep -i error [log-path]

# Monitor resource usage
sudo systemctl status [service-name]
htop -p $(pgrep -f [service-name])
```

### Metrics
- **CPU Usage:** [Normal range]
- **Memory Usage:** [Normal range]
- **Disk Usage:** [Normal range]
- **Network Traffic:** [Normal range]
- **Response Time:** [Normal range]

---

## Maintenance & Operations

### Backup Procedures
```bash
# Backup configuration
[backup commands]

# Backup data (if applicable)
[backup commands]

# Verify backup
[verification commands]
```

### Update Procedures
```bash
# 1. Backup current configuration
[backup commands]

# 2. Stop service
sudo systemctl stop [service-name]

# 3. Update service
[update commands]

# 4. Restart service
sudo systemctl start [service-name]

# 5. Verify
[verification commands]
```

### Rollback Procedures
```bash
# 1. Stop service
sudo systemctl stop [service-name]

# 2. Restore previous version
[rollback commands]

# 3. Restart service
sudo systemctl start [service-name]

# 4. Verify
[verification commands]
```

---

## Troubleshooting

### Common Issues

#### Issue 1: [Issue Description]
**Symptoms:**
- [Symptom 1]
- [Symptom 2]

**Diagnosis:**
```bash
[diagnostic commands]
```

**Resolution:**
```bash
[resolution commands]
```

#### Issue 2: [Issue Description]
**Symptoms:**
- [Symptom 1]
- [Symptom 2]

**Diagnosis:**
```bash
[diagnostic commands]
```

**Resolution:**
```bash
[resolution commands]
```

### Diagnostic Commands
```bash
# Check service status
sudo systemctl status [service-name]

# Check connectivity
nc -zv [host] [port]

# Check logs
sudo tail -100 [log-path]

# Check configuration syntax
[validation command]

# Check resources
df -h [mount-point]
free -h
```

---

## Performance Tuning

### Current Settings
| Setting | Value | Rationale |
|---------|-------|-----------|
| [Setting 1] | [Value] | [Why this value] |
| [Setting 2] | [Value] | [Why this value] |

### Optimization Opportunities
- [Optimization 1]: [Description and expected impact]
- [Optimization 2]: [Description and expected impact]

---

## Dependencies

### Service Dependencies
| Dependency | Version | Required? | Purpose |
|------------|---------|-----------|---------|
| [Service 1] | [Version] | Yes/No | [Purpose] |
| [Service 2] | [Version] | Yes/No | [Purpose] |

### Network Dependencies
- **Inbound:** [Services that connect to this service]
- **Outbound:** [Services this service connects to]

### Package Dependencies
```bash
# Required packages
[package list]

# Installation commands
[installation commands]
```

---

## Change History

### [YYYY-MM-DD] - [Change Title]
**Changed By:** [Name]  
**Playbook Run:** [Playbook name and command]

**Changes:**
- [Change 1]
- [Change 2]

**Impact:**
- [Impact description]

**Validation:**
- ✅ [Validation step 1]
- ✅ [Validation step 2]

---

### [YYYY-MM-DD] - [Change Title]
**Changed By:** [Name]  
**Playbook Run:** [Playbook name and command]

**Changes:**
- [Change 1]
- [Change 2]

**Impact:**
- [Impact description]

**Validation:**
- ✅ [Validation step 1]
- ✅ [Validation step 2]

---

## References

### Related Documentation
- [Configuration Guide] - `[path/to/doc]`
- [API Documentation] - `[URL or path]`
- [Deployment Playbook] - `playbooks/[playbook-name].yml`
- [Ansible Role] - `roles/[role-name]/`

### External Resources
- [Official Documentation] - [URL]
- [Community Resources] - [URL]
- [GitHub Repository] - [URL]

### Related Status Reports
- [STATUS-YYYY-MM-DD.md] - [Brief description of relevant status]

---

## Appendix

### Environment Variables
```bash
# Service environment variables
export VAR_NAME="value"
export VAR_NAME="value"
```

### Configuration Snippets
[Include any additional relevant configuration examples]

### Scripts
[Include or reference any maintenance or deployment scripts]

---

**Document Maintained By:** [Team Name]  
**Last Reviewed:** [Date]  
**Next Review:** [Date]  
**Contact:** [Contact information]
```

---

## TEMPLATE USAGE GUIDELINES

### When to Create a Configuration Document
1. **Initial Deployment** - Document configuration after first successful deployment
2. **Major Changes** - Create new version when significant configuration changes occur
3. **Service Updates** - Document after version upgrades
4. **Security Updates** - Document after security patches or credential rotation
5. **Architecture Changes** - Document when service architecture changes

### What to Document
✅ **DO Document:**
- Current service configuration
- Network topology and dependencies
- File locations and directory structure
- Commands for common operations
- Troubleshooting procedures
- Links to vault for secrets (never actual secrets)

❌ **DON'T Document:**
- Actual API keys, passwords, or secrets
- Temporary configurations or experiments
- Debug settings that shouldn't be in production
- Personal scripts or workflows

### Maintenance
- Review configuration docs quarterly
- Update after any infrastructure changes
- Archive old configurations to `configuration/archive/`
- Cross-reference with status reports
- Keep vault references updated

### Best Practices
- Use tables for structured data
- Include command examples with expected output
- Link to related documentation
- Version control all changes
- Test all commands before documenting
- Include rollback procedures
- Document the "why" not just the "what"

---

**Template Created By:** DevOps Team  
**Template Version:** 1.0  
**Questions or Suggestions?** Contact the platform team or submit an issue.
