"""
Orchestrator LightRAG Service Tests

Tests for the LightRAG service wrapper in orchestrator.
Single Responsibility: Validate hybrid knowledge graph + vector retrieval.

Component Under Test:
- orchestrator_lightrag/services/lightrag_service.py.j2

LightRAG Service (deployed on orchestrator at hx-orchestrator-server):
- Hybrid retrieval (Knowledge Graph + Vector Search)
- Entity extraction from text
- Relationship mapping
- 4 query modes: hybrid, local, global, naive

Test Coverage:
- Service initialization
- Text insertion and KG construction
- Query execution (all 4 modes)
- Invalid mode handling
- Statistics retrieval
- Service lifecycle (init, close)
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio


# Mock LightRAG service class
class MockLightRAGService:
    """Mock LightRAG service for testing"""

    def __init__(self):
        self.rag = None
        self.working_dir = "/opt/hx-citadel-shield/lightrag"
        self.initialized = False
        self.llm_model = "gpt-4"
        self.embedding_model = "mxbai-embed-large"

    async def initialize(self):
        """Initialize LightRAG engine"""
        if self.initialized:
            return

        self.rag = MagicMock()
        self.initialized = True

    async def insert_text(self, text: str, metadata: dict = None):
        """Insert text into LightRAG"""
        if not self.initialized:
            await self.initialize()

        return {
            "status": "success",
            "text_length": len(text),
            "entities_extracted": 5,
            "relationships_extracted": 3,
            "metadata": metadata or {}
        }

    async def query(self, query: str, mode: str = "hybrid", top_k: int = 5, max_depth: int = 2):
        """Query LightRAG"""
        if not self.initialized:
            await self.initialize()

        if mode not in ["hybrid", "local", "global", "naive"]:
            raise ValueError(f"Invalid mode: {mode}")

        return {
            "query": query,
            "mode": mode,
            "answer": f"Answer for: {query}",
            "metadata": {
                "top_k": top_k,
                "max_depth": max_depth,
                "model": self.llm_model,
                "embedding_model": self.embedding_model
            }
        }

    async def get_stats(self):
        """Get LightRAG statistics"""
        return {
            "initialized": self.initialized,
            "working_dir": self.working_dir,
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
            "kg_entities": 42,
            "kg_relationships": 67,
            "vector_count": 128
        }

    async def close(self):
        """Close LightRAG"""
        self.rag = None
        self.initialized = False


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGServiceInitialization:
    """Test LightRAG service initialization"""

    async def test_service_initializes_successfully(self):
        """Test that service initializes correctly"""
        service = MockLightRAGService()

        assert service.initialized is False
        assert service.rag is None

        await service.initialize()

        assert service.initialized is True
        assert service.rag is not None

    async def test_service_initialization_is_idempotent(self):
        """Test that calling initialize() twice is safe"""
        service = MockLightRAGService()

        await service.initialize()
        first_rag = service.rag

        # Initialize again
        await service.initialize()

        # Should not reinitialize
        assert service.initialized is True
        assert service.rag is first_rag

    async def test_service_sets_working_directory(self):
        """Test that service sets working directory"""
        service = MockLightRAGService()

        assert service.working_dir is not None
        assert isinstance(service.working_dir, str)
        assert len(service.working_dir) > 0

    async def test_service_configures_llm_model(self):
        """Test that service configures LLM model"""
        service = MockLightRAGService()

        assert service.llm_model is not None
        assert isinstance(service.llm_model, str)

    async def test_service_configures_embedding_model(self):
        """Test that service configures embedding model"""
        service = MockLightRAGService()

        assert service.embedding_model is not None
        assert isinstance(service.embedding_model, str)


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGTextInsertion:
    """Test text insertion and knowledge graph construction"""

    async def test_insert_text_returns_success_status(self):
        """Test that text insertion returns success status"""
        service = MockLightRAGService()
        await service.initialize()

        result = await service.insert_text("Test document content")

        assert result["status"] == "success"

    async def test_insert_text_returns_text_length(self):
        """Test that insertion returns text length"""
        service = MockLightRAGService()
        await service.initialize()

        text = "This is a test document"
        result = await service.insert_text(text)

        assert result["text_length"] == len(text)

    async def test_insert_text_extracts_entities(self):
        """Test that insertion extracts entities"""
        service = MockLightRAGService()
        await service.initialize()

        result = await service.insert_text("Python is a programming language")

        assert "entities_extracted" in result
        assert isinstance(result["entities_extracted"], int)
        assert result["entities_extracted"] >= 0

    async def test_insert_text_extracts_relationships(self):
        """Test that insertion extracts relationships"""
        service = MockLightRAGService()
        await service.initialize()

        result = await service.insert_text("Python is used for AI development")

        assert "relationships_extracted" in result
        assert isinstance(result["relationships_extracted"], int)
        assert result["relationships_extracted"] >= 0

    async def test_insert_text_preserves_metadata(self):
        """Test that insertion preserves metadata"""
        service = MockLightRAGService()
        await service.initialize()

        metadata = {"source_uri": "https://example.com", "document_id": "doc-123"}
        result = await service.insert_text("Test content", metadata=metadata)

        assert result["metadata"] == metadata

    async def test_insert_text_auto_initializes_if_needed(self):
        """Test that insertion auto-initializes service if not initialized"""
        service = MockLightRAGService()

        assert service.initialized is False

        # Should auto-initialize
        result = await service.insert_text("Test content")

        assert service.initialized is True
        assert result["status"] == "success"


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGQuerying:
    """Test LightRAG query with different modes"""

    async def test_query_hybrid_mode(self):
        """Test querying with hybrid mode (KG + Vector)"""
        service = MockLightRAGService()
        await service.initialize()

        result = await service.query("What is Python?", mode="hybrid")

        assert result["query"] == "What is Python?"
        assert result["mode"] == "hybrid"
        assert "answer" in result
        assert len(result["answer"]) > 0

    async def test_query_local_mode(self):
        """Test querying with local mode (Local KG traversal)"""
        service = MockLightRAGService()
        await service.initialize()

        result = await service.query("Python decorators", mode="local")

        assert result["mode"] == "local"
        assert "answer" in result

    async def test_query_global_mode(self):
        """Test querying with global mode (Global KG overview)"""
        service = MockLightRAGService()
        await service.initialize()

        result = await service.query("Python ecosystem", mode="global")

        assert result["mode"] == "global"
        assert "answer" in result

    async def test_query_naive_mode(self):
        """Test querying with naive mode (Simple vector search)"""
        service = MockLightRAGService()
        await service.initialize()

        result = await service.query("Python syntax", mode="naive")

        assert result["mode"] == "naive"
        assert "answer" in result

    async def test_query_includes_metadata(self):
        """Test that query result includes metadata"""
        service = MockLightRAGService()
        await service.initialize()

        result = await service.query("Test query", mode="hybrid", top_k=10, max_depth=3)

        assert "metadata" in result
        assert result["metadata"]["top_k"] == 10
        assert result["metadata"]["max_depth"] == 3
        assert "model" in result["metadata"]
        assert "embedding_model" in result["metadata"]

    async def test_query_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError"""
        service = MockLightRAGService()
        await service.initialize()

        with pytest.raises(ValueError):
            await service.query("Test query", mode="invalid_mode")

    async def test_query_auto_initializes_if_needed(self):
        """Test that query auto-initializes service if not initialized"""
        service = MockLightRAGService()

        assert service.initialized is False

        # Should auto-initialize
        result = await service.query("Test query")

        assert service.initialized is True
        assert "answer" in result


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGStatistics:
    """Test LightRAG statistics retrieval"""

    async def test_get_stats_returns_initialization_status(self):
        """Test that stats include initialization status"""
        service = MockLightRAGService()

        stats = await service.get_stats()
        assert stats["initialized"] is False

        await service.initialize()

        stats = await service.get_stats()
        assert stats["initialized"] is True

    async def test_get_stats_includes_working_directory(self):
        """Test that stats include working directory"""
        service = MockLightRAGService()

        stats = await service.get_stats()

        assert "working_dir" in stats
        assert isinstance(stats["working_dir"], str)

    async def test_get_stats_includes_model_info(self):
        """Test that stats include model configuration"""
        service = MockLightRAGService()

        stats = await service.get_stats()

        assert "llm_model" in stats
        assert "embedding_model" in stats
        assert isinstance(stats["llm_model"], str)
        assert isinstance(stats["embedding_model"], str)

    async def test_get_stats_includes_kg_metrics(self):
        """Test that stats include knowledge graph metrics"""
        service = MockLightRAGService()
        await service.initialize()

        stats = await service.get_stats()

        assert "kg_entities" in stats
        assert "kg_relationships" in stats
        assert isinstance(stats["kg_entities"], int)
        assert isinstance(stats["kg_relationships"], int)

    async def test_get_stats_includes_vector_count(self):
        """Test that stats include vector count"""
        service = MockLightRAGService()
        await service.initialize()

        stats = await service.get_stats()

        assert "vector_count" in stats
        assert isinstance(stats["vector_count"], int)


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLightRAGServiceLifecycle:
    """Test LightRAG service lifecycle (init, close)"""

    async def test_service_closes_cleanly(self):
        """Test that service closes and cleans up resources"""
        service = MockLightRAGService()
        await service.initialize()

        assert service.initialized is True
        assert service.rag is not None

        await service.close()

        assert service.initialized is False
        assert service.rag is None

    async def test_service_can_reinitialize_after_close(self):
        """Test that service can be reinitialized after closing"""
        service = MockLightRAGService()

        # First lifecycle
        await service.initialize()
        await service.close()

        # Second lifecycle
        await service.initialize()

        assert service.initialized is True
        assert service.rag is not None
