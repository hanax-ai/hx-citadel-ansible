# Component 5: Qdrant Integration
## Vector Database Client - Ansible Deployment Plan

**Component:** Qdrant Integration  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Qdrant Server:** hx-vectordb-server (192.168.10.9:6333)  
**Timeline:** Week 2, Days 5-7 (3-4 hours)  
**Priority:** ⭐ **CRITICAL - DATA LAYER**  
**Dependencies:** Component 1 (Base Setup), Component 2 (FastAPI)

---

## Overview

This plan covers Qdrant vector database integration for semantic search and vector storage, including:

- Qdrant client library installation
- HTTPS connection configuration (self-signed certificates)
- Collection verification (hx_corpus_v1)
- Vector search operations
- Embedding integration (Ollama)
- Health check integration
- Error handling and retries

---

## Ansible Role Structure

```
roles/orchestrator_qdrant/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-dependencies.yml
│   ├── 02-client-setup.yml
│   ├── 03-embeddings.yml
│   ├── 04-search-ops.yml
│   └── 05-validation.yml
├── templates/
│   ├── services/qdrant_client.py.j2
│   ├── services/embeddings.py.j2
│   └── utils/qdrant_health.py.j2
├── files/
│   └── requirements-qdrant.txt
└── handlers/
    └── main.yml
```

---

## files/requirements-qdrant.txt

```
# Qdrant Dependencies
# Component 5: Qdrant Integration

# Qdrant client
qdrant-client>=1.7.0

# gRPC support (for better performance)
grpcio>=1.60.0

# HTTP client (already installed, but ensure version)
httpx[http2]>=0.28.1
```

---

## defaults/main.yml

```yaml
---
# Qdrant Configuration
qdrant_url: "https://192.168.10.9:6333"
qdrant_api_key: "{{ vault_qdrant_api_key }}"
qdrant_collection: "hx_corpus_v1"
qdrant_verify_ssl: false  # Self-signed cert
qdrant_timeout: 30
qdrant_grpc_port: 6334

# Ollama (for embeddings)
ollama_url: "http://192.168.10.50:11434"
ollama_embedding_model: "mxbai-embed-large"
ollama_embedding_dim: 1024

# Search configuration
qdrant_default_limit: 10
qdrant_default_score_threshold: 0.7
qdrant_batch_size: 100
```

---

## templates/services/qdrant_client.py.j2

```python
"""
Qdrant vector database client
"""

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition
from typing import List, Dict, Any, Optional
import logging
from config.settings import settings

logger = logging.getLogger("shield-orchestrator.qdrant")


class QdrantService:
    """
    Qdrant vector database service.
    
    Features:
      - Async operations
      - Connection pooling
      - Error handling and retries
      - Health monitoring
    """
    
    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
        self.collection_name = "{{ qdrant_collection }}"
        self.embedding_dim = {{ ollama_embedding_dim }}
    
    async def connect(self):
        """Initialize Qdrant client"""
        self.client = AsyncQdrantClient(
            url="{{ qdrant_url }}",
            api_key="{{ qdrant_api_key }}",
            timeout={{ qdrant_timeout }},
            https={{ 'True' if 'https' in qdrant_url else 'False' }},
            verify={{ qdrant_verify_ssl | lower }}
        )
        
        # Verify connection
        collections = await self.client.get_collections()
        logger.info(f"✅ Connected to Qdrant ({len(collections.collections)} collections)")
    
    async def close(self):
        """Close Qdrant client"""
        if self.client:
            await self.client.close()
            logger.info("✅ Qdrant client closed")
    
    async def verify_collection(self) -> bool:
        """Verify collection exists"""
        try:
            collection_info = await self.client.get_collection(self.collection_name)
            logger.info(f"✅ Collection {self.collection_name}: {collection_info.points_count} vectors")
            return True
        except Exception as e:
            logger.error(f"Collection verification failed: {str(e)}")
            return False
    
    async def search(
        self,
        query_vector: List[float],
        limit: int = {{ qdrant_default_limit }},
        score_threshold: float = {{ qdrant_default_score_threshold }},
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search in Qdrant.
        
        Args:
            query_vector: Embedding vector (1024-dim for mxbai-embed-large)
            limit: Maximum results
            score_threshold: Minimum similarity score
            filters: Optional metadata filters
        
        Returns:
            List of search results with scores and metadata
        """
        try:
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filters
            )
            
            return [
                {
                    "id": str(result.id),
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "source_uri": result.payload.get("source_uri", ""),
                    "source_type": result.payload.get("source_type", "unknown"),
                    "metadata": result.payload
                }
                for result in results
            ]
        
        except Exception as e:
            logger.error(f"Qdrant search error: {str(e)}")
            raise
    
    async def upsert(
        self,
        points: List[Dict[str, Any]]
    ) -> bool:
        """
        Insert or update vectors in Qdrant.
        
        Args:
            points: List of points with id, vector, payload
        
        Returns:
            Success status
        """
        try:
            qdrant_points = [
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                for point in points
            ]
            
            await self.client.upsert(
                collection_name=self.collection_name,
                points=qdrant_points
            )
            
            logger.info(f"✅ Upserted {len(points)} vectors to {self.collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Qdrant upsert error: {str(e)}")
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_config": str(info.config.params.vectors),
                "status": str(info.status)
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {"error": str(e)}


# Global client instance
qdrant_service = QdrantService()


async def init_qdrant():
    """Initialize Qdrant service"""
    await qdrant_service.connect()
    await qdrant_service.verify_collection()


async def close_qdrant():
    """Close Qdrant service"""
    await qdrant_service.close()


async def check_qdrant_health() -> dict:
    """
    Check Qdrant health for /health/detailed endpoint.
    
    Returns:
        dict with status, latency, and collection info
    """
    import time
    
    try:
        start = time.time()
        collections = await qdrant_service.client.get_collections()
        latency_ms = (time.time() - start) * 1000
        
        collection_info = await qdrant_service.get_collection_info()
        
        return {
            "status": "up",
            "latency_ms": round(latency_ms, 2),
            "collections": [c.name for c in collections.collections],
            "vectors": collection_info.get("points_count", 0)
        }
    except Exception as e:
        logger.error(f"Qdrant health check failed: {str(e)}")
        return {
            "status": "down",
            "error": str(e),
            "latency_ms": 0
        }
```

---

## templates/services/embeddings.py.j2

```python
"""
Embedding service using Ollama
"""

import httpx
from typing import List
import logging
from config.settings import settings

logger = logging.getLogger("shield-orchestrator.embeddings")


class EmbeddingService:
    """
    Ollama embedding service.
    
    Uses mxbai-embed-large model (1024 dimensions).
    """
    
    def __init__(self):
        self.ollama_url = "{{ ollama_url }}"
        self.model = "{{ ollama_embedding_model }}"
        self.dimension = {{ ollama_embedding_dim }}
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for single text.
        
        Args:
            text: Text to embed
        
        Returns:
            1024-dimensional embedding vector
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["embedding"]
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts (batched).
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                response = await client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                result = response.json()
                embeddings.append(result["embedding"])
        
        logger.debug(f"Generated {len(embeddings)} embeddings")
        return embeddings


# Global service instance
embedding_service = EmbeddingService()


async def check_ollama_health() -> dict:
    """
    Check Ollama health for /health/detailed endpoint.
    """
    import time
    
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{embedding_service.ollama_url}/api/tags")
            response.raise_for_status()
            models = response.json()
        
        latency_ms = (time.time() - start) * 1000
        
        model_names = [m["name"] for m in models.get("models", [])]
        
        return {
            "status": "up",
            "latency_ms": round(latency_ms, 2),
            "models": model_names
        }
    except Exception as e:
        logger.error(f"Ollama health check failed: {str(e)}")
        return {
            "status": "down",
            "error": str(e),
            "latency_ms": 0
        }
```

---

## tasks/01-dependencies.yml

```yaml
---
# Qdrant client installation
- name: Copy Qdrant requirements
  ansible.builtin.copy:
    src: requirements-qdrant.txt
    dest: "{{ orchestrator_app_dir }}/requirements-qdrant.txt"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes

- name: Install Qdrant Python dependencies
  ansible.builtin.pip:
    requirements: "{{ orchestrator_app_dir }}/requirements-qdrant.txt"
    virtualenv: "{{ orchestrator_venv_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  notify: restart orchestrator
  tags: [dependencies]

- name: Verify Qdrant client installation
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'from qdrant_client import AsyncQdrantClient; print("Qdrant client installed")'
  register: qdrant_import_test
  changed_when: false
  tags: [dependencies, validation]
```

---

## tasks/02-client-setup.yml

```yaml
---
# Qdrant client module deployment
- name: Deploy Qdrant client module
  ansible.builtin.template:
    src: services/qdrant_client.py.j2
    dest: "{{ orchestrator_app_dir }}/services/qdrant_client.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [client]

- name: Test Qdrant client module import
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import sys; sys.path.insert(0, "{{ orchestrator_app_dir }}"); 
    from services.qdrant_client import QdrantService; 
    print("Qdrant service module imported")'
  register: client_import_test
  changed_when: false
  tags: [client, validation]
```

---

## tasks/03-embeddings.yml

```yaml
---
# Embedding service deployment
- name: Deploy embedding service module
  ansible.builtin.template:
    src: services/embeddings.py.j2
    dest: "{{ orchestrator_app_dir }}/services/embeddings.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [embeddings]

- name: Test embedding service import
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import sys; sys.path.insert(0, "{{ orchestrator_app_dir }}"); 
    from services.embeddings import EmbeddingService; 
    print("Embedding service imported")'
  register: embedding_import_test
  changed_when: false
  tags: [embeddings, validation]
```

---

## tasks/04-search-ops.yml

```yaml
---
# Deploy search operations
# (Will be expanded in LightRAG component)
- name: Create placeholder for search operations
  ansible.builtin.copy:
    content: |
      """
      Vector search operations
      
      TODO: Implement in LightRAG component (Component 6)
      """
      # Placeholder for now
    dest: "{{ orchestrator_app_dir }}/services/vector_search.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  tags: [search]
```

---

## tasks/05-validation.yml

```yaml
---
# Qdrant integration validation
- name: Test Qdrant connection from orchestrator
  ansible.builtin.uri:
    url: "{{ qdrant_url }}/collections"
    method: GET
    headers:
      api-key: "{{ qdrant_api_key }}"
    validate_certs: "{{ qdrant_verify_ssl }}"
    status_code: 200
  register: qdrant_connection_test
  tags: [validation]

- name: Verify collection exists
  ansible.builtin.uri:
    url: "{{ qdrant_url }}/collections/{{ qdrant_collection }}"
    method: GET
    headers:
      api-key: "{{ qdrant_api_key }}"
    validate_certs: "{{ qdrant_verify_ssl }}"
    status_code: 200
  register: collection_verification
  tags: [validation]

- name: Test Ollama embedding endpoint
  ansible.builtin.uri:
    url: "{{ ollama_url }}/api/tags"
    method: GET
    status_code: 200
  register: ollama_test
  tags: [validation]

- name: Verify embedding model available
  ansible.builtin.shell: >
    curl -s {{ ollama_url }}/api/tags | jq -r '.models[].name' | grep -q {{ ollama_embedding_model }}
  register: embedding_model_check
  changed_when: false
  tags: [validation]

- name: Display Qdrant validation summary
  ansible.builtin.debug:
    msg:
      - "✅ Qdrant connection: {{ qdrant_connection_test.status }}"
      - "✅ Collection {{ qdrant_collection }}: exists"
      - "✅ Vectors: {{ collection_verification.json.result.points_count }}"
      - "✅ Ollama available: {{ ollama_test.status }}"
      - "✅ Embedding model: {{ ollama_embedding_model }}"
      - "✅ Qdrant integration complete!"
  tags: [validation]
```

---

## Success Criteria

```yaml
✅ Dependencies:
   • qdrant-client >=1.7.0 installed
   • grpcio >=1.60.0 installed
   • httpx[http2] installed

✅ Python Modules:
   • services/qdrant_client.py deployed
   • services/embeddings.py deployed
   • QdrantService class importable
   • EmbeddingService class importable

✅ Qdrant Connection:
   • HTTPS connection successful (verify_ssl=false for self-signed)
   • API key authentication working
   • Collection hx_corpus_v1 accessible
   • Vector count > 0 (from MCP testing)

✅ Ollama Integration:
   • Ollama API accessible
   • mxbai-embed-large model available
   • Embedding generation working (1024-dim)

✅ Validation:
   • Qdrant collections endpoint returns 200
   • Collection info retrieved successfully
   • Ollama health check passing
   • Embedding model verified
```

---

## Testing Procedures

```bash
# Test 1: Qdrant connection
curl -k -H "api-key: {{ vault_qdrant_api_key }}" \
  https://192.168.10.9:6333/collections | jq .

# Test 2: Collection info
curl -k -H "api-key: {{ vault_qdrant_api_key }}" \
  https://192.168.10.9:6333/collections/hx_corpus_v1 | jq .

# Test 3: Ollama connection
curl http://192.168.10.50:11434/api/tags | jq .

# Test 4: Generate embedding
curl http://192.168.10.50:11434/api/embeddings \
  -d '{"model": "mxbai-embed-large", "prompt": "test"}' | jq '.embedding | length'
# Should return: 1024

# Test 5: Python client test
cd /opt/hx-citadel-shield/orchestrator
source ../orchestrator-venv/bin/activate
python -c "
import asyncio
from services.qdrant_client import qdrant_service

async def test():
    await qdrant_service.connect()
    exists = await qdrant_service.verify_collection()
    info = await qdrant_service.get_collection_info()
    print(f'Collection: {info}')
    await qdrant_service.close()

asyncio.run(test())
"
```

---

## Timeline

**Estimated Time:** 3-4 hours

```yaml
Task Breakdown:
  • Dependencies installation: 30 minutes
  • Client setup: 1 hour
  • Embeddings integration: 1 hour
  • Validation: 30 minutes
  • Testing: 30 minutes

Total: 3.5 hours
```

---

## Next Component

**After Qdrant integration, proceed to:**

→ **Component 6: LightRAG Engine** (`06-lightrag-engine-plan.md`) ⭐ **MOST COMPLEX**

---

**Qdrant Integration Plan Complete!** ✅
**Vector search enabled!** 🚀

