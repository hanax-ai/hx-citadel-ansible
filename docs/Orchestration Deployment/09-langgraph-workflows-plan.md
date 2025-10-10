# Component 9: LangGraph Workflows
## Multi-Step Agent Coordination - Ansible Deployment Plan

**Component:** LangGraph Workflows  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Timeline:** Week 5, Days 4-7 (6-8 hours)  
**Priority:** ⭐ **HIGH - INTELLIGENCE LAYER**  
**Dependencies:** Component 8 (Pydantic AI Agents)

---

## Overview

This plan covers LangGraph workflow deployment for multi-step agent coordination:

- Ingestion workflow (multi-step processing)
- Query workflow (routing and retrieval)
- State management (Redis checkpoints)
- Workflow testing
- Integration with Pydantic AI agents

**Reference:**
- Repository: `tech_kb/langgraph-main/` (563 MB, 23+ examples)
- Examples: `tech_kb/langgraph-example-main/`
- Integration: `tech_kb/ottomator-agents-main/pydantic-ai-langgraph-parallelization/`

---

## Ansible Role Structure

```
roles/orchestrator_langgraph/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-dependencies.yml
│   ├── 02-workflows.yml
│   └── 03-validation.yml
├── templates/
│   ├── workflows/ingestion_workflow.py.j2
│   └── workflows/query_workflow.py.j2
├── files/
│   └── requirements-langgraph.txt
└── handlers/
    └── main.yml
```

---

## files/requirements-langgraph.txt

```
# LangGraph Dependencies
# Component 9: LangGraph Workflows

# LangGraph framework
langgraph>=0.2.0

# LangChain dependencies
langchain-core>=0.3.0
langchain-community>=0.3.0
langchain-openai>=0.2.0

# Already installed, ensure compatibility
pydantic>=2.0.0
```

---

## defaults/main.yml

```yaml
---
# LangGraph Configuration
langgraph_checkpoint_backend: "redis"
langgraph_checkpoint_db: 1
langgraph_state_retention_hours: 72

# Workflow configuration
workflow_max_iterations: 10
workflow_timeout_seconds: 300
```

---

## templates/workflows/ingestion_workflow.py.j2

```python
"""
Ingestion Workflow (LangGraph)
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
import logging

from agents.web_crawl_coordinator import coordinate_web_crawl
from agents.doc_process_coordinator import coordinate_doc_processing
from services.lightrag_service import lightrag_service

logger = logging.getLogger("shield-orchestrator.workflows.ingestion")


class IngestionState(TypedDict):
    """State for ingestion workflow"""
    job_id: str
    source_type: str  # web or document
    source_uri: str
    chunks: List[str]
    entities_extracted: int
    relationships_extracted: int
    status: str
    error: str | None


def should_process_more(state: IngestionState) -> str:
    """Decide if more processing needed"""
    if state["status"] == "failed":
        return END
    if state["chunks"]:
        return "process_chunk"
    return END


def create_ingestion_workflow():
    """
    Create ingestion workflow graph.
    
    Steps:
      1. Validate source
      2. Extract content (crawl or parse)
      3. Chunk content
      4. Process chunks (loop)
      5. Update Knowledge Graph
      6. Emit completion event
    """
    workflow = StateGraph(IngestionState)
    
    # Define nodes
    workflow.add_node("validate", validate_source)
    workflow.add_node("extract", extract_content)
    workflow.add_node("chunk", chunk_content)
    workflow.add_node("process_chunk", process_single_chunk)
    workflow.add_node("finalize", finalize_ingestion)
    
    # Define edges
    workflow.set_entry_point("validate")
    workflow.add_edge("validate", "extract")
    workflow.add_edge("extract", "chunk")
    workflow.add_edge("chunk", "process_chunk")
    workflow.add_conditional_edges(
        "process_chunk",
        should_process_more,
        {
            "process_chunk": "process_chunk",
            END: "finalize"
        }
    )
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


async def validate_source(state: IngestionState) -> IngestionState:
    """Validate source URI and permissions"""
    logger.info(f"Validating source: {state['source_uri']}")
    
    # TODO: Add validation logic
    state["status"] = "validated"
    return state


async def extract_content(state: IngestionState) -> IngestionState:
    """Extract content from source"""
    logger.info(f"Extracting content from {state['source_type']}")
    
    if state["source_type"] == "web":
        # Coordinate web crawl
        result = await coordinate_web_crawl(
            url=state["source_uri"],
            allowed_domains=[],  # TODO: Get from state
            max_pages=10
        )
        # TODO: Extract pages to chunks
    
    state["status"] = "extracted"
    return state


async def chunk_content(state: IngestionState) -> IngestionState:
    """Chunk extracted content"""
    logger.info("Chunking content...")
    
    # TODO: Chunking logic
    state["chunks"] = []  # Placeholder
    state["status"] = "chunked"
    return state


async def process_single_chunk(state: IngestionState) -> IngestionState:
    """Process one chunk through LightRAG"""
    if state["chunks"]:
        chunk = state["chunks"].pop(0)
        
        # Process through LightRAG
        result = await lightrag_service.insert_text(chunk)
        
        state["entities_extracted"] += result.get("entities_extracted", 0)
        state["relationships_extracted"] += result.get("relationships_extracted", 0)
    
    return state


async def finalize_ingestion(state: IngestionState) -> IngestionState:
    """Finalize ingestion"""
    logger.info(f"Ingestion complete: {state['entities_extracted']} entities, {state['relationships_extracted']} relationships")
    state["status"] = "completed"
    return state


# Create workflow instance
ingestion_workflow = create_ingestion_workflow()
```

---

## templates/workflows/query_workflow.py.j2

```python
"""
Query Workflow (LangGraph)
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
import logging

from agents.query_router import route_query
from services.lightrag_service import lightrag_service
from services.qdrant_client import qdrant_service
from services.embeddings import embedding_service

logger = logging.getLogger("shield-orchestrator.workflows.query")


class QueryState(TypedDict):
    """State for query workflow"""
    query: str
    path: str  # fast or deep
    mode: str  # hybrid, kg, vector
    results: List[Dict[str, Any]]
    answer: str
    metadata: Dict[str, Any]


def create_query_workflow():
    """
    Create query workflow graph.
    
    Steps:
      1. Route query (fast vs. deep path)
      2a. Fast path: Direct Qdrant search
      2b. Deep path: LightRAG hybrid retrieval
      3. Generate answer
      4. Return results
    """
    workflow = StateGraph(QueryState)
    
    # Define nodes
    workflow.add_node("route", route_query_node)
    workflow.add_node("fast_path", fast_path_search)
    workflow.add_node("deep_path", deep_path_search)
    workflow.add_node("generate_answer", generate_answer_node)
    
    # Define edges
    workflow.set_entry_point("route")
    workflow.add_conditional_edges(
        "route",
        lambda state: state["path"],
        {
            "fast": "fast_path",
            "deep": "deep_path"
        }
    )
    workflow.add_edge("fast_path", "generate_answer")
    workflow.add_edge("deep_path", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    return workflow.compile()


async def route_query_node(state: QueryState) -> QueryState:
    """Route query to fast or deep path"""
    decision = await route_query(state["query"])
    
    state["path"] = decision.path
    state["mode"] = decision.mode
    state["metadata"]["routing_reason"] = decision.reason
    state["metadata"]["routing_confidence"] = decision.confidence
    
    logger.info(f"Query routed to {decision.path} path (mode: {decision.mode})")
    return state


async def fast_path_search(state: QueryState) -> QueryState:
    """Fast path: Direct Qdrant search"""
    logger.info("Executing fast path (direct Qdrant)")
    
    # Get query embedding
    embedding = await embedding_service.get_embedding(state["query"])
    
    # Search Qdrant
    results = await qdrant_service.search(
        query_vector=embedding,
        limit=10
    )
    
    state["results"] = results
    state["metadata"]["path_used"] = "fast"
    return state


async def deep_path_search(state: QueryState) -> QueryState:
    """Deep path: LightRAG hybrid retrieval"""
    logger.info(f"Executing deep path (LightRAG {state['mode']})")
    
    # Query via LightRAG
    result = await lightrag_service.query(
        query=state["query"],
        mode=state["mode"]
    )
    
    state["answer"] = result["answer"]
    state["metadata"]["path_used"] = "deep"
    state["metadata"]["retrieval_mode"] = state["mode"]
    return state


async def generate_answer_node(state: QueryState) -> QueryState:
    """Generate final answer (if not from deep path)"""
    if state["path"] == "fast":
        # Fast path needs answer generation
        # TODO: Use LLM to generate answer from results
        state["answer"] = f"Fast path results: {len(state['results'])} chunks found"
    
    return state


# Create workflow instance
query_workflow = create_query_workflow()
```

---

## tasks/01-dependencies.yml

```yaml
---
# LangGraph dependencies installation
- name: Copy LangGraph requirements
  ansible.builtin.copy:
    src: requirements-langgraph.txt
    dest: "{{ orchestrator_app_dir }}/requirements-langgraph.txt"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes

- name: Install LangGraph and dependencies
  ansible.builtin.pip:
    requirements: "{{ orchestrator_app_dir }}/requirements-langgraph.txt"
    virtualenv: "{{ orchestrator_venv_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  notify: restart orchestrator
  tags: [dependencies]

- name: Verify LangGraph installation
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import langgraph; print(f"LangGraph installed")'
  register: langgraph_check
  changed_when: false
  tags: [dependencies, validation]
```

---

## tasks/02-workflows.yml

```yaml
---
# Deploy workflow definitions
- name: Deploy ingestion workflow
  ansible.builtin.template:
    src: workflows/ingestion_workflow.py.j2
    dest: "{{ orchestrator_app_dir }}/workflows/ingestion_workflow.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [workflows]

- name: Deploy query workflow
  ansible.builtin.template:
    src: workflows/query_workflow.py.j2
    dest: "{{ orchestrator_app_dir }}/workflows/query_workflow.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [workflows]

- name: Test workflow imports
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import sys; sys.path.insert(0, "{{ orchestrator_app_dir }}"); 
    from workflows.ingestion_workflow import ingestion_workflow;
    from workflows.query_workflow import query_workflow;
    print("Workflows imported")'
  register: workflow_import_test
  changed_when: false
  tags: [workflows, validation]
```

---

## Success Criteria

```yaml
✅ Dependencies:
   • langgraph >=0.2.0 installed
   • langchain-core installed
   • langchain-community installed

✅ Workflows:
   • ingestion_workflow.py deployed
   • query_workflow.py deployed
   • State graphs defined
   • Checkpoints configured (Redis)

✅ Integration:
   • Workflows can call Pydantic AI agents
   • Workflows can call LightRAG
   • State persisted in Redis

✅ Validation:
   • Workflows importable
   • State graphs compilable
   • Test execution passes
```

---

## Timeline

**Estimated Time:** 6-8 hours

---

## Next Component

**After LangGraph workflows, proceed to:**

→ **Component 10: CopilotKit Adapter** (`10-copilotkit-adapter-plan.md`)

---

**LangGraph Workflows Plan Complete!** ✅
**Multi-step coordination enabled!** 🚀

