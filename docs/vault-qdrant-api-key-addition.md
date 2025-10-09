# Qdrant API Key Vault Addition

**Date:** 2025-01-07  
**Task:** Add `vault_qdrant_api_key` to `group_vars/all/vault.yml`  
**Purpose:** Centralize Qdrant API key for use across MCP Server and Qdrant Web UI deployments

---

## Current State

The Qdrant API key is currently hardcoded in `playbooks/deploy-qdrant-ui.yml`:
```yaml
qdrant_ui_backend_api_key: "9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09"
```

This needs to be migrated to Ansible Vault for security.

---

## Required Action

### Step 1: Edit the encrypted vault file

```bash
ansible-vault edit group_vars/all/vault.yml
```

**Vault Password:** `Major8859!`

### Step 2: Add the following variable

Add this line to the vault file (it will be automatically encrypted):

```yaml
vault_qdrant_api_key: "9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09"
```

### Step 3: Update playbooks to use the vault variable

**File:** `playbooks/deploy-qdrant-ui.yml`

**Change from:**
```yaml
qdrant_ui_backend_api_key: "9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09"
```

**Change to:**
```yaml
qdrant_ui_backend_api_key: "{{ vault_qdrant_api_key }}"
```

---

## Usage in MCP Server Deployment

The MCP server deployment plan already references this vault variable:

**File:** `docs/mcp-server-deployment-plan.md` (Section 2.2)

```yaml
# roles/fastmcp_server/defaults/main.yml
qdrant_api_key: "{{ vault_qdrant_api_key }}"
```

This ensures:
- ✅ Secure API key storage
- ✅ Centralized management
- ✅ Consistent access across all services
- ✅ No hardcoded secrets in playbooks

---

## Verification

After adding to vault, verify the variable is accessible:

```bash
# View vault contents (requires password)
ansible-vault view group_vars/all/vault.yml

# Test variable in playbook
ansible-playbook playbooks/deploy-qdrant-ui.yml --check --ask-vault-pass
```

---

## Security Benefits

1. **Encrypted at Rest:** API key stored encrypted in Git repository
2. **Access Control:** Requires vault password to decrypt
3. **Single Source of Truth:** One variable for all Qdrant API access
4. **Audit Trail:** Git history tracks vault changes
5. **No Plaintext Leaks:** Removes hardcoded secrets from playbooks

---

## Related Files

- `group_vars/all/vault.yml` - Encrypted vault file (add variable here)
- `playbooks/deploy-qdrant-ui.yml` - Update to use vault variable
- `docs/mcp-server-deployment-plan.md` - Already references vault variable
- `configuration/qdrant_ui_config_2025-10-07.md` - Documents this migration need

---

## Manual Execution Command

```bash
# One-liner to add to vault (interactive)
echo "vault_qdrant_api_key: \"9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09\"" | \
ansible-vault encrypt_string --stdin-name 'vault_qdrant_api_key' --vault-password-file <(echo "Major8859!")

# Then manually add output to group_vars/all/vault.yml
```

Or edit directly:
```bash
ANSIBLE_VAULT_PASSWORD_FILE=<(echo "Major8859!") ansible-vault edit group_vars/all/vault.yml
```

---

## Post-Migration Checklist

- [ ] Variable added to `group_vars/all/vault.yml`
- [ ] `playbooks/deploy-qdrant-ui.yml` updated to use `{{ vault_qdrant_api_key }}`
- [ ] Tested Qdrant Web UI deployment with vault variable
- [ ] Tested MCP server deployment with vault variable
- [ ] Verified API key works with Qdrant backend (192.168.10.9:6333)
- [ ] Removed hardcoded API key from all playbooks
- [ ] Documented change in git commit message

---

## Example Vault Structure (After Addition)

```yaml
# group_vars/all/vault.yml (unencrypted view)
---
# Existing vault variables
vault_existing_var_1: "value1"
vault_existing_var_2: "value2"

# Qdrant API Key (added 2025-01-07)
vault_qdrant_api_key: "9381d692ff19c9eace23c8a3a73ffc551fab5281a1e75e10db599cc148558d09"

# Other vault variables
vault_other_var: "value3"
```

**Note:** The actual file remains encrypted when stored in Git.

---

**Status:** ✅ Documentation Complete - Manual execution required (vault password needed)
