# FQDN Policy Violations Report
**Date**: October 10, 2025  
**Scanner**: scripts/check-fqdn.sh  
**Status**: 35 violations found (after allowlist filtering)

---

## Executive Summary

The FQDN policy enforcer found **35 hardcoded IP addresses and localhost references** across the Ansible roles. These need to be replaced with FQDNs or Ansible variables from `group_vars/all/fqdn_map.yml`.

### Violation Categories

1. **Critical (Production Config)**: 22 violations - Must fix before Component 6
2. **Medium (Templates)**: 8 violations - Should fix during Component 6
3. **Low (Documentation)**: 5 violations - Can fix later

---

## Critical Violations (Production Configs)

### Component 2 (FastAPI) - 13 violations

**File**: `roles/orchestrator_fastapi/defaults/main.yml`
```yaml
# Lines 29-32: CORS origins using IPs
orchestrator_cors_origins:
  - "http://192.168.10.11"       # ❌ Should be: hx-webui-server
  - "http://192.168.10.12:3000"  # ❌ Should be: hx-dev-server
  - "http://192.168.10.12:3001"  # ❌ Should be: hx-dev-server
  - "http://192.168.10.12:3002"  # ❌ Should be: hx-dev-server
```

**Recommended Fix**:
```yaml
orchestrator_cors_origins:
  - "http://{{ hx_hosts_fqdn['hx-webui-server'] }}"
  - "http://{{ hx_hosts_fqdn['hx-dev-server'] }}:3000"
  - "http://{{ hx_hosts_fqdn['hx-dev-server'] }}:3001"
  - "http://{{ hx_hosts_fqdn['hx-dev-server'] }}:3002"
```

---

**File**: `roles/orchestrator_fastapi/templates/config/.env.j2`
```bash
# Lines 13, 20, 25, 31: Database and service connections
POSTGRES_HOST=192.168.10.48         # ❌ hx-sqldb-server
REDIS_HOST=192.168.10.48            # ❌ hx-sqldb-server
QDRANT_URL=https://192.168.10.9:6333   # ❌ hx-vectordb-server
LLM_API_BASE=http://192.168.10.46:4000/v1  # ❌ hx-litellm-server
```

**Recommended Fix**:
```bash
POSTGRES_HOST={{ hx_hosts_fqdn['hx-sqldb-server'] }}
REDIS_HOST={{ hx_hosts_fqdn['hx-sqldb-server'] }}
QDRANT_URL=https://{{ hx_hosts_fqdn['hx-vectordb-server'] }}:6333
LLM_API_BASE=http://{{ hx_hosts_fqdn['hx-litellm-server'] }}:4000/v1
```

---

**File**: `roles/orchestrator_fastapi/templates/config/settings.py.j2`
```python
# Lines 30, 41, 50, 56: Default values with IPs
postgres_host: str = Field(default="192.168.10.48")
redis_host: str = Field(default="192.168.10.48")
qdrant_url: str = Field(default="https://192.168.10.9:6333")
llm_api_base: str = Field(default="http://192.168.10.46:4000/v1")
```

**Recommended Fix**:
```python
postgres_host: str = Field(default="{{ hx_hosts_fqdn['hx-sqldb-server'] }}")
redis_host: str = Field(default="{{ hx_hosts_fqdn['hx-sqldb-server'] }}")
qdrant_url: str = Field(default="https://{{ hx_hosts_fqdn['hx-vectordb-server'] }}:6333")
llm_api_base: str = Field(default="http://{{ hx_hosts_fqdn['hx-litellm-server'] }}:4000/v1")
```

---

**File**: `roles/orchestrator_fastapi/templates/main.py.j2`
```python
# Lines 84-87: CORS allowed hosts
allowed_hosts=[
    "192.168.10.8",    # ❌ hx-orchestrator-server
    "hx-orchestrator-server",
    "localhost",       # ⚠️ Acceptable for dev, but prefer FQDN
    "127.0.0.1"        # ⚠️ Acceptable for dev, but prefer FQDN
]
```

**Recommended Fix**:
```python
allowed_hosts=[
    "{{ hx_hosts_fqdn['hx-orchestrator-server'] }}",
    "hx-orchestrator-server.dev-test.hana-x.ai",
    "hx-orchestrator-server",
    "localhost",  # Keep for local dev
    "127.0.0.1"   # Keep for local dev
]
```

---

### Component 3 (PostgreSQL) - 1 violation

**File**: `roles/orchestrator_postgresql/defaults/main.yml`
```yaml
# Line 5: PostgreSQL host
postgres_host: "192.168.10.48"  # ❌ hx-sqldb-server
```

**Recommended Fix**:
```yaml
postgres_host: "{{ hx_hosts_fqdn['hx-sqldb-server'] }}"
```

---

### Component 4 (Redis) - 2 violations

**File**: `roles/orchestrator_redis/defaults/main.yml`
```yaml
# Lines 3, 7: Redis connection
redis_host: "192.168.10.48"  # ❌ hx-sqldb-server
redis_url: "redis://:{{ vault_redis_password }}@192.168.10.48:6379/0"  # ❌
```

**Recommended Fix**:
```yaml
redis_host: "{{ hx_hosts_fqdn['hx-sqldb-server'] }}"
redis_url: "redis://:{{ vault_redis_password }}@{{ hx_hosts_fqdn['hx-sqldb-server'] }}:6379/0"
```

---

### Component 5 (Qdrant) - 2 violations

**File**: `roles/orchestrator_qdrant/defaults/main.yml`
```yaml
# Lines 3, 11: Qdrant and Ollama URLs
qdrant_url: "https://192.168.10.9:6333"    # ❌ hx-vectordb-server
ollama_url: "http://192.168.10.50:11434"   # ❌ hx-ollama1
```

**Recommended Fix**:
```yaml
qdrant_url: "https://{{ hx_hosts_fqdn['hx-vectordb-server'] }}:6333"
ollama_url: "http://{{ hx_hosts_fqdn['hx-ollama1'] }}:11434"
```

---

### Qdrant Web UI - 1 violation

**File**: `roles/qdrant_web_ui/defaults/main.yml`
```yaml
# Line 8: Backend host
qdrant_ui_backend_host: 192.168.10.8  # ❌ hx-orchestrator-server
```

**Recommended Fix**:
```yaml
qdrant_ui_backend_host: "{{ hx_hosts_fqdn['hx-orchestrator-server'] }}"
```

---

### Legacy FastAPI Role - 2 violations

**File**: `roles/fastapi/templates/orchestrator.env.j2`
```bash
# Lines 3-4: Fallback defaults
QDRANT_URL={{ orch_env.QDRANT_URL | default('http://localhost:6333') }}  # ❌
LITELLM_URL={{ orch_env.LITELLM_URL | default('http://localhost:4000') }}  # ❌
```

**Recommended Fix**:
```bash
QDRANT_URL={{ orch_env.QDRANT_URL | default('https://' + hx_hosts_fqdn['hx-vectordb-server'] + ':6333') }}
LITELLM_URL={{ orch_env.LITELLM_URL | default('http://' + hx_hosts_fqdn['hx-litellm-server'] + ':4000') }}
```

---

## Medium Priority (Templates/Examples)

### FastMCP Server - 2 violations

**File**: `roles/fastmcp_server/templates/prometheus_scrape_config.yml.j2`
```yaml
# Line 4: Comment with IP
# Add this to Prometheus configuration on hx-metrics-server (192.168.10.16)  # ⚠️ Comment only
```

**File**: `roles/fastmcp_server/templates/logging_config.py.j2`
```python
# Line 175: Example log
logger.info("dependency_connected", service="qdrant", url="https://192.168.10.9:6333")  # ⚠️ Example
```

**Recommended**: Update comments and examples to use FQDNs for consistency.

---

### Orchestrator Redis API - 2 violations

**File**: `roles/orchestrator_redis/templates/api/events.py.j2`
```python
# Lines 28, 31: Example curl commands in docstrings
curl -N http://192.168.10.8:8000/events/stream  # ⚠️ Example
curl -N http://192.168.10.8:8000/events/stream?last_id=1234567890-0  # ⚠️ Example
```

**Recommended**: Update examples to use `hx-orchestrator-server.dev-test.hana-x.ai`.

---

## Low Priority (Documentation)

### Redis Role README - 2 violations

**File**: `roles/redis_role/README.md`
```markdown
redis_bind_interface: 127.0.0.1  # Example
redis_additional_bind_ip: "192.168.10.48"  # Example
```

**Recommended**: Update examples to use FQDNs.

---

### PostgreSQL Role README - 3 violations

**File**: `roles/postgresql_role/README.md`
```yaml
# Multiple lines: Documentation examples with 127.0.0.1 and localhost
```

**Recommended**: Update documentation to show FQDN best practices.

---

## Remediation Plan

### Phase 1: Critical Fixes (Before Component 6)
**Priority**: HIGH  
**Timeline**: Immediate (today)

1. ✅ Create `group_vars/all/fqdn_map.yml` - **DONE**
2. Update Component 2 (orchestrator_fastapi):
   - defaults/main.yml (CORS origins)
   - templates/config/.env.j2 (DB connections)
   - templates/config/settings.py.j2 (default values)
   - templates/main.py.j2 (allowed hosts)
3. Update Component 3 (orchestrator_postgresql):
   - defaults/main.yml (postgres_host)
4. Update Component 4 (orchestrator_redis):
   - defaults/main.yml (redis_host, redis_url)
5. Update Component 5 (orchestrator_qdrant):
   - defaults/main.yml (qdrant_url, ollama_url)
6. Update qdrant_web_ui:
   - defaults/main.yml (backend_host)
7. Update legacy fastapi role:
   - templates/orchestrator.env.j2 (defaults)

**Estimated Time**: 30 minutes

---

### Phase 2: Template Examples (During Component 6)
**Priority**: MEDIUM  
**Timeline**: Next week

1. Update fastmcp_server templates (comments and examples)
2. Update orchestrator_redis API examples (docstrings)

**Estimated Time**: 15 minutes

---

### Phase 3: Documentation (When convenient)
**Priority**: LOW  
**Timeline**: As time permits

1. Update redis_role README examples
2. Update postgresql_role README examples

**Estimated Time**: 15 minutes

---

## Testing Strategy

### After Phase 1 Fixes:

1. **Re-run FQDN checker**:
   ```bash
   bash scripts/check-fqdn.sh roles/
   ```
   Expected: Only Medium/Low priority violations remain

2. **Test Component 5 deployment**:
   ```bash
   ansible-playbook playbooks/deploy-orchestrator-qdrant.yml --check
   ```
   Expected: No template errors

3. **Verify service still works**:
   ```bash
   curl http://192.168.10.8:8000/health
   ```
   Expected: 200 OK

4. **Install pre-commit hook**:
   ```bash
   pipx install pre-commit
   pre-commit install --hook-type pre-commit --hook-type pre-push
   ```

---

## Allowlist Status

Created `.fqdn-allowlist` with patterns for:
- README documentation examples
- Health check scripts (localhost pings)
- Qdrant Web UI localhost validation
- PostgreSQL role templated defaults
- Redis role bind interface defaults

**Current violations**: 35 (down from 57 raw matches)

---

## Next Steps

1. **Approve** this remediation plan
2. **Execute** Phase 1 fixes (30 minutes)
3. **Test** updated roles
4. **Enable** pre-commit hook
5. **Proceed** with Component 6 deployment

---

**Report Generated**: October 10, 2025  
**Generated By**: GitHub Copilot + FQDN Policy Enforcer  
**Scan Command**: `bash scripts/check-fqdn.sh roles/`
