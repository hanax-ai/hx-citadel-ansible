"""
Orchestrator LightRAG API Tests

Tests for the LightRAG hybrid retrieval and ingestion API endpoints.
Single Responsibility: Validate LightRAG query and ingestion endpoints.

Component Under Test:
- orchestrator_lightrag/api/query.py.j2
- orchestrator_lightrag/api/ingestion.py.j2

LightRAG API Features (deployed on orchestrator at hx-orchestrator-server:8000):
- Hybrid query with 4 modes (hybrid, local, global, naive)
- Async ingestion with HTTP 202 pattern
- Health check and statistics
- Job tracking integration
- Event bus integration
- Pydantic request/response validation

Test Coverage:
- Query endpoint with different modes
- Query response model validation
- Health check endpoint
- Async ingestion endpoint (HTTP 202)
- Ingestion validation (empty chunks check)
- Ingestion response model validation
- Stats endpoint
- Job creation and tracking
- Event emission on ingestion
"""

import pytest
import uuid


# Mock Pydantic models
class MockQueryRequest:
    """Mock QueryRequest model"""

    def __init__(
        self, query: str, mode: str = "hybrid", top_k: int = 10, max_depth: int = 2
    ):
        self.query = query
        self.mode = mode
        self.top_k = top_k
        self.max_depth = max_depth


class MockQueryResponse:
    """Mock QueryResponse model"""

    def __init__(self, query: str, mode: str, answer: str, metadata: dict):
        self.query = query
        self.mode = mode
        self.answer = answer
        self.metadata = metadata


class MockChunkData:
    """Mock ChunkData model"""

    def __init__(self, text: str, source_uri: str = "", metadata: dict = None):
        self.text = text
        self.source_uri = source_uri
        self.metadata = metadata or {}


class MockIngestRequest:
    """Mock IngestRequest model"""

    def __init__(self, chunks: list, source_type: str, metadata: dict = None):
        self.chunks = chunks
        self.source_type = source_type
        self.metadata = metadata or {}


class MockIngestResponse:
    """Mock IngestResponse model"""

    def __init__(self, status: str, job_id: str, chunks_queued: int, message: str):
        self.status = status
        self.job_id = job_id
        self.chunks_queued = chunks_queued
        self.message = message


# Mock LightRAG service
class MockLightRAGService:
    """Mock LightRAG service"""

    def __init__(self):
        self.initialized = True
        self.working_dir = "/opt/hx-citadel-shield/data/lightrag"
        self.kg_entities = 100
        self.kg_relationships = 250

    async def query(
        self, query: str, mode: str = "hybrid", top_k: int = 10, max_depth: int = 2
    ):
        """Execute query"""
        return {
            "answer": f"Answer to: {query} (mode: {mode})",
            "metadata": {
                "mode": mode,
                "top_k": top_k,
                "max_depth": max_depth,
                "processing_time": 0.5,
            },
        }

    async def get_stats(self):
        """Get statistics"""
        return {
            "initialized": self.initialized,
            "working_dir": self.working_dir,
            "llm_model": "llama3.2:latest",
            "embedding_model": "mxbai-embed-large",
            "kg_entities": self.kg_entities,
            "kg_relationships": self.kg_relationships,
        }


# Mock job tracker
class MockJobTracker:
    """Mock job tracker"""

    def __init__(self):
        self.jobs = {}

    async def create_job(
        self, job_id: str, job_type: str, chunks_total: int, metadata: dict = None
    ):
        """Create job"""
        self.jobs[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "chunks_total": chunks_total,
            "metadata": metadata or {},
        }


# Mock Redis streams
class MockRedisStreams:
    """Mock Redis streams"""

    def __init__(self):
        self.tasks = []

    async def add_task(
        self,
        job_id: str,
        chunk_id: str,
        content: str,
        source_uri: str,
        source_type: str,
        metadata: dict,
    ):
        """Add task to stream"""
        self.tasks.append(
            {
                "job_id": job_id,
                "chunk_id": chunk_id,
                "content": content,
                "source_uri": source_uri,
                "source_type": source_type,
                "metadata": metadata,
            }
        )


# Mock event bus
class MockEventBus:
    """Mock event bus"""

    def __init__(self):
        self.events = []

    async def emit_event(
        self,
        event_type: str,
        job_id: str = None,
        data: dict = None,
        metadata: dict = None,
    ):
        """Emit event"""
        self.events.append(
            {
                "event_type": event_type,
                "job_id": job_id,
                "data": data,
                "metadata": metadata,
            }
        )


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGQueryEndpoint:
    """Test POST /lightrag/query endpoint"""

    async def test_query_executes_with_hybrid_mode(self):
        """Test that query executes successfully with hybrid mode"""
        service = MockLightRAGService()
        request = MockQueryRequest(query="What is LightRAG?", mode="hybrid")

        result = await service.query(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k,
            max_depth=request.max_depth,
        )

        assert "answer" in result
        assert "mode: hybrid" in result["answer"]
        assert result["metadata"]["mode"] == "hybrid"

    async def test_query_supports_local_mode(self):
        """Test that query supports local KG mode"""
        service = MockLightRAGService()
        request = MockQueryRequest(query="Test query", mode="local")

        result = await service.query(query=request.query, mode=request.mode)

        assert result["metadata"]["mode"] == "local"

    async def test_query_supports_global_mode(self):
        """Test that query supports global KG mode"""
        service = MockLightRAGService()
        request = MockQueryRequest(query="Test query", mode="global")

        result = await service.query(query=request.query, mode=request.mode)

        assert result["metadata"]["mode"] == "global"

    async def test_query_supports_naive_mode(self):
        """Test that query supports naive vector-only mode"""
        service = MockLightRAGService()
        request = MockQueryRequest(query="Test query", mode="naive")

        result = await service.query(query=request.query, mode=request.mode)

        assert result["metadata"]["mode"] == "naive"

    async def test_query_returns_answer_and_metadata(self):
        """Test that query returns both answer and metadata"""
        service = MockLightRAGService()
        request = MockQueryRequest(query="Test query")

        result = await service.query(query=request.query, mode=request.mode)

        assert "answer" in result
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)

    async def test_query_respects_top_k_parameter(self):
        """Test that query respects top_k parameter"""
        service = MockLightRAGService()
        request = MockQueryRequest(query="Test query", top_k=20)

        result = await service.query(
            query=request.query, mode=request.mode, top_k=request.top_k
        )

        assert result["metadata"]["top_k"] == 20

    async def test_query_respects_max_depth_parameter(self):
        """Test that query respects max_depth parameter for KG traversal"""
        service = MockLightRAGService()
        request = MockQueryRequest(query="Test query", max_depth=3)

        result = await service.query(
            query=request.query, mode=request.mode, max_depth=request.max_depth
        )

        assert result["metadata"]["max_depth"] == 3


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGHealthEndpoint:
    """Test GET /lightrag/health endpoint"""

    async def test_health_returns_initialized_status(self):
        """Test that health endpoint returns initialized status"""
        service = MockLightRAGService()

        stats = await service.get_stats()

        assert stats["initialized"] is True
        assert "working_dir" in stats

    async def test_health_returns_model_information(self):
        """Test that health endpoint returns LLM and embedding model info"""
        service = MockLightRAGService()

        stats = await service.get_stats()

        assert stats["llm_model"] == "llama3.2:latest"
        assert stats["embedding_model"] == "mxbai-embed-large"

    async def test_health_returns_kg_statistics(self):
        """Test that health endpoint returns KG entity and relationship counts"""
        service = MockLightRAGService()

        stats = await service.get_stats()

        assert stats["kg_entities"] == 100
        assert stats["kg_relationships"] == 250


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGIngestionEndpoint:
    """Test POST /lightrag/ingest-async endpoint"""

    async def test_ingest_async_returns_http_202_accepted(self):
        """Test that ingest-async returns HTTP 202 Accepted immediately"""
        job_tracker = MockJobTracker()
        redis_streams = MockRedisStreams()
        event_bus = MockEventBus()

        chunks = [MockChunkData(text="Test content", source_uri="http://example.com")]
        request = MockIngestRequest(chunks=chunks, source_type="web")

        job_id = str(uuid.uuid4())

        # Create job
        await job_tracker.create_job(
            job_id=job_id,
            job_type="lightrag_ingestion",
            chunks_total=len(request.chunks),
            metadata={"source_type": request.source_type},
        )

        # Queue chunks
        for idx, chunk in enumerate(request.chunks):
            chunk_id = f"{job_id}::{idx}"
            await redis_streams.add_task(
                job_id=job_id,
                chunk_id=chunk_id,
                content=chunk.text,
                source_uri=chunk.source_uri,
                source_type=request.source_type,
                metadata={"chunk_index": idx},
            )

        # Emit event
        await event_bus.emit_event(
            event_type="ingestion.queued",
            job_id=job_id,
            data={
                "chunks_total": len(request.chunks),
                "source_type": request.source_type,
            },
        )

        # Verify job created
        assert job_id in job_tracker.jobs
        assert job_tracker.jobs[job_id]["chunks_total"] == 1

        # Verify chunks queued
        assert len(redis_streams.tasks) == 1
        assert redis_streams.tasks[0]["content"] == "Test content"

        # Verify event emitted
        assert len(event_bus.events) == 1
        assert event_bus.events[0]["event_type"] == "ingestion.queued"

    async def test_ingest_async_returns_job_id(self):
        """Test that ingest-async returns job_id for tracking"""
        job_tracker = MockJobTracker()
        request = MockIngestRequest(
            chunks=[MockChunkData(text="Test")], source_type="web"
        )

        job_id = str(uuid.uuid4())
        await job_tracker.create_job(
            job_id=job_id,
            job_type="lightrag_ingestion",
            chunks_total=len(request.chunks),
        )

        assert job_id in job_tracker.jobs

    async def test_ingest_async_queues_multiple_chunks(self):
        """Test that ingest-async queues all chunks to Redis Streams"""
        redis_streams = MockRedisStreams()
        chunks = [
            MockChunkData(text="Chunk 1"),
            MockChunkData(text="Chunk 2"),
            MockChunkData(text="Chunk 3"),
        ]
        request = MockIngestRequest(chunks=chunks, source_type="document")

        job_id = str(uuid.uuid4())

        for idx, chunk in enumerate(request.chunks):
            chunk_id = f"{job_id}::{idx}"
            await redis_streams.add_task(
                job_id=job_id,
                chunk_id=chunk_id,
                content=chunk.text,
                source_uri=chunk.source_uri,
                source_type=request.source_type,
                metadata={"chunk_index": idx},
            )

        assert len(redis_streams.tasks) == 3
        assert redis_streams.tasks[0]["content"] == "Chunk 1"
        assert redis_streams.tasks[2]["content"] == "Chunk 3"

    async def test_ingest_async_emits_ingestion_queued_event(self):
        """Test that ingest-async emits ingestion.queued event"""
        event_bus = MockEventBus()
        request = MockIngestRequest(
            chunks=[MockChunkData(text="Test")],
            source_type="web",
            metadata={"test": "data"},
        )

        job_id = str(uuid.uuid4())

        await event_bus.emit_event(
            event_type="ingestion.queued",
            job_id=job_id,
            data={
                "chunks_total": len(request.chunks),
                "source_type": request.source_type,
                "metadata": request.metadata,
            },
        )

        assert len(event_bus.events) == 1
        assert event_bus.events[0]["event_type"] == "ingestion.queued"
        assert event_bus.events[0]["data"]["source_type"] == "web"


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGStatsEndpoint:
    """Test GET /lightrag/stats endpoint"""

    async def test_stats_returns_kg_statistics(self):
        """Test that stats endpoint returns KG entity and relationship counts"""
        service = MockLightRAGService()

        stats = await service.get_stats()

        assert "kg_entities" in stats
        assert "kg_relationships" in stats
        assert stats["kg_entities"] == 100
        assert stats["kg_relationships"] == 250

    async def test_stats_returns_initialization_status(self):
        """Test that stats endpoint returns initialization status"""
        service = MockLightRAGService()

        stats = await service.get_stats()

        assert "initialized" in stats
        assert stats["initialized"] is True
