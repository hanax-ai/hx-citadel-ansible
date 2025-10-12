#!/bin/bash
# Fix APT repository issues on failed servers

echo "=== Fixing APT Repository Issues ==="
echo ""

FAILED_SERVERS="hx-dc-server hx-vectordb-server hx-ollama2"

for server in $FAILED_SERVERS; do
    echo "[$server] Removing problematic Qdrant repository..."
    ansible $server -i inventory/prod.ini -m shell -a "sudo rm -f /etc/apt/sources.list.d/*qdrant*" -b 2>/dev/null || echo "  ✗ Failed"
    
    echo "[$server] Updating apt cache..."
    ansible $server -i inventory/prod.ini -m apt -a "update_cache=yes" -b 2>/dev/null && echo "  ✓ Success" || echo "  ✗ Failed"
    echo ""
done

echo "=== Testing connectivity ===" 
ansible $FAILED_SERVERS -i inventory/prod.ini -m ping --one-line
