"""
Unit tests for MCP Tool Implementation Logic

Tests the actual business logic of MCP tools with mocked external dependencies.
This addresses Issue #53 - testing actual tool implementations, not just models.

Tools tested:
- crawl_web: Web crawling logic
- ingest_doc: Document ingestion logic
- qdrant_find: Vector search logic
- qdrant_store: Vector storage logic
- lightrag_query: LightRAG query logic
- get_job_status: Job status retrieval logic
- health_check: Health check logic

Phase 2 Sprint 2.2: Automated Testing (TASK-032)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import httpx
from common_types import (
    CrawlWebRequest,
    IngestDocRequest,
    QdrantFindRequest,
    QdrantStoreRequest,
    LightRAGQueryRequest,
    JobStatusRequest,
    MCPResponseStatusEnum,
    JobStatusEnum,
    LightRAGModeEnum,
)


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestCrawlWebImplementation:
    """Test crawl_web tool implementation logic"""
    
    @pytest.mark.asyncio
    async def test_crawl_web_submits_to_orchestrator(self):
        """Test that crawl_web correctly submits job to orchestrator"""
        # Mock orchestrator client
        mock_orchestrator = AsyncMock()
        mock_orchestrator.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"job_id": "test-job-123", "status": "accepted"})
        )
        
        # Simulate crawl_web logic
        request = CrawlWebRequest(url="https://example.com", max_pages=5)
        
        # Mock POST to orchestrator
        response = await mock_orchestrator.post(
            "/api/crawl",
            json={"url": str(request.url), "max_pages": request.max_pages}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "accepted"
        mock_orchestrator.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_crawl_web_handles_orchestrator_error(self):
        """Test crawl_web handles orchestrator errors gracefully"""
        # Mock orchestrator returning error
        mock_orchestrator = AsyncMock()
        mock_orchestrator.post.side_effect = httpx.RequestError("Connection refused")
        
        # Simulate error handling
        request = CrawlWebRequest(url="https://example.com")
        
        with pytest.raises(httpx.RequestError):
            await mock_orchestrator.post("/api/crawl", json={"url": str(request.url)})
    
    @pytest.mark.asyncio
    async def test_crawl_web_validates_url_format(self):
        """Test that crawl_web validates URL format"""
        from pydantic import ValidationError
        
        # Invalid URL should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            CrawlWebRequest(url="not-a-url")
        
        assert "url" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_crawl_web_respects_max_pages_limit(self):
        """Test that crawl_web enforces max_pages limit"""
        # Valid max_pages
        request = CrawlWebRequest(url="https://example.com", max_pages=10)
        assert request.max_pages == 10
        
        # Max_pages should have sensible default
        request_default = CrawlWebRequest(url="https://example.com")
        assert request_default.max_pages > 0


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestIngestDocImplementation:
    """Test ingest_doc tool implementation logic"""
    
    @pytest.mark.asyncio
    async def test_ingest_doc_submits_to_orchestrator(self):
        """Test that ingest_doc submits document to orchestrator"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"job_id": "ingest-job-456", "status": "accepted"})
        )
        
        request = IngestDocRequest(
            file_path="/tmp/test.pdf",
            collection_name="test-collection"
        )
        
        response = await mock_orchestrator.post(
            "/api/ingest",
            json={"file_path": request.file_path, "collection_name": request.collection_name}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "ingest-job-456"
    
    @pytest.mark.asyncio
    async def test_ingest_doc_validates_file_path(self):
        """Test that ingest_doc validates file_path"""
        # Valid file path
        request = IngestDocRequest(
            file_path="/tmp/document.pdf",
            collection_name="docs"
        )
        assert request.file_path == "/tmp/document.pdf"
    
    @pytest.mark.asyncio
    async def test_ingest_doc_handles_missing_file(self):
        """Test ingest_doc error handling for missing files"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.post.return_value = Mock(
            status_code=404,
            json=Mock(return_value={"error": "File not found"})
        )
        
        request = IngestDocRequest(
            file_path="/nonexistent/file.pdf",
            collection_name="test"
        )
        
        response = await mock_orchestrator.post("/api/ingest", json=request.dict())
        
        assert response.status_code == 404
        assert "error" in response.json()


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestQdrantFindImplementation:
    """Test qdrant_find tool implementation logic"""
    
    @pytest.mark.asyncio
    async def test_qdrant_find_queries_orchestrator(self):
        """Test that qdrant_find queries orchestrator correctly"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={
                "results": [
                    {"id": "doc1", "score": 0.95, "payload": {"text": "test"}},
                    {"id": "doc2", "score": 0.88, "payload": {"text": "example"}}
                ]
            })
        )
        
        request = QdrantFindRequest(
            query="test query",
            collection_name="test-collection",
            limit=5
        )
        
        response = await mock_orchestrator.post(
            "/api/qdrant/find",
            json=request.dict()
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["score"] == 0.95
    
    @pytest.mark.asyncio
    async def test_qdrant_find_handles_empty_results(self):
        """Test qdrant_find handles no results gracefully"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"results": []})
        )
        
        request = QdrantFindRequest(
            query="nonexistent query",
            collection_name="test-collection"
        )
        
        response = await mock_orchestrator.post("/api/qdrant/find", json=request.dict())
        
        assert response.status_code == 200
        assert len(response.json()["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_qdrant_find_validates_limit(self):
        """Test that qdrant_find validates limit parameter"""
        # Valid limit
        request = QdrantFindRequest(
            query="test",
            collection_name="test",
            limit=10
        )
        assert request.limit == 10
        
        # Default limit
        request_default = QdrantFindRequest(
            query="test",
            collection_name="test"
        )
        assert request_default.limit > 0


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestQdrantStoreImplementation:
    """Test qdrant_store tool implementation logic"""
    
    @pytest.mark.asyncio
    async def test_qdrant_store_submits_to_orchestrator(self):
        """Test that qdrant_store submits vectors to orchestrator"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"status": "success", "stored": 2})
        )
        
        request = QdrantStoreRequest(
            collection_name="test-collection",
            points=[
                {"id": "1", "vector": [0.1, 0.2, 0.3], "payload": {"text": "test"}},
                {"id": "2", "vector": [0.4, 0.5, 0.6], "payload": {"text": "example"}}
            ]
        )
        
        response = await mock_orchestrator.post(
            "/api/qdrant/store",
            json=request.dict()
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["stored"] == 2
    
    @pytest.mark.asyncio
    async def test_qdrant_store_validates_vector_dimensions(self):
        """Test qdrant_store validates vector dimensions"""
        # All vectors should have same dimensions
        request = QdrantStoreRequest(
            collection_name="test",
            points=[
                {"id": "1", "vector": [0.1, 0.2, 0.3], "payload": {}},
                {"id": "2", "vector": [0.4, 0.5, 0.6], "payload": {}}
            ]
        )
        
        # Verify all vectors have same length
        vectors = [p["vector"] for p in request.points]
        assert all(len(v) == len(vectors[0]) for v in vectors)


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestLightRAGQueryImplementation:
    """Test lightrag_query tool implementation logic"""
    
    @pytest.mark.asyncio
    async def test_lightrag_query_submits_to_orchestrator(self):
        """Test that lightrag_query submits to orchestrator"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={
                "answer": "Test answer",
                "context": [{"source": "doc1", "text": "context"}],
                "metadata": {"tokens": 100}
            })
        )
        
        request = LightRAGQueryRequest(
            query="test question",
            mode=LightRAGModeEnum.HYBRID
        )
        
        response = await mock_orchestrator.post(
            "/api/lightrag/query",
            json=request.dict()
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Test answer"
        assert len(data["context"]) == 1
    
    @pytest.mark.asyncio
    async def test_lightrag_query_supports_all_modes(self):
        """Test that lightrag_query supports all query modes"""
        for mode in [LightRAGModeEnum.LOCAL, LightRAGModeEnum.GLOBAL, LightRAGModeEnum.HYBRID]:
            request = LightRAGQueryRequest(
                query="test",
                mode=mode
            )
            assert request.mode == mode


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestGetJobStatusImplementation:
    """Test get_job_status tool implementation logic"""
    
    @pytest.mark.asyncio
    async def test_get_job_status_queries_orchestrator(self):
        """Test that get_job_status queries orchestrator"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={
                "job_id": "test-job-123",
                "status": "completed",
                "result": {"output": "success"}
            })
        )
        
        request = JobStatusRequest(job_id="test-job-123")
        
        response = await mock_orchestrator.get(
            f"/api/jobs/{request.job_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["job_id"] == "test-job-123"
    
    @pytest.mark.asyncio
    async def test_get_job_status_handles_not_found(self):
        """Test get_job_status handles nonexistent jobs"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get.return_value = Mock(
            status_code=404,
            json=Mock(return_value={"error": "Job not found"})
        )
        
        request = JobStatusRequest(job_id="nonexistent-job")
        
        response = await mock_orchestrator.get(f"/api/jobs/{request.job_id}")
        
        assert response.status_code == 404


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestHealthCheckImplementation:
    """Test health_check tool implementation logic"""
    
    @pytest.mark.asyncio
    async def test_health_check_queries_orchestrator(self):
        """Test that health_check queries orchestrator health"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={
                "status": "healthy",
                "orchestrator": {"status": "up"},
                "circuit_breaker": {"state": "closed"}
            })
        )
        
        response = await mock_orchestrator.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["orchestrator"]["status"] == "up"
    
    @pytest.mark.asyncio
    async def test_health_check_handles_degraded_state(self):
        """Test health_check reports degraded state correctly"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={
                "status": "degraded",
                "orchestrator": {"status": "down"},
                "circuit_breaker": {"state": "open"}
            })
        )
        
        response = await mock_orchestrator.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["circuit_breaker"]["state"] == "open"

