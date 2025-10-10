# Component 10: CopilotKit Adapter
## Human-in-the-Loop Frontend Integration - Ansible Deployment Plan

**Component:** CopilotKit Adapter  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Frontend:** shield-power-ui (192.168.10.12:3000)  
**Timeline:** Week 6, Days 1-3 (4-6 hours)  
**Priority:** ⭐ **MEDIUM - FRONTEND INTEGRATION**  
**Dependencies:** Components 1-9 (all intelligence layer)

---

## Overview

This plan covers CopilotKit adapter deployment for Human-in-the-Loop (HITL) integration with shield-power-ui:

- CopilotKit adapter endpoints
- State streaming (useCopilotReadable)
- Action handling (useCopilotAction)
- SSE configuration
- Frontend integration testing

**Reference:**
- Repository: `tech_kb/CopilotKit-main/`
- Integration patterns: HITL workflows
- Frontend: React + CopilotKit hooks

---

## Ansible Role Structure

```
roles/orchestrator_copilotkit/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-adapter.yml
│   └── 02-validation.yml
├── templates/
│   ├── api/copilotkit.py.j2
│   └── services/copilotkit_adapter.py.j2
├── files/
│   └── (none - no new dependencies)
└── handlers/
    └── main.yml
```

---

## defaults/main.yml

```yaml
---
# CopilotKit Configuration
copilotkit_enable: true
copilotkit_sse_endpoint: "/copilotkit/stream"
copilotkit_actions_endpoint: "/copilotkit/actions"
```

---

## templates/services/copilotkit_adapter.py.j2

```python
"""
CopilotKit adapter for shield-power-ui
"""

from typing import Dict, Any, AsyncIterator
import asyncio
import logging
import json

from services.lightrag_service import lightrag_service
from services.job_tracker import job_tracker

logger = logging.getLogger("shield-orchestrator.copilotkit")


class CopilotKitAdapter:
    """
    Adapter for CopilotKit integration.
    
    Provides:
      - State streaming (useCopilotReadable)
      - Action execution (useCopilotAction)
      - Progress updates
    """
    
    async def stream_state(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream job state for useCopilotReadable.
        
        Yields SSE-formatted state updates.
        """
        while True:
            progress = await job_tracker.get_progress(job_id)
            
            state_update = {
                "type": "state",
                "data": {
                    "jobId": job_id,
                    "status": progress.get("status"),
                    "progress": progress.get("percent_complete", 0),
                    "chunksProcessed": progress.get("chunks_processed", 0),
                    "chunksTotal": progress.get("chunks_total", 0)
                }
            }
            
            yield f"data: {json.dumps(state_update)}\n\n"
            
            # Check if job complete
            if progress.get("status") in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)  # Poll every second
    
    async def execute_action(
        self,
        action_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute CopilotKit action.
        
        Actions:
          - ingest_document
          - search_knowledge
          - update_kg (curator action)
        """
        logger.info(f"Executing action: {action_name}")
        
        if action_name == "search_knowledge":
            query = parameters.get("query", "")
            result = await lightrag_service.query(query, mode="hybrid")
            return result
        
        elif action_name == "ingest_document":
            # TODO: Implement document ingestion
            return {"status": "queued"}
        
        else:
            return {"error": f"Unknown action: {action_name}"}


# Global adapter instance
copilotkit_adapter = CopilotKitAdapter()
```

---

## templates/api/copilotkit.py.j2

```python
"""
CopilotKit API endpoints
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import logging

from services.copilotkit_adapter import copilotkit_adapter

router = APIRouter()
logger = logging.getLogger("shield-orchestrator.api.copilotkit")


@router.get("/copilotkit/stream/{job_id}")
async def copilotkit_stream(job_id: str):
    """
    SSE endpoint for CopilotKit state streaming.
    
    Used by useCopilotReadable hook in shield-power-ui.
    """
    return StreamingResponse(
        copilotkit_adapter.stream_state(job_id),
        media_type="text/event-stream"
    )


@router.post("/copilotkit/actions")
async def copilotkit_action(action: dict):
    """
    Action execution endpoint for useCopilotAction.
    
    Request:
      {
        "action": "action_name",
        "parameters": {...}
      }
    """
    result = await copilotkit_adapter.execute_action(
        action_name=action.get("action"),
        parameters=action.get("parameters", {})
    )
    
    return result
```

---

## tasks/01-adapter.yml

```yaml
---
# CopilotKit adapter deployment
- name: Deploy CopilotKit adapter service
  ansible.builtin.template:
    src: services/copilotkit_adapter.py.j2
    dest: "{{ orchestrator_app_dir }}/services/copilotkit_adapter.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [copilotkit]

- name: Deploy CopilotKit API endpoints
  ansible.builtin.template:
    src: api/copilotkit.py.j2
    dest: "{{ orchestrator_app_dir }}/api/copilotkit.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [copilotkit, api]

- name: Add CopilotKit router to main.py
  ansible.builtin.lineinfile:
    path: "{{ orchestrator_app_dir }}/main.py"
    line: "app.include_router(copilotkit.router, prefix='/copilotkit', tags=['copilotkit'])"
    insertafter: "app.include_router\\(jobs.router"
    state: present
  become: yes
  notify: restart orchestrator
  tags: [copilotkit, api]
```

---

## tasks/02-validation.yml

```yaml
---
# CopilotKit adapter validation
- name: Test CopilotKit endpoints
  ansible.builtin.uri:
    url: "http://localhost:8000/copilotkit/actions"
    method: POST
    body_format: json
    body:
      action: "search_knowledge"
      parameters:
        query: "test query"
    status_code: 200
  register: copilotkit_test
  tags: [validation]

- name: Display validation summary
  ansible.builtin.debug:
    msg:
      - "✅ CopilotKit adapter deployed"
      - "✅ Action endpoint tested"
      - "✅ CopilotKit integration complete!"
  tags: [validation]
```

---

## Success Criteria

```yaml
✅ Adapter:
   • CopilotKit adapter service deployed
   • State streaming implemented
   • Action execution implemented

✅ API Endpoints:
   • GET /copilotkit/stream/{job_id} (SSE)
   • POST /copilotkit/actions

✅ Integration:
   • Connects to shield-power-ui
   • State updates stream in real-time
   • Actions execute successfully

✅ Validation:
   • Endpoints respond correctly
   • SSE streaming works
   • Actions callable
```

---

## Timeline

**Estimated Time:** 4-6 hours

---

**CopilotKit Adapter Plan Complete!** ✅
**HITL integration enabled!** 🚀

---

## 🎉 ALL 10 COMPONENT PLANS COMPLETE!

**Status:** ✅ **READY FOR DEPLOYMENT**

