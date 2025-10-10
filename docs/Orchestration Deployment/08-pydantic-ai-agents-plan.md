# Component 8: Pydantic AI Agents
## Type-Safe Agent Definitions - Ansible Deployment Plan

**Component:** Pydantic AI Agents  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Timeline:** Week 5, Days 1-3 (6-8 hours)  
**Priority:** ⭐ **HIGH - INTELLIGENCE LAYER**  
**Dependencies:** Components 1-7 (especially LightRAG and Worker Pool)

---

## Overview

This plan covers Pydantic AI agent deployment for type-safe agent definitions and coordination:

- Web crawl coordinator agent
- Document process coordinator agent
- Query router agent
- Agent dependencies configuration
- Integration with LightRAG and LangGraph
- Agent testing

**Reference:** Existing implementation in `source/rag_agent.py`

---

## Ansible Role Structure

```
roles/orchestrator_agents/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-dependencies.yml
│   ├── 02-agent-definitions.yml
│   └── 03-validation.yml
├── templates/
│   ├── agents/web_crawl_coordinator.py.j2
│   ├── agents/doc_process_coordinator.py.j2
│   └── agents/query_router.py.j2
├── files/
│   └── requirements-pydantic-ai.txt
└── handlers/
    └── main.yml
```

---

## files/requirements-pydantic-ai.txt

```
# Pydantic AI Dependencies
# Component 8: Pydantic AI Agents

# Pydantic AI framework
# NOTE: Package name uses underscore, not hyphen
# Validated from: source/rag_agent.py (lines 12-13)
pydantic_ai

# Already installed, but ensure compatibility
pydantic>=2.0.0
httpx>=0.28.1
openai>=1.0.0  # For OpenAI-compatible LLM
```

---

## templates/agents/web_crawl_coordinator.py.j2

```python
"""
Web Crawl Coordinator Agent (Pydantic AI)
"""

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

logger = logging.getLogger("shield-orchestrator.agents.web-crawl")


class CrawlDeps(BaseModel):
    """Dependencies for crawl agent"""
    allowed_domains: List[str]
    max_pages: int
    max_depth: int


class CrawlResult(BaseModel):
    """Crawl result model"""
    pages_crawled: int
    chunks_extracted: int
    domains_visited: List[str]
    errors: List[str] = []


# Define web crawl coordinator agent
web_crawl_agent = Agent(
    model="openai:llama3.2:latest",
    result_type=CrawlResult,
    system_prompt="""
    You are the Web Crawl Coordinator for the Shield platform.
    
    Your responsibilities:
    - Validate crawl requests (domain allowlist, depth limits)
    - Coordinate Crawl4AI tool execution
    - Monitor crawl progress
    - Handle errors gracefully
    - Extract and chunk content for LightRAG processing
    
    Always prioritize:
    1. Respect robots.txt
    2. Stay within allowed domains
    3. Limit crawl depth to prevent infinite loops
    4. Extract clean, LLM-ready content
    """,
)


@web_crawl_agent.tool
async def validate_crawl_request(
    ctx: RunContext[CrawlDeps],
    url: str
) -> str:
    """Validate crawl request against policies"""
    from urllib.parse import urlparse
    
    domain = urlparse(url).netloc
    
    if domain not in ctx.deps.allowed_domains:
        return f"❌ Domain {domain} not in allowlist: {ctx.deps.allowed_domains}"
    
    return f"✅ Domain {domain} approved for crawling"


@web_crawl_agent.tool
async def execute_crawl(
    ctx: RunContext[CrawlDeps],
    url: str
) -> Dict[str, Any]:
    """Execute crawl via Crawl4AI"""
    # TODO: Call FastMCP crawl_web tool
    # For now, return mock result
    
    return {
        "status": "success",
        "pages_crawled": 0,
        "chunks_extracted": 0
    }


async def coordinate_web_crawl(
    url: str,
    allowed_domains: List[str],
    max_pages: int = 10,
    max_depth: int = 2
) -> CrawlResult:
    """
    Coordinate web crawl operation.
    
    Uses Pydantic AI agent to validate and execute crawl.
    """
    deps = CrawlDeps(
        allowed_domains=allowed_domains,
        max_pages=max_pages,
        max_depth=max_depth
    )
    
    prompt = f"""
    Coordinate a web crawl:
    - URL: {url}
    - Allowed domains: {allowed_domains}
    - Max pages: {max_pages}
    - Max depth: {max_depth}
    
    Validate the request and execute the crawl.
    """
    
    result = await web_crawl_agent.run(prompt, deps=deps)
    return result.data
```

---

## templates/agents/query_router.py.j2

```python
"""
Query Router Agent (Pydantic AI)
"""

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import Literal
import logging

logger = logging.getLogger("shield-orchestrator.agents.query-router")


class QueryRoutingDecision(BaseModel):
    """Query routing decision"""
    path: Literal["fast", "deep"]
    mode: Literal["hybrid", "kg", "vector"]
    reason: str
    confidence: float  # 0-1


# Define query router agent
query_router_agent = Agent(
    model="openai:llama3.2:latest",
    result_type=QueryRoutingDecision,
    system_prompt="""
    You are the Query Router for the Shield platform.
    
    Your responsibilities:
    - Analyze incoming queries
    - Decide optimal retrieval path:
      * Fast Path: Direct Qdrant (simple queries, low latency)
      * Deep Path: LightRAG hybrid (complex queries, best quality)
    - Select retrieval mode:
      * hybrid: KG + Vector (best for complex questions)
      * kg: Knowledge Graph only (relationships, connections)
      * vector: Vector only (semantic similarity)
    
    Decision criteria:
    - Query complexity (simple vs. complex)
    - Relationship requirements (needs KG?)
    - Latency requirements (real-time vs. batch)
    - Context requirements (shallow vs. deep)
    """,
)


async def route_query(query: str) -> QueryRoutingDecision:
    """
    Route query to optimal retrieval path.
    
    Args:
        query: User query
    
    Returns:
        Routing decision (fast/deep, hybrid/kg/vector)
    """
    prompt = f"""
    Analyze this query and decide the optimal retrieval strategy:
    
    Query: "{query}"
    
    Consider:
    - Is this a simple factual lookup or complex reasoning?
    - Does it require relationship traversal (KG)?
    - Does it need semantic similarity (vector)?
    - What's the latency requirement?
    """
    
    result = await query_router_agent.run(prompt)
    
    logger.info(f"Query routed to {result.data.path} path (mode: {result.data.mode})")
    return result.data
```

---

## tasks/02-agent-definitions.yml

```yaml
---
# Deploy agent definitions
- name: Deploy web crawl coordinator agent
  ansible.builtin.template:
    src: agents/web_crawl_coordinator.py.j2
    dest: "{{ orchestrator_app_dir }}/agents/web_crawl_coordinator.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [agents]

- name: Deploy document process coordinator agent
  ansible.builtin.template:
    src: agents/doc_process_coordinator.py.j2
    dest: "{{ orchestrator_app_dir }}/agents/doc_process_coordinator.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [agents]

- name: Deploy query router agent
  ansible.builtin.template:
    src: agents/query_router.py.j2
    dest: "{{ orchestrator_app_dir }}/agents/query_router.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [agents]

- name: Test agent imports
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import sys; sys.path.insert(0, "{{ orchestrator_app_dir }}"); 
    from agents.web_crawl_coordinator import web_crawl_agent;
    from agents.query_router import query_router_agent;
    print("Agents imported successfully")'
  register: agents_import_test
  changed_when: false
  tags: [agents, validation]
```

---

## Success Criteria

```yaml
✅ Dependencies:
   • pydantic-ai installed
   • Compatible with pydantic >=2.0.0

✅ Agents Defined:
   • web_crawl_coordinator.py
   • doc_process_coordinator.py
   • query_router.py

✅ Agent Features:
   • Type-safe (Pydantic models)
   • Tool definitions
   • System prompts
   • Dependencies (RunContext)

✅ Integration:
   • Agents can call LightRAG
   • Agents can emit events
   • Agents importable

✅ Validation:
   • All agents import successfully
   • Agent tools callable
   • Type checking passes
```

---

## Timeline

**Estimated Time:** 6-8 hours

```yaml
Day 1 (3 hours):
  • Dependencies: 30 minutes
  • Web crawl agent: 1 hour
  • Query router agent: 1 hour
  • Testing: 30 minutes

Day 2 (3 hours):
  • Doc process agent: 1 hour
  • Integration testing: 1.5 hours
  • Validation: 30 minutes

Day 3 (2 hours):
  • Documentation: 1 hour
  • Buffer: 1 hour

Total: 8 hours
```

---

## Next Component

**After Pydantic AI agents are defined, proceed to:**

→ **Component 9: LangGraph Workflows** (`09-langgraph-workflows-plan.md`)

---

**Pydantic AI Agents Plan Complete!** ✅
**Type-safe intelligence!** 🚀

