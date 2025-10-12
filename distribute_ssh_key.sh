#!/bin/bash
# Distribute SSH key to all fleet servers

SERVERS=$(grep "ansible_host=" inventory/prod.ini | awk '{print $1}')
KEY_FILE=~/.ssh/id_ed25519.pub

echo "=== Distributing SSH Key to Fleet Servers ==="
echo "Public key: $(cat $KEY_FILE)"
echo ""
echo "Servers to configure:"
echo "$SERVERS" | nl
echo ""
read -p "Enter password for agent0 (or Ctrl+C to cancel): " -s PASSWORD
echo ""

for server in $SERVERS; do
    echo -n "[$server]: "
    sshpass -p "$PASSWORD" ssh-copy-id -o StrictHostKeyChecking=no -i $KEY_FILE agent0@$server 2>&1 | grep -v "Warning" | head -1
done

echo ""
echo "=== Testing connectivity ==="
ansible all -i inventory/prod.ini -m ping --one-line
