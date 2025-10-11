"""
Pydantic Response Model Tests

Tests for all Pydantic response models.
Single Responsibility: Validate response model structure and creation.

Models Tested:
- CrawlWebResponse
- IngestDocResponse
- QdrantFindResponse
- LightRAGQueryResponse
"""

import pytest
from common_types import (
    CrawlWebResponse,
    IngestDocResponse,
    QdrantFindResponse,
    LightRAGQueryResponse,
    MCPResponseStatusEnum,
)


@pytest.mark.unit
@pytest.mark.fast
class TestCrawlWebResponse:
    """Test CrawlWebResponse model"""

    def test_success_response(self):
        """Test creating success response"""
        resp = CrawlWebResponse(
            status=MCPResponseStatusEnum.SUCCESS,
            message="Crawl completed",
            pages_crawled=5,
            source_url="https://example.com"
        )
        assert resp.status == MCPResponseStatusEnum.SUCCESS
        assert resp.pages_crawled == 5

    def test_accepted_response_http_202(self):
        """Test creating HTTP 202 accepted response"""
        resp = CrawlWebResponse(
            status=MCPResponseStatusEnum.ACCEPTED,
            message="Crawl started",
            job_id="job-123",
            pages_crawled=0,
            check_status_endpoint="/jobs/job-123"
        )
        assert resp.status == MCPResponseStatusEnum.ACCEPTED
        assert resp.job_id == "job-123"
        assert resp.check_status_endpoint == "/jobs/job-123"

    def test_error_response(self):
        """Test creating error response"""
        resp = CrawlWebResponse(
            status=MCPResponseStatusEnum.ERROR,
            pages_crawled=0,
            error="Connection timeout",
            error_type="http_error",
            retry_after=60
        )
        assert resp.status == MCPResponseStatusEnum.ERROR
        assert resp.error == "Connection timeout"
        assert resp.retry_after == 60


@pytest.mark.unit
@pytest.mark.fast
class TestQdrantFindResponse:
    """Test QdrantFindResponse model"""

    def test_success_with_results(self):
        """Test response with search results"""
        resp = QdrantFindResponse(
            status=MCPResponseStatusEnum.SUCCESS,
            query="machine learning",
            collection="shield_kb",
            result_count=3,
            results=[
                {"id": "point-1", "score": 0.95, "payload": {"text": "ML content"}},
                {"id": "point-2", "score": 0.87, "payload": {"text": "AI content"}},
                {"id": "point-3", "score": 0.75, "payload": {"text": "Data content"}}
            ],
            score_threshold=0.7,
            embedding_model="nomic-embed-text"
        )
        assert resp.result_count == 3
        assert len(resp.results) == 3
        assert resp.results[0]["score"] == 0.95

    def test_no_results(self):
        """Test response with no results"""
        resp = QdrantFindResponse(
            status=MCPResponseStatusEnum.SUCCESS,
            query="nonexistent term",
            result_count=0,
            results=[]
        )
        assert resp.result_count == 0
        assert len(resp.results) == 0
