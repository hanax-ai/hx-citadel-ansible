# Docker Installation & Configuration Plan - Dev Server

**Target**: hx-dev-server (192.168.10.12)  
**Purpose**: Prepare dev-server for Shield AG-UI deployment  
**Date**: October 13, 2025  
**Status**: Draft - Awaiting Approval

---

## Current State

**Preflight Check Results** (as of 2025-10-13 03:20 UTC):
- ✅ OS: Ubuntu 24.04
- ✅ Network connectivity: Orchestrator, Redis, LiteLLM all reachable
- ⚠️ Docker: Partially installed (docker.io installed, compose missing)
- ⚠️ Docker Compose: NOT INSTALLED (required for shield_ag_ui role)

**What was done already**:
- ✅ Installed docker.io package (version 28.2.2)
- ✅ Added agent0 to docker group
- ✅ Docker service enabled and started

**What's still needed**:
- ❌ Docker Compose V2 plugin
- ❌ Verify Docker daemon running
- ❌ Test Docker functionality
- ❌ Configure Docker for production use

---

## Installation Plan

### Phase 1: Docker Compose Installation

**Objective**: Install Docker Compose V2 plugin

**Method**: Official Docker Compose plugin installation

**Steps**:
1. Download Docker Compose plugin binary
   ```bash
   DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
   mkdir -p $DOCKER_CONFIG/cli-plugins
   curl -SL https://github.com/docker/compose/releases/download/v2.29.0/docker-compose-linux-x86_64 \
     -o $DOCKER_CONFIG/cli-plugins/docker-compose
   chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
   ```

2. Alternative: Install via apt (if available in Ubuntu 24.04)
   ```bash
   apt update
   apt install docker-compose-v2
   ```

**Verification**:
```bash
docker compose version
# Expected: Docker Compose version v2.29.0 or newer
```

**Estimated Time**: 5 minutes

---

### Phase 2: Docker Daemon Configuration

**Objective**: Configure Docker for production use

**Configuration File**: `/etc/docker/daemon.json`

**Settings**:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-address-pools": [
    {
      "base": "172.80.0.0/16",
      "size": 24
    }
  ],
  "live-restore": true,
  "userland-proxy": false,
  "icc": false,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

**Rationale**:
- **log-driver**: Prevent log file bloat
- **storage-driver**: overlay2 is recommended for Ubuntu
- **default-address-pools**: Avoid conflicts with existing network ranges
- **live-restore**: Keep containers running during daemon upgrades
- **userland-proxy**: Better performance
- **icc**: Disable inter-container communication by default (security)
- **default-ulimits**: Support for high-connection workloads

**Apply Configuration**:
```bash
systemctl restart docker
systemctl status docker
```

**Estimated Time**: 10 minutes

---

### Phase 3: User & Group Configuration

**Objective**: Ensure proper permissions

**Steps**:
1. ✅ Add agent0 to docker group (DONE)
2. Verify group membership: `groups agent0`
3. Note: User needs to log out/in or `newgrp docker` for group to take effect
4. Create agui user (if needed by shield_ag_ui role)

**Verification**:
```bash
# As agent0 (after re-login or newgrp)
docker ps
docker compose version
```

**Estimated Time**: 5 minutes (plus user re-login)

---

### Phase 4: Network Configuration

**Objective**: Create Docker networks for shield_ag_ui

**Networks Required** (from shield_ag_ui defaults):
- `ag-ui-network` (bridge network for containers)

**Steps**:
```bash
docker network create ag-ui-network --driver bridge
docker network ls | grep ag-ui
```

**Verification**:
```bash
docker network inspect ag-ui-network
```

**Note**: The shield_ag_ui role may create this automatically. Verify in role tasks before manual creation.

**Estimated Time**: 2 minutes

---

### Phase 5: Docker Service Validation

**Objective**: Verify Docker is fully operational

**Test Commands**:
```bash
# 1. Check Docker daemon
systemctl status docker

# 2. Test Docker functionality
docker run --rm hello-world

# 3. Test Docker Compose
docker compose version

# 4. Check disk space
df -h /var/lib/docker

# 5. Verify networking
docker network ls
```

**Expected Results**:
- ✅ Docker daemon: active (running)
- ✅ Hello-world: Pulls image and runs successfully
- ✅ Docker Compose: Shows version v2.x
- ✅ Disk space: >10GB available
- ✅ Networks: Default bridge, host, none networks present

**Estimated Time**: 5 minutes

---

## Implementation Approach

### Option A: Manual Installation (Ad-hoc Commands)
**Pros**: Quick, minimal changes to codebase  
**Cons**: Not reproducible, not documented in Ansible

**Steps**:
1. SSH to hx-dev-server
2. Run installation commands manually
3. Verify each step
4. Proceed to deployment

**Time**: 20-30 minutes

---

### Option B: Ansible Playbook (Recommended)
**Pros**: Reproducible, documented, automated  
**Cons**: Requires creating/modifying playbook

**Steps**:
1. Create `playbooks/setup-docker-dev-server.yml`
2. Include Docker Compose installation
3. Include daemon configuration
4. Run playbook
5. Verify

**Time**: 30-45 minutes (includes playbook creation)

---

### Option C: Extend shield_ag_ui Role Prerequisites
**Pros**: Self-contained, role handles all deps  
**Cons**: Modifies Devin's work

**Steps**:
1. Add Docker Compose installation to `roles/shield_ag_ui/tasks/01-prerequisites.yml`
2. Add daemon configuration task
3. Run full deployment playbook

**Time**: 15-20 minutes

---

## Recommendation

**Recommended Approach**: **Option B** (Ansible Playbook)

**Rationale**:
1. Follows infrastructure-as-code principles
2. Reproducible for other servers
3. Documented in version control
4. Doesn't modify Devin's tested role
5. Can be reused for test-server later

**Playbook Name**: `playbooks/setup-docker-dev-server.yml`

**Tasks**:
1. Install Docker (already done, skip if present)
2. Install Docker Compose V2
3. Configure Docker daemon
4. Add users to docker group
5. Restart Docker service
6. Verify installation

---

## Prerequisites Check

**Before Docker Installation**:
- [x] Server accessible via Ansible
- [x] Ubuntu 24.04 confirmed
- [x] Sufficient disk space (>10GB for Docker)
- [x] Network connectivity verified

**After Docker Installation**:
- [ ] Docker daemon running
- [ ] Docker Compose V2 installed
- [ ] agent0 in docker group
- [ ] Test container can run
- [ ] Networks can be created

---

## Post-Installation Validation

**Test Script**:
```bash
#!/bin/bash
# Docker installation validation

echo "1. Docker version:"
docker --version

echo ""
echo "2. Docker Compose version:"
docker compose version

echo ""
echo "3. Docker daemon status:"
systemctl status docker --no-pager | head -5

echo ""
echo "4. User groups:"
groups agent0

echo ""
echo "5. Docker info:"
docker info | grep -E "Server Version|Storage Driver|Logging Driver"

echo ""
echo "6. Test container:"
docker run --rm hello-world 2>&1 | grep "Hello from Docker"

echo ""
echo "7. Network test:"
docker network create test-network
docker network rm test-network
echo "Network create/delete: OK"
```

**Expected Output**:
- Docker: v28.2.2 or newer
- Compose: v2.29.0 or newer
- Daemon: active (running)
- Groups: agent0 adm cdrom sudo dip plugdev lxd docker
- Storage: overlay2
- Test: "Hello from Docker!"
- Network: OK

---

## Risk Assessment

**Low Risk**:
- Docker installation is standard Ubuntu package
- Docker Compose is official plugin
- Configuration is production-tested

**Medium Risk**:
- User group change requires logout/login or `newgrp docker`
- Docker daemon restart may affect existing containers (none expected on dev-server)

**Mitigation**:
- Verify no existing containers before daemon restart: `docker ps -a`
- Use `newgrp docker` to activate group without logout
- Keep backup of daemon.json before modifications

---

## Dependencies

**Before Shield AG-UI Deployment Can Proceed**:
1. ✅ Ansible Vault secrets (DONE - just configured)
2. ⏳ Docker installed (DONE - just installed)
3. ⏳ Docker Compose installed (PENDING)
4. ⏳ Docker daemon configured (PENDING)
5. ✅ Network connectivity (VERIFIED)

---

## Next Steps

**Immediate**:
1. Approve this plan
2. Choose implementation approach (A, B, or C)
3. Execute Docker Compose installation
4. Configure Docker daemon
5. Validate installation
6. Re-run preflight checks
7. Proceed with shield_ag_ui deployment

**After Docker Setup**:
1. Deploy Shield AG-UI role
2. Follow PR #57 testing checklist
3. Verify all services
4. Test end-to-end functionality

---

## Questions for Approval

1. **Which installation approach?** (Option A, B, or C)
2. **Docker daemon configuration?** Use recommended settings or custom?
3. **Additional users?** Should agui user be in docker group?
4. **Network pools?** Use 172.80.0.0/16 or different range?
5. **Storage driver?** overlay2 (recommended) or other?

---

**Awaiting approval to proceed** ✋


