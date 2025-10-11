"""
Unit tests for common_types module

Phase 2 Sprint 2.2: Automated Testing (TASK-032)

This is a CRITICAL test suite that validates the foundation of the entire
HX-Citadel Shield type system. All type definitions, validators, and utility
functions must be thoroughly tested.

Coverage Target: 100% (this is the foundation)
"""

import pytest
from typing import Dict, Any
from pathlib import Path
import tempfile
import os


# Import common_types from the deployed location
# Note: This will be available after deployment
try:
    import sys
    # Add the MCP server common_types to path
    sys.path.insert(0, "/tmp/common_types_test")
    from common_types import (
        # Enums
        JobStatusEnum,
        HealthStatusEnum,
        CircuitBreakerStateEnum,
        LightRAGModeEnum,
        MCPResponseStatusEnum,
        # Pydantic Models
        CrawlWebRequest,
        IngestDocRequest,
        QdrantFindRequest,
        QdrantStoreRequest,
        LightRAGQueryRequest,
        JobStatusRequest,
        CrawlWebResponse,
        IngestDocResponse,
        QdrantFindResponse,
        LightRAGQueryResponse,
        # Utility Functions
        create_error_response,
        create_job_status_response,
        # Type Guards
        is_valid_job_status,
        is_valid_health_status,
        is_valid_lightrag_mode,
        # Constants
        SUPPORTED_DOCUMENT_FORMATS,
        DEFAULT_QDRANT_COLLECTION,
        DEFAULT_EMBEDDING_MODEL,
        DEFAULT_MAX_PAGES,
        DEFAULT_CIRCUIT_FAIL_MAX,
    )
    COMMON_TYPES_AVAILABLE = True
except ImportError:
    COMMON_TYPES_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not COMMON_TYPES_AVAILABLE,
    reason="common_types module not available (needs deployment)"
)


# ==========================================
# Enum Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.fast
class TestJobStatusEnum:
    """Test JobStatusEnum values and behavior"""

    def test_all_values_present(self):
        """Test all expected job status values exist"""
        expected_values = ["pending", "processing", "completed", "failed", "cancelled"]
        actual_values = [status.value for status in JobStatusEnum]
        assert set(actual_values) == set(expected_values)
        assert len(actual_values) == 5

    def test_enum_is_string(self):
        """Test that enum values are strings"""
        for status in JobStatusEnum:
            assert isinstance(status.value, str)

    def test_enum_access(self):
        """Test accessing enum by name"""
        assert JobStatusEnum.PENDING.value == "pending"
        assert JobStatusEnum.PROCESSING.value == "processing"
        assert JobStatusEnum.COMPLETED.value == "completed"
        assert JobStatusEnum.FAILED.value == "failed"
        assert JobStatusEnum.CANCELLED.value == "cancelled"

    def test_enum_comparison(self):
        """Test enum comparison works correctly"""
        assert JobStatusEnum.PENDING == JobStatusEnum.PENDING
        assert JobStatusEnum.COMPLETED != JobStatusEnum.FAILED


@pytest.mark.unit
@pytest.mark.fast
class TestHealthStatusEnum:
    """Test HealthStatusEnum values"""

    def test_all_values_present(self):
        """Test all health status values exist"""
        expected_values = ["healthy", "degraded", "unhealthy", "unknown"]
        actual_values = [status.value for status in HealthStatusEnum]
        assert set(actual_values) == set(expected_values)
        assert len(actual_values) == 4

    def test_healthy_status(self):
        """Test healthy status value"""
        assert HealthStatusEnum.HEALTHY.value == "healthy"

    def test_degraded_status(self):
        """Test degraded status value"""
        assert HealthStatusEnum.DEGRADED.value == "degraded"


@pytest.mark.unit
@pytest.mark.fast
class TestCircuitBreakerStateEnum:
    """Test CircuitBreakerStateEnum values"""

    def test_all_states_present(self):
        """Test all circuit breaker states exist"""
        expected_states = ["closed", "open", "half_open"]
        actual_states = [state.value for state in CircuitBreakerStateEnum]
        assert set(actual_states) == set(expected_states)
        assert len(actual_states) == 3

    def test_closed_state(self):
        """Test closed (normal operation) state"""
        assert CircuitBreakerStateEnum.CLOSED.value == "closed"

    def test_open_state(self):
        """Test open (failing fast) state"""
        assert CircuitBreakerStateEnum.OPEN.value == "open"

    def test_half_open_state(self):
        """Test half_open (testing recovery) state"""
        assert CircuitBreakerStateEnum.HALF_OPEN.value == "half_open"


@pytest.mark.unit
@pytest.mark.fast
class TestLightRAGModeEnum:
    """Test LightRAGModeEnum values"""

    def test_all_modes_present(self):
        """Test all LightRAG modes exist"""
        expected_modes = ["naive", "local", "global", "hybrid"]
        actual_modes = [mode.value for mode in LightRAGModeEnum]
        assert set(actual_modes) == set(expected_modes)
        assert len(actual_modes) == 4

    def test_hybrid_mode_default(self):
        """Test hybrid mode (recommended default)"""
        assert LightRAGModeEnum.HYBRID.value == "hybrid"


@pytest.mark.unit
@pytest.mark.fast
class TestMCPResponseStatusEnum:
    """Test MCPResponseStatusEnum values"""

    def test_all_statuses_present(self):
        """Test all MCP response statuses exist"""
        expected_statuses = ["success", "accepted", "error"]
        actual_statuses = [status.value for status in MCPResponseStatusEnum]
        assert set(actual_statuses) == set(expected_statuses)
        assert len(actual_statuses) == 3

    def test_http_202_accepted_pattern(self):
        """Test that ACCEPTED status exists for HTTP 202 pattern"""
        assert MCPResponseStatusEnum.ACCEPTED.value == "accepted"


# ==========================================
# Pydantic Request Model Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.fast
class TestCrawlWebRequest:
    """Test CrawlWebRequest validation"""

    def test_valid_request_minimal(self):
        """Test creating request with minimal required fields"""
        req = CrawlWebRequest(url="https://example.com")
        assert str(req.url) == "https://example.com/"
        assert req.max_pages == 10  # Default
        assert req.max_depth == 2   # Default

    def test_valid_request_full(self):
        """Test creating request with all fields"""
        req = CrawlWebRequest(
            url="https://example.com/docs",
            max_pages=50,
            allowed_domains=["example.com", "docs.example.com"],
            max_depth=3
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
            filter_conditions={"category": "tech"}
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
            only_need_context=True
        )
        assert req.mode == LightRAGModeEnum.LOCAL
        assert req.only_need_context is True

    def test_all_modes_accepted(self):
        """Test that all LightRAG modes are accepted"""
        for mode in LightRAGModeEnum:
            req = LightRAGQueryRequest(query="test", mode=mode)
            assert req.mode == mode


# ==========================================
# Pydantic Response Model Tests
# ==========================================

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


# ==========================================
# Utility Function Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.fast
class TestCreateErrorResponse:
    """Test create_error_response() utility"""

    def test_minimal_error(self):
        """Test creating minimal error response"""
        resp = create_error_response(
            error="Something went wrong",
            error_type="generic_error"
        )
        assert resp["status"] == "error"
        assert resp["error"] == "Something went wrong"
        assert resp["error_type"] == "generic_error"
        assert "status_code" not in resp
        assert "retry_after" not in resp

    def test_error_with_status_code(self):
        """Test error response with HTTP status code"""
        resp = create_error_response(
            error="Not found",
            error_type="http_error",
            status_code=404
        )
        assert resp["status_code"] == 404

    def test_error_with_retry_after(self):
        """Test error response with retry delay"""
        resp = create_error_response(
            error="Rate limited",
            error_type="rate_limit_error",
            retry_after=120
        )
        assert resp["retry_after"] == 120

    def test_error_with_all_fields(self):
        """Test error response with all optional fields"""
        resp = create_error_response(
            error="Service unavailable",
            error_type="service_error",
            status_code=503,
            retry_after=60
        )
        assert resp["status"] == "error"
        assert resp["error"] == "Service unavailable"
        assert resp["error_type"] == "service_error"
        assert resp["status_code"] == 503
        assert resp["retry_after"] == 60


@pytest.mark.unit
@pytest.mark.fast
class TestCreateJobStatusResponse:
    """Test create_job_status_response() utility"""

    def test_pending_job(self):
        """Test creating response for pending job"""
        resp = create_job_status_response(
            job_id="job-123",
            job_status=JobStatusEnum.PENDING,
            progress=0,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:00:00Z"
        )
        assert resp["job_id"] == "job-123"
        assert resp["job_status"] == JobStatusEnum.PENDING
        assert resp["progress"] == 0
        assert resp["status"] == MCPResponseStatusEnum.SUCCESS

    def test_processing_job_with_progress(self):
        """Test response for job in progress"""
        resp = create_job_status_response(
            job_id="job-456",
            job_status=JobStatusEnum.PROCESSING,
            progress=50,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:05:00Z",
            metadata={"pages_processed": 25}
        )
        assert resp["progress"] == 50
        assert resp["job_status"] == JobStatusEnum.PROCESSING
        assert resp["metadata"]["pages_processed"] == 25

    def test_completed_job_with_result(self):
        """Test response for completed job"""
        resp = create_job_status_response(
            job_id="job-789",
            job_status=JobStatusEnum.COMPLETED,
            progress=100,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:10:00Z",
            result={"documents_indexed": 100, "vectors_created": 100}
        )
        assert resp["progress"] == 100
        assert resp["job_status"] == JobStatusEnum.COMPLETED
        assert resp["result"]["documents_indexed"] == 100

    def test_failed_job_with_error(self):
        """Test response for failed job"""
        resp = create_job_status_response(
            job_id="job-fail",
            job_status=JobStatusEnum.FAILED,
            progress=30,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:03:00Z",
            error="Connection timeout to Qdrant"
        )
        assert resp["job_status"] == JobStatusEnum.FAILED
        assert resp["error"] == "Connection timeout to Qdrant"

    def test_progress_clamping(self):
        """Test that progress is clamped to 0-100 range"""
        # Below 0
        resp = create_job_status_response(
            job_id="job-1",
            job_status=JobStatusEnum.PENDING,
            progress=-10,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:00:00Z"
        )
        assert resp["progress"] == 0

        # Above 100
        resp = create_job_status_response(
            job_id="job-2",
            job_status=JobStatusEnum.COMPLETED,
            progress=150,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:00:00Z"
        )
        assert resp["progress"] == 100


# ==========================================
# Type Guard Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.fast
class TestTypeGuards:
    """Test runtime type checking functions"""

    def test_is_valid_job_status(self):
        """Test job status validation"""
        assert is_valid_job_status("pending") is True
        assert is_valid_job_status("processing") is True
        assert is_valid_job_status("completed") is True
        assert is_valid_job_status("failed") is True
        assert is_valid_job_status("cancelled") is True

        assert is_valid_job_status("invalid") is False
        assert is_valid_job_status("PENDING") is False  # Case sensitive
        assert is_valid_job_status("") is False

    def test_is_valid_health_status(self):
        """Test health status validation"""
        assert is_valid_health_status("healthy") is True
        assert is_valid_health_status("degraded") is True
        assert is_valid_health_status("unhealthy") is True
        assert is_valid_health_status("unknown") is True

        assert is_valid_health_status("invalid") is False
        assert is_valid_health_status("OK") is False

    def test_is_valid_lightrag_mode(self):
        """Test LightRAG mode validation"""
        assert is_valid_lightrag_mode("naive") is True
        assert is_valid_lightrag_mode("local") is True
        assert is_valid_lightrag_mode("global") is True
        assert is_valid_lightrag_mode("hybrid") is True

        assert is_valid_lightrag_mode("invalid") is False
        assert is_valid_lightrag_mode("HYBRID") is False  # Case sensitive


# ==========================================
# Constants Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.fast
class TestConstants:
    """Test module constants"""

    def test_supported_document_formats(self):
        """Test supported document format list"""
        assert ".pdf" in SUPPORTED_DOCUMENT_FORMATS
        assert ".docx" in SUPPORTED_DOCUMENT_FORMATS
        assert ".txt" in SUPPORTED_DOCUMENT_FORMATS
        assert ".md" in SUPPORTED_DOCUMENT_FORMATS

    def test_default_values(self):
        """Test default configuration values"""
        assert DEFAULT_QDRANT_COLLECTION == "shield_knowledge_base"
        assert DEFAULT_EMBEDDING_MODEL == "nomic-embed-text"
        assert DEFAULT_MAX_PAGES == 10
        assert DEFAULT_MAX_PAGES > 0
        assert DEFAULT_MAX_PAGES <= 100

    def test_circuit_breaker_defaults(self):
        """Test circuit breaker default values"""
        assert DEFAULT_CIRCUIT_FAIL_MAX == 5
        assert DEFAULT_CIRCUIT_FAIL_MAX > 0
        assert isinstance(DEFAULT_CIRCUIT_FAIL_MAX, int)


# ==========================================
# Integration Tests (Cross-type validation)
# ==========================================

@pytest.mark.unit
@pytest.mark.fast
class TestTypeIntegration:
    """Test that types work together correctly"""

    def test_error_response_in_crawl_response(self):
        """Test that error responses work in crawl response"""
        error = create_error_response(
            error="Connection failed",
            error_type="http_error",
            status_code=500
        )

        resp = CrawlWebResponse(
            status=MCPResponseStatusEnum.ERROR,
            pages_crawled=0,
            error=error["error"],
            error_type=error["error_type"]
        )
        assert resp.status == MCPResponseStatusEnum.ERROR
        assert resp.error == "Connection failed"

    def test_job_status_lifecycle(self):
        """Test complete job status lifecycle"""
        # Pending
        pending = create_job_status_response(
            job_id="lifecycle-job",
            job_status=JobStatusEnum.PENDING,
            progress=0,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:00:00Z"
        )
        assert pending["job_status"] == JobStatusEnum.PENDING

        # Processing
        processing = create_job_status_response(
            job_id="lifecycle-job",
            job_status=JobStatusEnum.PROCESSING,
            progress=50,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:05:00Z"
        )
        assert processing["progress"] == 50

        # Completed
        completed = create_job_status_response(
            job_id="lifecycle-job",
            job_status=JobStatusEnum.COMPLETED,
            progress=100,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:10:00Z",
            result={"success": True}
        )
        assert completed["result"]["success"] is True
