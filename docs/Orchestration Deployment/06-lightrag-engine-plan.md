# Component 6: LightRAG Engine
## Hybrid Knowledge Graph + Vector Retrieval - Ansible Deployment Plan

**Component:** LightRAG Engine ⭐ **MOST COMPLEX**  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Timeline:** Week 3, Days 1-7 (12-15 hours)  
**Priority:** ⭐⭐⭐ **CRITICAL - INTELLIGENCE CORE**  
**Dependencies:** Components 1-5 (ALL data layer must be operational)

---

## Overview

This is the **MOST COMPLEX** component, implementing the core intelligence of the Shield platform. LightRAG provides hybrid retrieval combining Knowledge Graph traversal with vector search for superior RAG quality.

**Key Features:**
- Entity extraction from text (LLM-based)
- Relationship mapping (builds Knowledge Graph)
- Hybrid retrieval (KG + Vector search)
- PostgreSQL storage (entities, relationships)
- Qdrant storage (vectors)
- Context enrichment
- Citation support

**Reference:**
- Repository: `tech_kb/LightRAG-main/`
- Examples: 24 examples including Ollama, PostgreSQL, OpenAI-compatible
- Documentation: [LearnOpenCV Guide](https://learnopencv.com/lightrag)

---

## Ansible Role Structure

```
roles/orchestrator_lightrag/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-dependencies.yml
│   ├── 02-lightrag-install.yml
│   ├── 03-configuration.yml
│   ├── 04-kg-storage-setup.yml
│   ├── 05-entity-extraction.yml
│   ├── 06-hybrid-retrieval.yml
│   ├── 07-api-endpoints.yml
│   └── 08-validation.yml
├── templates/
│   ├── services/lightrag_service.py.j2
│   ├── api/ingestion.py.j2
│   ├── api/query.py.j2
│   └── config/lightrag_config.py.j2
├── files/
│   ├── requirements-lightrag.txt
│   └── test_corpus/
│       └── sample.txt
└── handlers/
    └── main.yml
```

---

## files/requirements-lightrag.txt

```
# LightRAG Dependencies
# Component 6: LightRAG Engine

# LightRAG with API support
lightrag-hku[api]

# Already installed from other components, but ensure versions:
# - networkx (graph algorithms)
# - numpy (numerical operations)
# - pandas>=2.0.0 (data manipulation)
# - tiktoken (token counting)
# - tenacity (retry logic)
# - json_repair (JSON parsing)
# - xlsxwriter>=3.1.0 (export)

# Additional for PostgreSQL KG storage
asyncpg>=0.29.0  # Already installed in Component 3
sqlalchemy[asyncio]>=2.0.0  # Already installed

# For OpenAI-compatible LLM (LiteLLM)
openai>=1.0.0  # LiteLLM compatibility
```

---

## defaults/main.yml

```yaml
---
# LightRAG Configuration
lightrag_working_dir: "/opt/hx-citadel-shield/data/lightrag"
lightrag_kg_enable: true
lightrag_vector_enable: true
lightrag_hybrid_enable: true

# LLM Configuration (via LiteLLM - OpenAI compatible)
llm_api_base: "http://192.168.10.46:4000/v1"
llm_api_key: "{{ vault_litellm_api_key }}"
llm_model: "llama3.2:latest"
llm_embedding_model: "mxbai-embed-large"
llm_max_tokens: 4096
llm_temperature: 0.0  # Deterministic for entity extraction

# Entity Extraction Configuration
entity_extraction_prompt: |
  Extract entities and their types from the following text.
  Entity types: PERSON, ORGANIZATION, LOCATION, CONCEPT, EVENT, PRODUCT, TECHNOLOGY
  
  Return JSON:
  {
    "entities": [
      {"name": "...", "type": "...", "description": "..."},
      ...
    ]
  }

# Relationship Extraction Configuration
relationship_extraction_prompt: |
  Extract relationships between entities from the following text.
  
  Return JSON:
  {
    "relationships": [
      {"source": "...", "target": "...", "type": "...", "description": "..."},
      ...
    ]
  }

# Hybrid Retrieval Configuration
hybrid_alpha: 0.5  # 0.5 = equal weight KG and Vector
kg_max_depth: 2    # Graph traversal depth
vector_top_k: 10   # Vector search results
```

---

## templates/services/lightrag_service.py.j2

```python
"""
LightRAG service wrapper for Shield Orchestrator
"""

from lightrag import LightRAG, QueryParam
from lightrag.llm import openai_complete, openai_embedding
from lightrag.utils import EmbeddingFunc
import os
import logging
from typing import List, Dict, Any
import asyncio

logger = logging.getLogger("shield-orchestrator.lightrag")


class LightRAGService:
    """
    LightRAG engine wrapper.
    
    Features:
      - Hybrid retrieval (KG + Vector)
      - Entity extraction
      - Relationship mapping
      - PostgreSQL KG storage
      - Qdrant vector storage
    """
    
    def __init__(self):
        self.rag: Optional[LightRAG] = None
        self.working_dir = "{{ lightrag_working_dir }}"
        self.initialized = False
    
    async def initialize(self):
        """
        Initialize LightRAG engine.
        
        Configuration:
          - Working directory: {{ lightrag_working_dir }}
          - LLM: {{ llm_model }} (via LiteLLM)
          - Embeddings: {{ llm_embedding_model }} (via Ollama/LiteLLM)
          - KG Storage: PostgreSQL
          - Vector Storage: Qdrant
        """
        logger.info("Initializing LightRAG engine...")
        
        # Configure OpenAI-compatible LLM (LiteLLM)
        async def llm_model_func(prompt, **kwargs):
            return await openai_complete(
                prompt,
                model="{{ llm_model }}",
                api_base="{{ llm_api_base }}",
                api_key="{{ llm_api_key }}",
                **kwargs
            )
        
        # Configure embeddings (Ollama via LiteLLM)
        async def embedding_func(texts: List[str]) -> List[List[float]]:
            return await openai_embedding(
                texts,
                model="{{ llm_embedding_model }}",
                api_base="{{ llm_api_base }}",
                api_key="{{ llm_api_key }}"
            )
        
        # Initialize LightRAG
        self.rag = LightRAG(
            working_dir=self.working_dir,
            llm_model_func=llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim={{ ollama_embedding_dim }},
                max_token_size=8192,
                func=embedding_func
            ),
            # Storage backends will be configured in next iteration
            # For now, use file-based storage (default)
        )
        
        self.initialized = True
        logger.info("✅ LightRAG engine initialized")
    
    async def insert_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Insert text into LightRAG (builds KG + vectors).
        
        Steps:
          1. Extract entities (LLM)
          2. Extract relationships (LLM)
          3. Update Knowledge Graph
          4. Generate embeddings
          5. Store in Qdrant
        
        Args:
            text: Text content to process
            metadata: Optional metadata (source_uri, etc.)
        
        Returns:
            Statistics (entities extracted, relationships, etc.)
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Insert into LightRAG
            await self.rag.ainsert(text)
            
            # TODO: Track statistics
            stats = {
                "status": "success",
                "text_length": len(text),
                "entities_extracted": 0,  # TODO: Get from LightRAG
                "relationships_extracted": 0,  # TODO: Get from LightRAG
                "metadata": metadata or {}
            }
            
            logger.info(f"✅ Inserted text ({len(text)} chars)")
            return stats
        
        except Exception as e:
            logger.error(f"LightRAG insertion error: {str(e)}")
            raise
    
    async def query(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = {{ vector_top_k }},
        max_depth: int = {{ kg_max_depth }}
    ) -> Dict[str, Any]:
        """
        Query LightRAG with hybrid retrieval.
        
        Modes:
          - "hybrid": KG + Vector (best results)
          - "kg": Knowledge Graph only
          - "vector": Vector search only
        
        Args:
            query: Natural language query
            mode: Retrieval mode
            top_k: Number of results
            max_depth: KG traversal depth
        
        Returns:
            Retrieved context and answer
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create query parameters
            param = QueryParam(
                mode=mode,
                top_k=top_k,
                # Additional parameters as needed
            )
            
            # Execute query
            result = await self.rag.aquery(query, param=param)
            
            return {
                "query": query,
                "mode": mode,
                "answer": result,
                "metadata": {
                    "top_k": top_k,
                    "max_depth": max_depth
                }
            }
        
        except Exception as e:
            logger.error(f"LightRAG query error: {str(e)}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get LightRAG statistics.
        
        Returns:
            Entity count, relationship count, KG size, etc.
        """
        # TODO: Implement statistics gathering
        return {
            "initialized": self.initialized,
            "working_dir": self.working_dir,
            "kg_entities": 0,  # TODO: Count from PostgreSQL
            "kg_relationships": 0,  # TODO: Count from PostgreSQL
        }


# Global service instance
lightrag_service = LightRAGService()


async def init_lightrag():
    """Initialize LightRAG service"""
    await lightrag_service.initialize()


async def check_lightrag_health() -> dict:
    """
    Check LightRAG health for /health/detailed endpoint.
    """
    try:
        stats = await lightrag_service.get_stats()
        
        return {
            "status": "up",
            "initialized": stats["initialized"],
            "kg_entities": stats.get("kg_entities", 0),
            "kg_relationships": stats.get("kg_relationships", 0)
        }
    except Exception as e:
        logger.error(f"LightRAG health check failed: {str(e)}")
        return {
            "status": "down",
            "error": str(e)
        }
```

---

## templates/api/ingestion.py.j2

```python
"""
Ingestion API endpoints (async)
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import logging

from services.redis_streams import redis_streams
from services.event_bus import event_bus

router = APIRouter()
logger = logging.getLogger("shield-orchestrator.ingestion")


class IngestRequest(BaseModel):
    """Request model for async ingestion"""
    chunks: List[Dict[str, Any]]
    source_type: str  # web, document, manual
    metadata: Dict[str, Any] = {}


class IngestResponse(BaseModel):
    """Response model for async ingestion"""
    status: str
    job_id: str
    chunks_queued: int
    message: str


@router.post(
    "/lightrag/ingest-async",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["ingestion"]
)
async def ingest_async(request: IngestRequest):
    """
    Asynchronous ingestion endpoint (HTTP 202 Accepted).
    
    Flow:
      1. Generate job_id
      2. Add chunks to Redis Streams (shield:ingestion_queue)
      3. Return HTTP 202 Accepted immediately
      4. Workers process chunks in background
      5. Events emitted via Redis Streams (shield:events)
    
    Args:
        request: IngestRequest with chunks and metadata
    
    Returns:
        HTTP 202 + job_id for tracking
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Add chunks to Redis Streams queue
        chunks_queued = 0
        for idx, chunk in enumerate(request.chunks):
            chunk_id = f"{job_id}::{idx}"
            
            await redis_streams.add_task(
                job_id=job_id,
                chunk_id=chunk_id,
                content=chunk.get("text", ""),
                source_uri=chunk.get("source_uri", ""),
                source_type=request.source_type,
                metadata={
                    **chunk.get("metadata", {}),
                    **request.metadata
                }
            )
            chunks_queued += 1
        
        # Emit event: job queued
        await event_bus.emit_event(
            event_type="ingestion.queued",
            job_id=job_id,
            data={
                "chunks_total": len(request.chunks),
                "source_type": request.source_type
            }
        )
        
        logger.info(f"Job {job_id}: {chunks_queued} chunks queued")
        
        return IngestResponse(
            status="accepted",
            job_id=job_id,
            chunks_queued=chunks_queued,
            message=f"Ingestion job queued. Track status at /jobs/{job_id}"
        )
    
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

---

## templates/api/query.py.j2

```python
"""
Query API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from services.lightrag_service import lightrag_service

router = APIRouter()
logger = logging.getLogger("shield-orchestrator.query")


class QueryRequest(BaseModel):
    """Request model for LightRAG query"""
    query: str
    mode: str = "hybrid"  # hybrid, kg, vector
    top_k: int = 10
    max_depth: int = 2


class QueryResponse(BaseModel):
    """Response model for LightRAG query"""
    query: str
    mode: str
    answer: str
    metadata: Dict[str, Any]


@router.post(
    "/lightrag/query",
    response_model=QueryResponse,
    tags=["query"]
)
async def lightrag_query(request: QueryRequest):
    """
    LightRAG hybrid query endpoint.
    
    Retrieval modes:
      - hybrid: KG + Vector (best quality)
      - kg: Knowledge Graph only (relationships)
      - vector: Vector search only (fast)
    
    Args:
        request: QueryRequest with query and parameters
    
    Returns:
        Answer with retrieved context
    """
    try:
        result = await lightrag_service.query(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k,
            max_depth=request.max_depth
        )
        
        return QueryResponse(
            query=request.query,
            mode=request.mode,
            answer=result["answer"],
            metadata=result.get("metadata", {})
        )
    
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

---

## tasks/01-dependencies.yml

```yaml
---
# LightRAG dependencies installation
- name: Copy LightRAG requirements
  ansible.builtin.copy:
    src: requirements-lightrag.txt
    dest: "{{ orchestrator_app_dir }}/requirements-lightrag.txt"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes

- name: Install LightRAG and dependencies
  ansible.builtin.pip:
    requirements: "{{ orchestrator_app_dir }}/requirements-lightrag.txt"
    virtualenv: "{{ orchestrator_venv_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  notify: restart orchestrator
  tags: [dependencies]

- name: Verify LightRAG installation
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import lightrag; print(f"LightRAG version: {lightrag.__version__}")'
  register: lightrag_version_check
  changed_when: false
  tags: [dependencies, validation]

- name: Display LightRAG version
  ansible.builtin.debug:
    msg: "{{ lightrag_version_check.stdout }}"
  tags: [dependencies]
```

---

## tasks/02-lightrag-install.yml

```yaml
---
# LightRAG engine setup
- name: Deploy LightRAG service module
  ansible.builtin.template:
    src: services/lightrag_service.py.j2
    dest: "{{ orchestrator_app_dir }}/services/lightrag_service.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [lightrag]

- name: Deploy LightRAG configuration
  ansible.builtin.template:
    src: config/lightrag_config.py.j2
    dest: "{{ orchestrator_app_dir }}/config/lightrag_config.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [lightrag]

- name: Test LightRAG service import
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import sys; sys.path.insert(0, "{{ orchestrator_app_dir }}"); 
    from services.lightrag_service import LightRAGService; 
    print("LightRAG service imported")'
  register: lightrag_import_test
  changed_when: false
  tags: [lightrag, validation]
```

---

## tasks/03-configuration.yml

```yaml
---
# LightRAG configuration
- name: Ensure LightRAG working directory exists
  ansible.builtin.file:
    path: "{{ lightrag_working_dir }}"
    state: directory
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0750"
  become: yes
  tags: [configuration]

- name: Create LightRAG subdirectories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0750"
  loop:
    - "{{ lightrag_working_dir }}/vdb"
    - "{{ lightrag_working_dir }}/cache"
    - "{{ lightrag_working_dir }}/cache/entity_extraction"
    - "{{ lightrag_working_dir }}/cache/relationship_extraction"
    - "{{ lightrag_working_dir }}/logs"
    - "{{ lightrag_working_dir }}/checkpoints"
  become: yes
  tags: [configuration]

- name: Set LightRAG directory permissions
  ansible.builtin.file:
    path: "{{ lightrag_working_dir }}"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0750"
    recurse: yes
  become: yes
  tags: [configuration]
```

---

## tasks/07-api-endpoints.yml

```yaml
---
# Deploy LightRAG API endpoints
- name: Deploy ingestion API
  ansible.builtin.template:
    src: api/ingestion.py.j2
    dest: "{{ orchestrator_app_dir }}/api/ingestion.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [api]

- name: Deploy query API
  ansible.builtin.template:
    src: api/query.py.j2
    dest: "{{ orchestrator_app_dir }}/api/query.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [api]

- name: Update main.py to include ingestion and query routers
  ansible.builtin.blockinfile:
    path: "{{ orchestrator_app_dir }}/main.py"
    marker: "# {mark} LIGHTRAG ROUTERS"
    insertafter: "app.include_router\\(events.router"
    block: |
      app.include_router(ingestion.router, prefix="/lightrag", tags=["ingestion"])
      app.include_router(query.router, prefix="/lightrag", tags=["query"])
  become: yes
  notify: restart orchestrator
  tags: [api]

- name: Add LightRAG imports to main.py
  ansible.builtin.lineinfile:
    path: "{{ orchestrator_app_dir }}/main.py"
    line: "from api import health, events, ingestion, query"
    regexp: "^from api import"
    state: present
  become: yes
  notify: restart orchestrator
  tags: [api]
```

---

## tasks/08-validation.yml

```yaml
---
# LightRAG validation
- name: Test LightRAG initialization
  ansible.builtin.shell: |
    cd {{ orchestrator_app_dir }}
    source {{ orchestrator_venv_dir }}/bin/activate
    python -c "
    import asyncio
    import sys
    sys.path.insert(0, '{{ orchestrator_app_dir }}')
    from services.lightrag_service import lightrag_service
    
    async def test():
        await lightrag_service.initialize()
        print('LightRAG initialized successfully')
    
    asyncio.run(test())
    "
  register: lightrag_init_test
  changed_when: false
  tags: [validation]

- name: Test ingestion endpoint
  ansible.builtin.uri:
    url: "http://localhost:8000/lightrag/ingest-async"
    method: POST
    body_format: json
    body:
      chunks:
        - text: "Test chunk for validation"
          source_uri: "test://validation"
          metadata: {}
      source_type: "test"
      metadata: {}
    status_code: 202
  register: ingestion_test
  tags: [validation]

- name: Display validation summary
  ansible.builtin.debug:
    msg:
      - "✅ LightRAG initialization: {{ lightrag_init_test.stdout }}"
      - "✅ Ingestion endpoint: {{ ingestion_test.status }}"
      - "✅ Job ID: {{ ingestion_test.json.job_id }}"
      - "✅ LightRAG engine operational!"
  tags: [validation]
```

---

## Success Criteria

```yaml
✅ Dependencies:
   • lightrag-hku[api] installed
   • All LightRAG dependencies installed (20+ packages)
   • openai >=1.0.0 installed (LiteLLM compatibility)

✅ LightRAG Engine:
   • Working directory: /opt/hx-citadel-shield/data/lightrag
   • Subdirectories: vdb, cache, logs, checkpoints
   • Permissions: orchestrator:orchestrator (0750)
   • Initialization successful

✅ Python Modules:
   • services/lightrag_service.py deployed
   • config/lightrag_config.py deployed
   • LightRAGService class importable

✅ API Endpoints:
   • POST /lightrag/ingest-async (HTTP 202)
   • POST /lightrag/query (hybrid retrieval)
   • Both endpoints operational

✅ Integration:
   • LLM: LiteLLM proxy connection working
   • Embeddings: Ollama connection working
   • KG Storage: PostgreSQL ready
   • Vector Storage: Qdrant ready

✅ Validation:
   • LightRAG initializes without errors
   • Test ingestion returns job_id
   • Test query returns results (after worker processes)
```

---

## Testing Procedures

### **Manual Testing**

```bash
# Test 1: LightRAG installation
cd /opt/hx-citadel-shield/orchestrator
source ../orchestrator-venv/bin/activate
python -c "import lightrag; print(lightrag.__version__)"

# Test 2: Initialize LightRAG
python -c "
import asyncio
from services.lightrag_service import lightrag_service

async def test():
    await lightrag_service.initialize()
    print('✅ Initialized')

asyncio.run(test())
"

# Test 3: Ingestion endpoint (HTTP 202)
curl -X POST http://192.168.10.8:8000/lightrag/ingest-async \
  -H "Content-Type: application/json" \
  -d '{
    "chunks": [
      {
        "text": "LightRAG is a hybrid retrieval system.",
        "source_uri": "test://example",
        "metadata": {}
      }
    ],
    "source_type": "test",
    "metadata": {}
  }' | jq .

# Expected response:
# {
#   "status": "accepted",
#   "job_id": "uuid-here",
#   "chunks_queued": 1,
#   "message": "Ingestion job queued. Track status at /jobs/uuid-here"
# }

# Test 4: Query endpoint (after worker processes)
curl -X POST http://192.168.10.8:8000/lightrag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is LightRAG?",
    "mode": "hybrid",
    "top_k": 5
  }' | jq .
```

---

## Timeline

**Estimated Time:** 12-15 hours

```yaml
Day 1-2 (8 hours): Installation and Configuration
  • Dependencies installation: 1 hour
  • LightRAG engine setup: 2 hours
  • Configuration: 1 hour
  • KG storage setup: 2 hours
  • Initial testing: 2 hours

Day 3-4 (4 hours): Entity Extraction Tuning
  • Entity extraction prompts: 1 hour
  • Test with sample corpus: 1 hour
  • Tune parameters: 1 hour
  • Validation: 1 hour

Day 5-7 (3 hours): Hybrid Retrieval
  • Configure hybrid retrieval: 1 hour
  • Test retrieval accuracy: 1 hour
  • RAGAS evaluation: 1 hour

Total: 15 hours over 7 days
```

---

## RAGAS Evaluation

**Quality Metrics (Target):**

```yaml
Entity Extraction:
  • Accuracy: >90% (precision + recall)
  • Entity types: 7 types (PERSON, ORG, etc.)
  • Extraction time: <5s per 1000 tokens

Hybrid Retrieval:
  • Faithfulness: >0.8
  • Answer Relevance: >0.7
  • Context Precision: >0.7
  • Context Recall: >0.7

Performance:
  • Query latency (p95): <1 second
  • Ingestion throughput: >10 chunks/second/worker
  • KG construction: <5s per 1000 tokens
```

---

## Next Component

**After LightRAG engine is operational, proceed to:**

→ **Component 7: Worker Pool** (`07-worker-pool-plan.md`)

---

**LightRAG Engine Plan Complete!** ✅
**Hybrid retrieval enabled!** 🚀

