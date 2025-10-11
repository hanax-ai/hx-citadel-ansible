"""
Constants Tests

Tests for module constants and default values.
Single Responsibility: Validate constant definitions.

Constants Tested:
- SUPPORTED_DOCUMENT_FORMATS
- DEFAULT_QDRANT_COLLECTION
- DEFAULT_EMBEDDING_MODEL
- DEFAULT_MAX_PAGES
- DEFAULT_CIRCUIT_FAIL_MAX
- Other defaults
"""

import pytest
from common_types import (
    SUPPORTED_DOCUMENT_FORMATS,
    DEFAULT_QDRANT_COLLECTION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MAX_PAGES,
    DEFAULT_CIRCUIT_FAIL_MAX,
)


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
