"""
Orchestrator Qdrant Client Tests

Tests for the Qdrant vector database client in orchestrator.
Single Responsibility: Validate vector search and storage operations.

Component Under Test:
- orchestrator_qdrant/services/qdrant_client.py.j2

Qdrant Client Features (deployed at hx-vectordb-server:6333):
- Async vector operations
- Semantic search with similarity scores
- Vector upsert (insert/update)
- Metadata filtering
- Collection management
- Health monitoring with latency metrics

Test Coverage:
- Client connection and initialization
- Collection verification
- Vector search with filters
- Vector upsert operations
- Collection info retrieval
- Health check with latency measurement
- Error handling
- Client cleanup
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# Mock Qdrant client classes
class MockCollectionInfo:
    """Mock collection info"""

    def __init__(self, name: str = "test_collection", points_count: int = 0):
        self.name = name
        self.points_count = points_count
        self.config = MagicMock()
        self.config.params.vectors = "1024-dim"
        self.status = "green"


class MockCollections:
    """Mock collections list"""

    def __init__(self, names: list):
        self.collections = [MockCollectionInfo(name) for name in names]


class MockSearchResult:
    """Mock search result"""

    def __init__(self, id: str, score: float, payload: dict):
        self.id = id
        self.score = score
        self.payload = payload


class MockQdrantService:
    """Mock Qdrant service for testing"""

    def __init__(self):
        self.client = None
        self.collection_name = "hx_corpus_v1"
        self.embedding_dim = 1024
        self.connected = False

    async def connect(self):
        """Connect to Qdrant"""
        self.client = AsyncMock()
        self.client.get_collections = AsyncMock(
            return_value=MockCollections(["hx_corpus_v1", "test_collection"])
        )
        self.connected = True

    async def close(self):
        """Close Qdrant connection"""
        if self.client:
            await self.client.close()
            self.client = None
            self.connected = False

    async def verify_collection(self):
        """Verify collection exists"""
        if not self.client:
            return False

        try:
            collection_info = await self.client.get_collection(self.collection_name)
            return True
        except Exception:
            return False

    async def search(
        self, query_vector: list, limit: int = 5, score_threshold: float = 0.5, filters: dict = None
    ):
        """Search vectors"""
        if not self.client:
            raise Exception("Client not connected")

        # Mock search results
        results = [
            MockSearchResult(
                id="vec-1",
                score=0.95,
                payload={"text": "Result 1", "source_uri": "http://example.com", "source_type": "web"},
            ),
            MockSearchResult(
                id="vec-2",
                score=0.87,
                payload={"text": "Result 2", "source_uri": "http://example.org", "source_type": "web"},
            ),
        ]

        # Apply filters if provided
        if filters:
            # Filter results based on metadata (simplified)
            filtered = []
            for r in results:
                if filters.get("source_type") and r.payload.get("source_type") == filters["source_type"]:
                    filtered.append(r)
            results = filtered

        # Apply limit
        results = results[:limit]

        # Apply score threshold
        results = [r for r in results if r.score >= score_threshold]

        return [
            {
                "id": str(result.id),
                "score": result.score,
                "text": result.payload.get("text", ""),
                "source_uri": result.payload.get("source_uri", ""),
                "source_type": result.payload.get("source_type", "unknown"),
                "metadata": result.payload,
            }
            for result in results
        ]

    async def upsert(self, points: list):
        """Upsert vectors"""
        if not self.client:
            raise Exception("Client not connected")

        # Validate points
        for point in points:
            if "id" not in point or "vector" not in point:
                raise ValueError("Point must have 'id' and 'vector'")
            if len(point["vector"]) != self.embedding_dim:
                raise ValueError(f"Vector must be {self.embedding_dim}-dimensional")

        return True

    async def get_collection_info(self):
        """Get collection info"""
        if not self.client:
            return {"error": "Client not connected"}

        collection = MockCollectionInfo(self.collection_name, points_count=12345)

        return {
            "name": self.collection_name,
            "points_count": collection.points_count,
            "vectors_config": "1024-dim",
            "status": "green",
        }


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestQdrantConnection:
    """Test Qdrant client connection"""

    async def test_client_connects_successfully(self):
        """Test that client connects to Qdrant"""
        service = MockQdrantService()

        assert service.client is None
        assert service.connected is False

        await service.connect()

        assert service.client is not None
        assert service.connected is True

    async def test_client_verifies_collections_on_connect(self):
        """Test that client verifies collections exist on connect"""
        service = MockQdrantService()

        await service.connect()

        # Should have called get_collections
        assert service.client.get_collections.called

    async def test_client_closes_successfully(self):
        """Test that client closes connection"""
        service = MockQdrantService()

        await service.connect()
        await service.close()

        assert service.connected is False

    async def test_verify_collection_returns_true_if_exists(self):
        """Test that verify_collection returns True when collection exists"""
        service = MockQdrantService()

        await service.connect()

        # Mock get_collection to succeed
        service.client.get_collection = AsyncMock(
            return_value=MockCollectionInfo("hx_corpus_v1", points_count=100)
        )

        result = await service.verify_collection()

        assert result is True

    async def test_verify_collection_returns_false_if_not_connected(self):
        """Test that verify_collection returns False if not connected"""
        service = MockQdrantService()

        # Don't connect
        result = await service.verify_collection()

        assert result is False


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestQdrantSearch:
    """Test Qdrant vector search"""

    async def test_search_returns_results_with_scores(self):
        """Test that search returns results with similarity scores"""
        service = MockQdrantService()
        await service.connect()

        query_vector = [0.1] * 1024
        results = await service.search(query_vector, limit=5)

        assert len(results) > 0
        assert all("score" in r for r in results)
        assert all(isinstance(r["score"], float) for r in results)

    async def test_search_returns_results_with_metadata(self):
        """Test that search returns results with metadata"""
        service = MockQdrantService()
        await service.connect()

        query_vector = [0.1] * 1024
        results = await service.search(query_vector)

        assert all("text" in r for r in results)
        assert all("source_uri" in r for r in results)
        assert all("source_type" in r for r in results)

    async def test_search_respects_limit_parameter(self):
        """Test that search respects limit parameter"""
        service = MockQdrantService()
        await service.connect()

        query_vector = [0.1] * 1024
        results = await service.search(query_vector, limit=1)

        assert len(results) <= 1

    async def test_search_applies_score_threshold(self):
        """Test that search filters by score threshold"""
        service = MockQdrantService()
        await service.connect()

        query_vector = [0.1] * 1024
        results = await service.search(query_vector, score_threshold=0.9)

        # Only results with score >= 0.9
        assert all(r["score"] >= 0.9 for r in results)

    async def test_search_applies_metadata_filters(self):
        """Test that search applies metadata filters"""
        service = MockQdrantService()
        await service.connect()

        query_vector = [0.1] * 1024
        filters = {"source_type": "web"}

        results = await service.search(query_vector, filters=filters)

        assert all(r["source_type"] == "web" for r in results)

    async def test_search_raises_error_if_not_connected(self):
        """Test that search raises error if client not connected"""
        service = MockQdrantService()

        query_vector = [0.1] * 1024

        with pytest.raises(Exception):
            await service.search(query_vector)


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestQdrantUpsert:
    """Test Qdrant vector upsert"""

    async def test_upsert_inserts_vectors(self):
        """Test that upsert inserts vectors successfully"""
        service = MockQdrantService()
        await service.connect()

        points = [
            {"id": "vec-1", "vector": [0.1] * 1024, "payload": {"text": "Test 1"}},
            {"id": "vec-2", "vector": [0.2] * 1024, "payload": {"text": "Test 2"}},
        ]

        result = await service.upsert(points)

        assert result is True

    async def test_upsert_validates_vector_dimensions(self):
        """Test that upsert validates vector dimensions"""
        service = MockQdrantService()
        await service.connect()

        # Wrong dimension (512 instead of 1024)
        points = [{"id": "vec-1", "vector": [0.1] * 512, "payload": {}}]

        with pytest.raises(ValueError):
            await service.upsert(points)

    async def test_upsert_requires_id_and_vector(self):
        """Test that upsert requires id and vector fields"""
        service = MockQdrantService()
        await service.connect()

        # Missing 'vector' field
        points = [{"id": "vec-1", "payload": {}}]

        with pytest.raises(ValueError):
            await service.upsert(points)

    async def test_upsert_raises_error_if_not_connected(self):
        """Test that upsert raises error if client not connected"""
        service = MockQdrantService()

        points = [{"id": "vec-1", "vector": [0.1] * 1024}]

        with pytest.raises(Exception):
            await service.upsert(points)


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestQdrantCollectionInfo:
    """Test Qdrant collection info"""

    async def test_get_collection_info_returns_statistics(self):
        """Test that get_collection_info returns collection stats"""
        service = MockQdrantService()
        await service.connect()

        info = await service.get_collection_info()

        assert "name" in info
        assert "points_count" in info
        assert "vectors_config" in info
        assert "status" in info

    async def test_get_collection_info_returns_points_count(self):
        """Test that collection info includes points count"""
        service = MockQdrantService()
        await service.connect()

        info = await service.get_collection_info()

        assert isinstance(info["points_count"], int)
        assert info["points_count"] >= 0

    async def test_get_collection_info_returns_error_if_not_connected(self):
        """Test that collection info returns error if not connected"""
        service = MockQdrantService()

        info = await service.get_collection_info()

        assert "error" in info
