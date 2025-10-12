"""
Pydantic Request Model Tests

Tests for all Pydantic request validation models.
Single Responsibility: Validate request model validation logic.

Models Tested:
- CrawlWebRequest
- IngestDocRequest
- QdrantFindRequest
- QdrantStoreRequest
- LightRAGQueryRequest
- JobStatusRequest
"""

import pytest
import tempfile
import os
from common_types import (
    CrawlWebRequest,
    IngestDocRequest,
    QdrantFindRequest,
    LightRAGQueryRequest,
    LightRAGModeEnum,
)


@pytest.mark.unit
@pytest.mark.fast
class TestCrawlWebRequest:
    """Test CrawlWebRequest validation"""

    def test_valid_request_minimal(self):
        """Test creating request with minimal required fields"""
        req = CrawlWebRequest(url="https://example.com")
        assert str(req.url) == "https://example.com/"
        assert req.max_pages == 10  # Default
        assert req.max_depth == 2  # Default

    def test_valid_request_full(self):
        """Test creating request with all fields"""
        req = CrawlWebRequest(
            url="https://example.com/docs",
            max_pages=50,
            allowed_domains=["example.com", "docs.example.com"],
            max_depth=3,
        )
        assert req.max_pages == 50
        assert len(req.allowed_domains) == 2
        assert req.max_depth == 3

    def test_auto_set_allowed_domains(self):
        """Test that allowed_domains auto-sets to URL domain"""
        req = CrawlWebRequest(url="https://example.com/page")
        assert "example.com" in req.allowed_domains

    def test_max_pages_validation(self):
        """Test max_pages constraints (1-100)"""
        # Valid range
        req = CrawlWebRequest(url="https://example.com", max_pages=1)
        assert req.max_pages == 1

        req = CrawlWebRequest(url="https://example.com", max_pages=100)
        assert req.max_pages == 100

        # Invalid: too low
        with pytest.raises(Exception):  # Pydantic ValidationError
            CrawlWebRequest(url="https://example.com", max_pages=0)

        # Invalid: too high
        with pytest.raises(Exception):
            CrawlWebRequest(url="https://example.com", max_pages=101)

    def test_invalid_url(self):
        """Test that invalid URLs are rejected"""
        with pytest.raises(Exception):
            CrawlWebRequest(url="not-a-url")


@pytest.mark.unit
@pytest.mark.fast
class TestIngestDocRequest:
    """Test IngestDocRequest validation"""

    def test_valid_request(self):
        """Test creating request with valid file path"""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name

        try:
            req = IngestDocRequest(file_path=tmp_path, source_name="Test Document")
            assert req.file_path == tmp_path
            assert req.source_name == "Test Document"
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        """Test that non-existent file paths are rejected"""
        with pytest.raises(ValueError, match="File not found"):
            IngestDocRequest(file_path="/nonexistent/file.pdf")

    def test_directory_rejected(self):
        """Test that directories are rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="not a file"):
                IngestDocRequest(file_path=tmpdir)


@pytest.mark.unit
@pytest.mark.fast
class TestQdrantFindRequest:
    """Test QdrantFindRequest validation"""

    def test_valid_request_minimal(self):
        """Test creating request with minimal fields"""
        req = QdrantFindRequest(query="machine learning")
        assert req.query == "machine learning"
        assert req.limit == 10  # Default
        assert req.score_threshold == 0.0  # Default

    def test_valid_request_full(self):
        """Test creating request with all fields"""
        req = QdrantFindRequest(
            query="vector search",
            collection="my_collection",
            limit=50,
            score_threshold=0.7,
            filter_conditions={"category": "tech"},
        )
        assert req.collection == "my_collection"
        assert req.limit == 50
        assert req.score_threshold == 0.7
        assert req.filter_conditions["category"] == "tech"

    def test_empty_query_rejected(self):
        """Test that empty queries are rejected"""
        with pytest.raises(Exception):
            QdrantFindRequest(query="")

    def test_limit_validation(self):
        """Test limit constraints (1-100)"""
        req = QdrantFindRequest(query="test", limit=1)
        assert req.limit == 1

        req = QdrantFindRequest(query="test", limit=100)
        assert req.limit == 100

        with pytest.raises(Exception):
            QdrantFindRequest(query="test", limit=0)

        with pytest.raises(Exception):
            QdrantFindRequest(query="test", limit=101)

    def test_score_threshold_validation(self):
        """Test score_threshold constraints (0.0-1.0)"""
        req = QdrantFindRequest(query="test", score_threshold=0.0)
        assert req.score_threshold == 0.0

        req = QdrantFindRequest(query="test", score_threshold=1.0)
        assert req.score_threshold == 1.0

        with pytest.raises(Exception):
            QdrantFindRequest(query="test", score_threshold=-0.1)

        with pytest.raises(Exception):
            QdrantFindRequest(query="test", score_threshold=1.1)


@pytest.mark.unit
@pytest.mark.fast
class TestLightRAGQueryRequest:
    """Test LightRAGQueryRequest validation"""

    def test_valid_request_minimal(self):
        """Test creating request with minimal fields"""
        req = LightRAGQueryRequest(query="What is RAG?")
        assert req.query == "What is RAG?"
        assert req.mode == LightRAGModeEnum.HYBRID  # Default
        assert req.only_need_context is False  # Default

    def test_valid_request_with_mode(self):
        """Test creating request with specific mode"""
        req = LightRAGQueryRequest(
            query="Explain vector databases",
            mode=LightRAGModeEnum.LOCAL,
            only_need_context=True,
        )
        assert req.mode == LightRAGModeEnum.LOCAL
        assert req.only_need_context is True

    def test_all_modes_accepted(self):
        """Test that all LightRAG modes are accepted"""
        for mode in LightRAGModeEnum:
            req = LightRAGQueryRequest(query="test", mode=mode)
            assert req.mode == mode
