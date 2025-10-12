#!/bin/bash
# Quick SSH key distribution to all fleet servers

echo "=== SSH Key Distribution to HX Fleet ==="
echo ""
echo "Your new public key:"
cat ~/.ssh/id_ed25519.pub
echo ""
echo "This will copy your SSH key to all 17 fleet servers."
echo ""

# Get password once
read -sp "Enter password for agent0 on remote servers: " PASSWORD
echo ""
echo ""

# List of all servers from inventory
SERVERS="hx-dc-server hx-ca-server hx-orchestrator-server hx-vectordb-server hx-webui-server hx-dev-server hx-test-server hx-devops-server hx-metrics-server hx-fs-server hx-litellm-server hx-prisma-server hx-sqldb-server hx-ollama1 hx-ollama2 hx-qwebui-server hx-mcp1-server"

SUCCESS=0
FAILED=0

for server in $SERVERS; do
    echo -n "Copying to $server... "
    if sshpass -p "$PASSWORD" ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.ssh/id_ed25519.pub agent0@$server >/dev/null 2>&1; then
        echo "✓ SUCCESS"
        ((SUCCESS++))
    else
        echo "✗ FAILED"
        ((FAILED++))
    fi
done

echo ""
echo "=== Summary ==="
echo "Success: $SUCCESS"
echo "Failed: $FAILED"
echo ""

if [ $SUCCESS -gt 0 ]; then
    echo "Testing Ansible connectivity..."
    ansible all -i inventory/prod.ini -m ping --one-line 2>&1 | head -20
fi
