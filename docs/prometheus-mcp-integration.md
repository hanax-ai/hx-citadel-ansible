# Prometheus Integration for Shield MCP Server

**Date:** 2025-01-07  
**Purpose:** Monitor Shield MCP Server health, performance, and dependencies  
**Target:** hx-metrics-server (192.168.10.16)  
**Source:** hx-mcp1-server (192.168.10.59:8081)

---

## Overview

This document describes the Prometheus monitoring setup for the Shield MCP Server deployment. The configuration enables comprehensive observability including health checks, dependency status, tool execution metrics, and alerting.

---

## Architecture

```
┌─────────────────────────┐
│  hx-metrics-server      │
│  (192.168.10.16)        │
│                         │
│  ┌──────────────────┐   │
│  │   Prometheus     │   │
│  │   Port: 9090     │───┼───► Scrapes every 30s
│  └──────────────────┘   │
│                         │
│  ┌──────────────────┐   │
│  │   Grafana        │   │
│  │   Port: 3000     │───┼───► Visualizes metrics
│  └──────────────────┘   │
└─────────────────────────┘
            │
            │ HTTP GET /health
            │ HTTP GET /metrics
            ▼
┌─────────────────────────┐
│  hx-mcp1-server         │
│  (192.168.10.59:8081)   │
│                         │
│  ┌──────────────────┐   │
│  │  Shield MCP      │   │
│  │  FastMCP Server  │   │
│  └──────────────────┘   │
│         │               │
│         ├─► Qdrant      │
│         ├─► Ollama      │
│         └─► Orchestrator│
└─────────────────────────┘
```

---

## Metrics Endpoints

### Primary Health Endpoint

**URL:** `http://192.168.10.59:8081/health`

**Response Format:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-07T10:30:00Z",
  "server": {
    "name": "Shield MCP Server",
    "version": "1.0.0",
    "uptime_seconds": 3600
  },
  "dependencies": {
    "qdrant": {
      "status": "healthy",
      "response_time_ms": 45,
      "url": "https://192.168.10.9:6333"
    },
    "ollama": {
      "status": "healthy",
      "response_time_ms": 120,
      "url": "https://192.168.10.18:11434"
    },
    "orchestrator": {
      "status": "partial",
      "response_time_ms": 0,
      "url": "http://192.168.10.14:8000"
    }
  },
  "overall_status": "healthy_partial"
}
```

### Detailed Metrics Endpoint

**URL:** `http://192.168.10.59:8081/metrics`

**Metrics Exposed:**
- `fastmcp_tool_executions_total` - Total tool execution count
- `fastmcp_tool_errors_total` - Total tool execution errors
- `fastmcp_tool_duration_seconds` - Tool execution duration histogram
- `fastmcp_dependency_status` - Dependency health (1=healthy, 0=down)
- `fastmcp_requests_total` - Total HTTP requests received
- `fastmcp_active_connections` - Current active connections

---

## Prometheus Configuration

### Step 1: Add Scrape Jobs

Edit `/etc/prometheus/prometheus.yml` on **hx-metrics-server**:

```yaml
# Existing scrape_configs section
scrape_configs:
  
  # ... existing jobs ...

  # Shield MCP Server - Health Monitoring
  - job_name: 'shield-mcp-server'
    scrape_interval: 30s
    scrape_timeout: 10s
    metrics_path: '/health'
    scheme: http
    static_configs:
      - targets: ['192.168.10.59:8081']
        labels:
          environment: 'production'
          service: 'shield-mcp'
          role: 'mcp-server'
          hostname: 'hx-mcp1-server'
          datacenter: 'hx-citadel'

  # Shield MCP Server - Detailed Metrics
  - job_name: 'shield-mcp-tools'
    scrape_interval: 60s
    scrape_timeout: 10s
    metrics_path: '/metrics'
    scheme: http
    static_configs:
      - targets: ['192.168.10.59:8081']
        labels:
          environment: 'production'
          service: 'shield-mcp-tools'
          role: 'mcp-server'
          hostname: 'hx-mcp1-server'
          datacenter: 'hx-citadel'
```

### Step 2: Add Alerting Rules

Create `/etc/prometheus/rules/shield-mcp-alerts.yml` on **hx-metrics-server**:

```yaml
groups:
  - name: shield_mcp_alerts
    interval: 30s
    rules:
      # Critical: Service Down
      - alert: ShieldMCPDown
        expr: up{job="shield-mcp-server"} == 0
        for: 2m
        labels:
          severity: critical
          service: shield-mcp
          team: infrastructure
        annotations:
          summary: "Shield MCP Server is down"
          description: "Shield MCP Server on hx-mcp1-server (192.168.10.59) has been down for more than 2 minutes."
          runbook_url: "https://docs.hx-citadel.local/runbooks/shield-mcp-down"

      # Warning: Health Check Failing
      - alert: ShieldMCPUnhealthy
        expr: probe_success{job="shield-mcp-server"} == 0
        for: 5m
        labels:
          severity: warning
          service: shield-mcp
          team: infrastructure
        annotations:
          summary: "Shield MCP Server health check failing"
          description: "Shield MCP Server is reporting unhealthy status for 5+ minutes."

      # Warning: High Latency
      - alert: ShieldMCPHighLatency
        expr: probe_duration_seconds{job="shield-mcp-server"} > 5
        for: 5m
        labels:
          severity: warning
          service: shield-mcp
          team: infrastructure
        annotations:
          summary: "Shield MCP Server high response time"
          description: "Health check response time exceeds 5 seconds."

      # Warning: Qdrant Dependency Down
      - alert: ShieldMCPQdrantDown
        expr: fastmcp_dependency_status{service="qdrant"} == 0
        for: 5m
        labels:
          severity: warning
          service: shield-mcp
          dependency: qdrant
          team: infrastructure
        annotations:
          summary: "Shield MCP cannot reach Qdrant"
          description: "Shield MCP Server cannot connect to Qdrant at 192.168.10.9:6333."

      # Warning: Ollama Dependency Down
      - alert: ShieldMCPOllamaDown
        expr: fastmcp_dependency_status{service="ollama"} == 0
        for: 5m
        labels:
          severity: warning
          service: shield-mcp
          dependency: ollama
          team: infrastructure
        annotations:
          summary: "Shield MCP cannot reach Ollama"
          description: "Shield MCP Server cannot connect to Ollama at 192.168.10.18:11434."

      # Warning: High Error Rate
      - alert: ShieldMCPHighErrorRate
        expr: rate(fastmcp_tool_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
          service: shield-mcp
          team: infrastructure
        annotations:
          summary: "High error rate in Shield MCP tools"
          description: "Tool execution error rate exceeds 10% over 5 minutes."
```

### Step 3: Update Prometheus Main Config

Edit `/etc/prometheus/prometheus.yml` to include the alerting rules:

```yaml
# Alerting configuration
rule_files:
  # Existing rules
  - "/etc/prometheus/rules/*.yml"
  
  # Shield MCP rules
  - "/etc/prometheus/rules/shield-mcp-alerts.yml"
```

### Step 4: Reload Prometheus Configuration

```bash
# On hx-metrics-server
sudo systemctl reload prometheus

# Or send SIGHUP
sudo kill -HUP $(pgrep prometheus)

# Verify configuration
promtool check config /etc/prometheus/prometheus.yml
promtool check rules /etc/prometheus/rules/shield-mcp-alerts.yml
```

---

## Grafana Dashboard

### Dashboard Creation

1. **Access Grafana:** `http://192.168.10.16:3000`
2. **Create New Dashboard:** Dashboards → New Dashboard
3. **Dashboard Name:** "Shield MCP Server Monitoring"
4. **Dashboard UID:** `shield-mcp-monitoring`

### Recommended Panels

#### Panel 1: Service Status (Stat)

```promql
# Query
up{job="shield-mcp-server"}

# Settings
- Type: Stat
- Color: Green (1), Red (0)
- Title: "Service Status"
- Unit: None
- Thresholds: 1 (Green), 0 (Red)
```

#### Panel 2: Health Check Status (Stat)

```promql
# Query
probe_success{job="shield-mcp-server"}

# Settings
- Type: Stat
- Color: Green (1), Red (0)
- Title: "Health Check"
- Display: "Healthy" / "Unhealthy"
```

#### Panel 3: Response Time (Time Series)

```promql
# Query
probe_duration_seconds{job="shield-mcp-server"}

# Settings
- Type: Time Series
- Title: "Health Check Response Time"
- Unit: seconds
- Y-Axis Min: 0
```

#### Panel 4: Tool Execution Rate (Time Series)

```promql
# Query
rate(fastmcp_tool_executions_total[5m])

# Settings
- Type: Time Series
- Title: "Tool Execution Rate"
- Unit: ops/sec
- Legend: {{tool}}
```

#### Panel 5: Tool Error Rate (Time Series)

```promql
# Query
rate(fastmcp_tool_errors_total[5m])

# Settings
- Type: Time Series
- Title: "Tool Error Rate"
- Unit: errors/sec
- Color: Red
- Alert Threshold: 0.1
```

#### Panel 6: Dependency Status (Stat Grid)

```promql
# Query 1: Qdrant
fastmcp_dependency_status{service="qdrant"}

# Query 2: Ollama
fastmcp_dependency_status{service="ollama"}

# Query 3: Orchestrator
fastmcp_dependency_status{service="orchestrator"}

# Settings
- Type: Stat
- Layout: Grid (3 columns)
- Color: Green (1), Red (0), Yellow (0.5)
```

#### Panel 7: Request Rate (Time Series)

```promql
# Query
rate(fastmcp_requests_total[5m])

# Settings
- Type: Time Series
- Title: "HTTP Request Rate"
- Unit: req/sec
```

#### Panel 8: Active Connections (Gauge)

```promql
# Query
fastmcp_active_connections

# Settings
- Type: Gauge
- Title: "Active Connections"
- Max: 100
- Thresholds: 80 (Yellow), 90 (Red)
```

### Dashboard Variables

Add these template variables for filtering:

```
$environment = label_values(up{job="shield-mcp-server"}, environment)
$hostname = label_values(up{job="shield-mcp-server"}, hostname)
```

---

## Verification Steps

### 1. Test Metrics Endpoint

```bash
# From any server
curl -s http://192.168.10.59:8081/health | jq .

# Expected output: JSON with status, dependencies, etc.
```

### 2. Verify Prometheus Scraping

```bash
# Access Prometheus web UI
http://192.168.10.16:9090

# Go to Status → Targets
# Look for: shield-mcp-server (should be UP)
```

### 3. Query Metrics in Prometheus

```promql
# Service up/down
up{job="shield-mcp-server"}

# Health check success
probe_success{job="shield-mcp-server"}

# Dependency status
fastmcp_dependency_status
```

### 4. Verify Alerting Rules

```bash
# Check rules are loaded
curl http://192.168.10.16:9090/api/v1/rules | jq '.data.groups[] | select(.name=="shield_mcp_alerts")'
```

### 5. Test Alert Firing

```bash
# Stop Shield MCP service to trigger alerts
ssh hx-mcp1-server 'sudo systemctl stop shield-mcp-server'

# Wait 2 minutes, check Prometheus alerts
http://192.168.10.16:9090/alerts

# Should see: ShieldMCPDown (FIRING)

# Restart service
ssh hx-mcp1-server 'sudo systemctl start shield-mcp-server'
```

---

## Ansible Automation

### Add Prometheus Configuration Task

Create `roles/fastmcp_server/tasks/08-monitoring.yml`:

```yaml
---
# Prometheus monitoring integration

- name: Generate Prometheus scrape configuration
  ansible.builtin.template:
    src: prometheus_scrape_config.yml.j2
    dest: "{{ fastmcp_app_dir }}/prometheus-config.yml"
    owner: "{{ fastmcp_service_user }}"
    group: "{{ fastmcp_service_group }}"
    mode: "0644"
  become: yes

- name: Display Prometheus integration instructions
  ansible.builtin.debug:
    msg: |
      ╔════════════════════════════════════════════════════════════════╗
      ║           Prometheus Integration Instructions                  ║
      ╠════════════════════════════════════════════════════════════════╣
      ║                                                                ║
      ║  1. Copy configuration to metrics server:                      ║
      ║     scp {{ fastmcp_app_dir }}/prometheus-config.yml \         ║
      ║         hx-metrics-server:/tmp/                                ║
      ║                                                                ║
      ║  2. SSH to metrics server:                                     ║
      ║     ssh hx-metrics-server                                      ║
      ║                                                                ║
      ║  3. Append to Prometheus config:                               ║
      ║     sudo cat /tmp/prometheus-config.yml >> \                   ║
      ║         /etc/prometheus/prometheus.yml                         ║
      ║                                                                ║
      ║  4. Reload Prometheus:                                         ║
      ║     sudo systemctl reload prometheus                           ║
      ║                                                                ║
      ║  5. Verify targets:                                            ║
      ║     http://192.168.10.16:9090/targets                          ║
      ║                                                                ║
      ╚════════════════════════════════════════════════════════════════╝
```

---

## Retention and Storage

### Metrics Retention

- **Recommended:** 90 days
- **Configuration:** Add to Prometheus startup flags
- **Location:** `/etc/default/prometheus` or systemd service file

```bash
# Add to Prometheus flags
--storage.tsdb.retention.time=90d
--storage.tsdb.path=/var/lib/prometheus/data
```

### Disk Space Estimation

- **Scrape Interval:** 30s for health, 60s for metrics
- **Estimated Size:** ~50MB/day per endpoint
- **90-day retention:** ~4.5GB total

---

## Troubleshooting

### Issue: Targets Show as "DOWN"

```bash
# Check firewall on MCP server
sudo ufw status | grep 8081

# Allow from metrics server
sudo ufw allow from 192.168.10.16 to any port 8081 proto tcp

# Verify service is running
sudo systemctl status shield-mcp-server

# Test endpoint manually
curl http://192.168.10.59:8081/health
```

### Issue: No Metrics Available

```bash
# Check if metrics endpoint is implemented
curl http://192.168.10.59:8081/metrics

# Verify FastMCP server logs
sudo journalctl -u shield-mcp-server -f
```

### Issue: Alerts Not Firing

```bash
# Check alert rules are loaded
curl http://localhost:9090/api/v1/rules | jq .

# Verify Alertmanager is configured
sudo systemctl status alertmanager

# Check Prometheus logs
sudo journalctl -u prometheus -f
```

---

## Integration Checklist

- [ ] Prometheus scrape jobs added to `/etc/prometheus/prometheus.yml`
- [ ] Alert rules created in `/etc/prometheus/rules/shield-mcp-alerts.yml`
- [ ] Prometheus configuration reloaded
- [ ] Targets showing as UP in Prometheus UI
- [ ] Grafana dashboard created and configured
- [ ] Alert rules tested (service stop/start)
- [ ] Firewall rules added for metrics server access
- [ ] Documentation updated with dashboard URLs
- [ ] Team notified of new monitoring endpoints

---

**Status:** ✅ Configuration Ready - Manual integration with hx-metrics-server required

**Next Steps:**
1. Apply configuration to hx-metrics-server
2. Create Grafana dashboard
3. Test alert notifications
4. Document in runbooks
