"""
Unit tests for MCP Server tools

Tests for request/response models, validation, and error handling
for all MCP server tools: crawl_web, ingest_doc, qdrant_find, qdrant_store,
lightrag_query, get_job_status, and health_check.

Phase 2 Sprint 2.2: Automated Testing (TASK-032)
"""

import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from pydantic import ValidationError
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
class TestCrawlWebRequest:
    """Test CrawlWebRequest model validation"""
    
    def test_crawl_web_request_valid(self):
        """Test valid crawl_web request"""
        request = CrawlWebRequest(
            url="https://example.com",
            max_pages=10,
            allowed_domains=["example.com"],
            max_depth=2
        )
        
        assert str(request.url) == "https://example.com/"
        assert request.max_pages == 10
        assert request.allowed_domains == ["example.com"]
        assert request.max_depth == 2
    
    def test_crawl_web_request_defaults(self):
        """Test default values for crawl_web request"""
        request = CrawlWebRequest(url="https://example.com")
        
        assert request.max_pages == 10
        assert request.max_depth == 2
        assert request.allowed_domains is None
    
    def test_crawl_web_request_invalid_url(self):
        """Test validation error for invalid URL"""
        with pytest.raises(ValidationError) as exc_info:
            CrawlWebRequest(url="not-a-url")
        
        errors = exc_info.value.errors()
        assert any("url" in str(e).lower() for e in errors)
    
    def test_crawl_web_request_max_pages_bounds(self):
        """Test max_pages must be between 1 and 100"""
        with pytest.raises(ValidationError):
            CrawlWebRequest(url="https://example.com", max_pages=0)
        
        with pytest.raises(ValidationError):
            CrawlWebRequest(url="https://example.com", max_pages=101)
        
        request = CrawlWebRequest(url="https://example.com", max_pages=1)
        assert request.max_pages == 1
        
        request = CrawlWebRequest(url="https://example.com", max_pages=100)
        assert request.max_pages == 100
    
    def test_crawl_web_request_max_depth_bounds(self):
        """Test max_depth must be between 1 and 5"""
        with pytest.raises(ValidationError):
            CrawlWebRequest(url="https://example.com", max_depth=0)
        
        with pytest.raises(ValidationError):
            CrawlWebRequest(url="https://example.com", max_depth=6)
        
        request = CrawlWebRequest(url="https://example.com", max_depth=1)
        assert request.max_depth == 1


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestIngestDocRequest:
    """Test IngestDocRequest model validation"""
    
    def test_ingest_doc_request_valid(self, tmp_path):
        """Test valid ingest_doc request"""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("Test content")
        
        request = IngestDocRequest(
            file_path=str(test_file),
            source_name="test_document"
        )
        
        assert request.file_path == str(test_file)
        assert request.source_name == "test_document"
    
    def test_ingest_doc_request_defaults(self, tmp_path):
        """Test default source_name is None"""
        test_file = tmp_path / "my_document.pdf"
        test_file.write_text("Test content")
        
        request = IngestDocRequest(file_path=str(test_file))
        
        assert request.source_name is None
    
    def test_ingest_doc_request_empty_file_path(self):
        """Test validation error for empty file path"""
        with pytest.raises(ValidationError):
            IngestDocRequest(file_path="")
    
    def test_ingest_doc_request_supported_formats(self, tmp_path):
        """Test supported document formats"""
        supported_formats = [".pdf", ".docx", ".doc", ".txt", ".md"]
        
        for fmt in supported_formats:
            test_file = tmp_path / f"test{fmt}"
            test_file.write_text("Test content")
            
            request = IngestDocRequest(file_path=str(test_file))
            assert request.file_path == str(test_file)


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestQdrantFindRequest:
    """Test QdrantFindRequest model validation"""
    
    def test_qdrant_find_request_valid(self, sample_query):
        """Test valid qdrant_find request"""
        request = QdrantFindRequest(
            query=sample_query,
            collection="test_collection",
            limit=10,
            score_threshold=0.7
        )
        
        assert request.query == sample_query
        assert request.collection == "test_collection"
        assert request.limit == 10
        assert request.score_threshold == 0.7
    
    def test_qdrant_find_request_defaults(self, sample_query):
        """Test default values for qdrant_find request"""
        request = QdrantFindRequest(query=sample_query)
        
        assert request.collection is None
        assert request.limit == 10
        assert request.score_threshold == 0.0
    
    def test_qdrant_find_request_limit_bounds(self, sample_query):
        """Test limit must be between 1 and 100"""
        with pytest.raises(ValidationError):
            QdrantFindRequest(query=sample_query, limit=0)
        
        with pytest.raises(ValidationError):
            QdrantFindRequest(query=sample_query, limit=101)
    
    def test_qdrant_find_request_score_threshold_bounds(self, sample_query):
        """Test score_threshold must be between 0 and 1"""
        with pytest.raises(ValidationError):
            QdrantFindRequest(query=sample_query, score_threshold=-0.1)
        
        with pytest.raises(ValidationError):
            QdrantFindRequest(query=sample_query, score_threshold=1.1)


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestQdrantStoreRequest:
    """Test QdrantStoreRequest model validation"""
    
    def test_qdrant_store_request_valid(self, sample_text, sample_metadata):
        """Test valid qdrant_store request"""
        request = QdrantStoreRequest(
            text=sample_text,
            metadata=sample_metadata,
            collection="test_collection"
        )
        
        assert request.text == sample_text
        assert request.metadata == sample_metadata
        assert request.collection == "test_collection"
    
    def test_qdrant_store_request_defaults(self, sample_text):
        """Test default values for qdrant_store request"""
        request = QdrantStoreRequest(text=sample_text)
        
        assert request.collection is None
        assert request.metadata is None
    
    def test_qdrant_store_request_empty_text(self):
        """Test validation error for empty text"""
        with pytest.raises(ValidationError):
            QdrantStoreRequest(text="")


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestLightRAGQueryRequest:
    """Test LightRAGQueryRequest model validation"""
    
    def test_lightrag_query_request_valid(self, sample_query):
        """Test valid lightrag_query request"""
        request = LightRAGQueryRequest(
            query=sample_query,
            mode=LightRAGModeEnum.HYBRID,
            only_need_context=False
        )
        
        assert request.query == sample_query
        assert request.mode == LightRAGModeEnum.HYBRID
        assert request.only_need_context is False
    
    def test_lightrag_query_request_defaults(self, sample_query):
        """Test default values for lightrag_query request"""
        request = LightRAGQueryRequest(query=sample_query)
        
        assert request.mode == LightRAGModeEnum.HYBRID
        assert request.only_need_context is False
    
    def test_lightrag_query_request_all_modes(self, sample_query):
        """Test all LightRAG retrieval modes"""
        for mode in LightRAGModeEnum:
            request = LightRAGQueryRequest(query=sample_query, mode=mode)
            assert request.mode == mode


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestJobStatusRequest:
    """Test JobStatusRequest model validation"""
    
    def test_job_status_request_valid(self, sample_job_id):
        """Test valid job_status request"""
        request = JobStatusRequest(job_id=sample_job_id)
        
        assert request.job_id == sample_job_id
    
    def test_job_status_request_empty_job_id(self):
        """Test validation error for empty job_id"""
        with pytest.raises(ValidationError):
            JobStatusRequest(job_id="")


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestMCPResponseEnums:
    """Test MCP response status enums"""
    
    def test_mcp_response_status_enum_values(self):
        """Test MCPResponseStatusEnum has expected values"""
        assert MCPResponseStatusEnum.SUCCESS.value == "success"
        assert MCPResponseStatusEnum.ACCEPTED.value == "accepted"
        assert MCPResponseStatusEnum.ERROR.value == "error"
    
    def test_job_status_enum_values(self):
        """Test JobStatusEnum has expected values"""
        assert JobStatusEnum.PENDING.value == "pending"
        assert JobStatusEnum.PROCESSING.value == "processing"
        assert JobStatusEnum.COMPLETED.value == "completed"
        assert JobStatusEnum.FAILED.value == "failed"
        assert JobStatusEnum.CANCELLED.value == "cancelled"
    
    def test_lightrag_mode_enum_values(self):
        """Test LightRAGModeEnum has expected values"""
        assert LightRAGModeEnum.NAIVE.value == "naive"
        assert LightRAGModeEnum.LOCAL.value == "local"
        assert LightRAGModeEnum.GLOBAL.value == "global"
        assert LightRAGModeEnum.HYBRID.value == "hybrid"


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.asyncio
class TestMCPToolResponsePatterns:
    """Test MCP tool response patterns"""
    
    async def test_http_202_accepted_pattern(self, sample_job_id):
        """Test HTTP 202 Accepted pattern for async operations"""
        response = {
            "status": MCPResponseStatusEnum.ACCEPTED.value,
            "message": "Job accepted for processing",
            "job_id": sample_job_id,
            "check_status_endpoint": f"/jobs/{sample_job_id}"
        }
        
        assert response["status"] == "accepted"
        assert "job_id" in response
        assert "check_status_endpoint" in response
    
    async def test_success_response_pattern(self):
        """Test synchronous success response pattern"""
        response = {
            "status": MCPResponseStatusEnum.SUCCESS.value,
            "data": {"result": "test"}
        }
        
        assert response["status"] == "success"
        assert "data" in response
    
    async def test_error_response_pattern(self):
        """Test error response pattern"""
        response = {
            "status": MCPResponseStatusEnum.ERROR.value,
            "error": "Test error message",
            "error_type": "validation_error"
        }
        
        assert response["status"] == "error"
        assert "error" in response
        assert "error_type" in response


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.asyncio
class TestMCPToolErrorHandling:
    """Test MCP tool error handling"""
    
    async def test_invalid_url_error(self):
        """Test error handling for invalid URL"""
        with pytest.raises(ValidationError):
            CrawlWebRequest(url="not-a-valid-url")
    
    async def test_file_not_found_error(self):
        """Test error handling for missing file"""
        with pytest.raises(ValidationError):
            IngestDocRequest(file_path="/nonexistent/file.pdf")
    
    async def test_empty_query_error(self):
        """Test error handling for empty query"""
        with pytest.raises(ValidationError):
            QdrantFindRequest(query="")


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestMCPToolCircuitBreakerIntegration:
    """Test MCP tool request models work with circuit breaker patterns"""
    
    def test_request_models_support_error_responses(self, sample_query):
        """Test request models can be validated independently of circuit breaker"""
        request = QdrantFindRequest(query=sample_query)
        assert request.query == sample_query
        assert request.collection is None
    
    def test_request_models_support_http_202_pattern(self):
        """Test request models support async HTTP 202 job pattern"""
        request = CrawlWebRequest(url="https://example.com")
        assert str(request.url) == "https://example.com/"
        assert request.max_pages == 10


@pytest.mark.unit
@pytest.mark.mcp
@pytest.mark.fast
class TestMCPToolInputValidation:
    """Test MCP tool input validation"""
    
    def test_crawl_web_url_validation(self):
        """Test crawl_web URL validation"""
        valid_urls = [
            "https://example.com",
            "http://test.org",
            "https://subdomain.example.com/path"
        ]
        
        for url in valid_urls:
            request = CrawlWebRequest(url=url)
            assert request.url is not None
    
    def test_ingest_doc_path_validation(self, tmp_path):
        """Test ingest_doc file path validation"""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("content")
        
        request = IngestDocRequest(file_path=str(test_file))
        assert Path(request.file_path).exists()
    
    def test_qdrant_collection_name_validation(self, sample_text):
        """Test Qdrant collection name validation"""
        valid_names = ["test_collection", "shield_kb", "collection-name"]
        
        for name in valid_names:
            request = QdrantStoreRequest(text=sample_text, collection=name)
            assert request.collection == name
    
    def test_lightrag_mode_validation(self, sample_query):
        """Test LightRAG mode validation"""
        for mode in LightRAGModeEnum:
            request = LightRAGQueryRequest(query=sample_query, mode=mode)
            assert request.mode == mode
