#!/bin/bash
# Quick Vault Update Helper

echo "=== Ansible Vault Update Helper ==="
echo ""
echo "Your new vault is encrypted but the password file doesn't match."
echo ""
echo "Choose your action:"
echo "1. Update vault password file and edit vault"
echo "2. View vault template for reference"
echo "3. Replace vault with template and start fresh"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        read -sp "Enter your NEW vault password: " VAULT_PASS
        echo ""
        echo "$VAULT_PASS" > ~/.ansible_vault_pass
        chmod 600 ~/.ansible_vault_pass
        echo "✓ Vault password updated"
        echo ""
        echo "Opening vault for editing..."
        ansible-vault edit group_vars/all/vault.yml
        ;;
    2)
        echo ""
        echo "=== Vault Template Reference ==="
        cat group_vars/all/vault_template.yml
        echo ""
        echo "Run this script again to edit your vault."
        ;;
    3)
        echo ""
        read -sp "Enter password for NEW vault: " NEW_PASS
        echo ""
        echo "$NEW_PASS" > ~/.ansible_vault_pass
        chmod 600 ~/.ansible_vault_pass
        
        # Backup old vault
        mv group_vars/all/vault.yml group_vars/all/vault.yml.backup_$(date +%Y%m%d_%H%M%S)
        
        # Copy template and encrypt
        cp group_vars/all/vault_template.yml group_vars/all/vault.yml
        echo "✓ Template copied"
        echo ""
        echo "Now edit the vault with your values:"
        ansible-vault encrypt group_vars/all/vault.yml
        ansible-vault edit group_vars/all/vault.yml
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=== Testing vault access ==="
ansible-vault view group_vars/all/vault.yml | head -5
