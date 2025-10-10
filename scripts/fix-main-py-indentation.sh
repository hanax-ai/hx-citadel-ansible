#!/bin/bash
# Fix main.py indentation for agent_manager and workflow_manager

MAIN_PY="/opt/hx-citadel-shield/orchestrator/main.py"

# Remove all Ansible managed blocks first
sed -i '/# BEGIN ANSIBLE MANAGED BLOCK/,/# END ANSIBLE MANAGED BLOCK/d' "$MAIN_PY"

# Check and add agent_manager import if missing
if ! grep -q "from services.agent_manager import agent_manager" "$MAIN_PY"; then
    sed -i '/from services.event_bus import/a\from services.agent_manager import agent_manager' "$MAIN_PY"
    echo "Added agent_manager import"
fi

# Check and add workflow_manager import if missing
if ! grep -q "from services.workflow_manager import workflow_manager" "$MAIN_PY"; then
    sed -i '/from services.event_bus import/a\from services.workflow_manager import workflow_manager' "$MAIN_PY"
    echo "Added workflow_manager import"
fi

# Add initialization after init_event_bus (with proper indentation)
if ! grep -q "await agent_manager.initialize()" "$MAIN_PY"; then
    sed -i '/await init_event_bus()/a\    await agent_manager.initialize()\n    await workflow_manager.initialize()\n    logger.info("✅ Agents and workflows initialized")' "$MAIN_PY"
fi

# Add shutdown before close_event_bus (with proper indentation)
if ! grep -q "await workflow_manager.shutdown()" "$MAIN_PY"; then
    sed -i '/await close_event_bus()/i\    await workflow_manager.shutdown()\n    await agent_manager.shutdown()\n    logger.info("✅ Agents and workflows shut down")' "$MAIN_PY"
fi

echo "main.py fixed"

# Validate Python syntax
python3 -m py_compile "$MAIN_PY" && echo "✅ Syntax OK" || echo "❌ Syntax Error"
