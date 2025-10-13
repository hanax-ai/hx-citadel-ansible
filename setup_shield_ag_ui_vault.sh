#!/bin/bash
# 
# Setup Shield AG-UI Vault Variables
# Following PR #57 deployment checklist
#
# Usage: ./setup_shield_ag_ui_vault.sh

set -euo pipefail

echo "═══════════════════════════════════════════════════════════"
echo "   Shield AG-UI Vault Configuration"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Generate secrets
echo "Generating secure secrets..."
JWT_SECRET=$(openssl rand -base64 48)
DB_PASSWORD=$(openssl rand -base64 32)

echo ""
echo "Generated secrets:"
echo "  JWT Secret: ${JWT_SECRET:0:20}... (64 chars)"
echo "  DB Password: ${DB_PASSWORD:0:20}... (43 chars)"
echo ""

# Get LiteLLM API key (needs to be provided or retrieved)
echo "⚠️  LiteLLM API Key required"
echo "   Check your LiteLLM deployment or use placeholder for testing"
echo ""
read -p "Enter LiteLLM API Key (or press Enter for placeholder): " LITELLM_KEY
LITELLM_KEY=${LITELLM_KEY:-"sk-placeholder-replace-with-real-key"}

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   Adding to Ansible Vault"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Create secure temp file with new variables
SECURE_VAULT_VARS=$(mktemp --suffix=.yml)
chmod 600 "$SECURE_VAULT_VARS"

cat > "$SECURE_VAULT_VARS" << VAULT_VARS
# Shield AG-UI Vault Variables (added $(date))
vault_shield_ag_ui_jwt_secret: "${JWT_SECRET}"
vault_shield_ag_ui_litellm_api_key: "${LITELLM_KEY}"
vault_shield_ag_ui_db_password: "${DB_PASSWORD}"
VAULT_VARS

echo "Variables to add:"
cat "$SECURE_VAULT_VARS"
echo ""

echo "Next steps:"
echo "1. Get vault password: op read op://Infra/HX-Citadel-Ansible/VaultPassword/password > /tmp/.vault-pass"
echo "2. Edit vault: ansible-vault edit group_vars/all/vault.yml --vault-password-file /tmp/.vault-pass"
echo "3. Append contents from: $SECURE_VAULT_VARS"
echo "4. Save and exit"
echo "5. Clean up: shred -u /tmp/.vault-pass $SECURE_VAULT_VARS"
echo ""
echo "Or run this automated command:"
echo "ansible-vault decrypt group_vars/all/vault.yml --vault-password-file /tmp/.vault-pass && \\"
echo "cat $SECURE_VAULT_VARS >> group_vars/all/vault.yml && \\"
echo "ansible-vault encrypt group_vars/all/vault.yml --vault-password-file /tmp/.vault-pass && \\"
echo "shred -u $SECURE_VAULT_VARS"

