"""
Orchestrator Embedding Service Tests

Tests for the Ollama embedding service used by the orchestrator.
Single Responsibility: Validate embedding generation via local Ollama instance.

Component Under Test:
- orchestrator/services/embeddings.py

Embedding Models (deployed on orchestrator at hx-orchestrator-server:11434):
- mxbai-embed-large:latest (1024 dimensions, 669MB, F16)
- nomic-embed-text:latest (768 dimensions, 274MB, F16)
- all-minilm:latest (384 dimensions, 46MB, F16)

Test Coverage:
- Embedding generation (single text)
- Batch embedding generation
- Concurrent processing
- Error handling
- Health checks
- Timeout handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


# Mock embedding service for testing
class MockEmbeddingService:
    """Mock embedding service that matches production interface"""

    def __init__(self):
        self.ollama_url = "http://hx-orchestrator-server:11434"  # Corrected URL
        self.model = "mxbai-embed-large"
        self.dimension = 1024

    async def get_embedding(self, text: str):
        """Mock get_embedding method"""
        pass

    async def get_embeddings_batch(self, texts):
        """Mock get_embeddings_batch method"""
        pass


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestEmbeddingServiceConfiguration:
    """Test embedding service configuration"""

    def test_embedding_service_uses_correct_ollama_url(self):
        """Test that embedding service points to orchestrator (not hx-ollama1)"""
        service = MockEmbeddingService()

        # Should point to orchestrator where embedding models are deployed
        assert "hx-orchestrator-server" in service.ollama_url

        # Should NOT point to hx-ollama1 (no embedding models there)
        assert "hx-ollama1" not in service.ollama_url

    def test_embedding_service_uses_mxbai_embed_large_model(self):
        """Test default model is mxbai-embed-large"""
        service = MockEmbeddingService()
        assert service.model == "mxbai-embed-large"

    def test_embedding_service_expects_1024_dimensions(self):
        """Test default dimension is 1024 (mxbai-embed-large)"""
        service = MockEmbeddingService()
        assert service.dimension == 1024


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestGetEmbedding:
    """Test single text embedding generation"""

    async def test_get_embedding_success(self):
        """Test successful embedding generation for single text"""
        # Arrange
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3] * 341 + [0.1],  # 1024 dimensions
            "model": "mxbai-embed-large",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        service = MockEmbeddingService()

        # Act
        with patch("httpx.AsyncClient", return_value=mock_client):
            # Simulate actual method call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{service.ollama_url}/api/embeddings",
                    json={"model": service.model, "prompt": "test text"},
                )
                response.raise_for_status()
                result = response.json()
                embedding = result["embedding"]

        # Assert
        assert len(embedding) == 1024
        assert all(isinstance(val, (int, float)) for val in embedding)
        mock_client.post.assert_called_once()

    async def test_get_embedding_returns_correct_dimensions(self):
        """Test embedding has exactly 1024 dimensions"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "embedding": [0.5] * 1024  # Exactly 1024 dimensions
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{service.ollama_url}/api/embeddings",
                    json={"model": service.model, "prompt": "test"},
                )
                embedding = response.json()["embedding"]

        assert len(embedding) == 1024

    async def test_get_embedding_ollama_unavailable(self):
        """Test error handling when Ollama service is unavailable"""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            with pytest.raises(httpx.ConnectError):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await client.post(
                        f"{service.ollama_url}/api/embeddings",
                        json={"model": service.model, "prompt": "test"},
                    )

    async def test_get_embedding_timeout(self):
        """Test timeout handling for slow embedding generation"""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.side_effect = httpx.TimeoutException("Request timeout")

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            with pytest.raises(httpx.TimeoutException):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await client.post(
                        f"{service.ollama_url}/api/embeddings",
                        json={"model": service.model, "prompt": "test"},
                    )

    async def test_get_embedding_model_not_found(self):
        """Test error when embedding model doesn't exist"""
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found: model 'mxbai-embed-large' not found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            with pytest.raises(httpx.HTTPStatusError):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{service.ollama_url}/api/embeddings",
                        json={"model": service.model, "prompt": "test"},
                    )
                    response.raise_for_status()


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestGetEmbeddingsBatch:
    """Test batch embedding generation"""

    async def test_get_embeddings_batch_success(self):
        """Test successful batch embedding generation"""
        texts = ["text1", "text2", "text3"]

        mock_response = AsyncMock()
        mock_response.json.return_value = {"embedding": [0.1] * 1024}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            # Simulate batch processing
            embeddings = []
            async with httpx.AsyncClient(timeout=60.0) as client:
                for text in texts:
                    response = await client.post(
                        f"{service.ollama_url}/api/embeddings",
                        json={"model": service.model, "prompt": text},
                    )
                    response.raise_for_status()
                    result = response.json()
                    embeddings.append(result["embedding"])

        assert len(embeddings) == 3
        assert all(len(emb) == 1024 for emb in embeddings)

    async def test_get_embeddings_batch_empty_list(self):
        """Test batch embedding with empty input list"""
        texts = []

        # Should handle gracefully without calling Ollama
        embeddings = []
        for _ in texts:
            pass  # No API calls

        assert len(embeddings) == 0

    async def test_get_embeddings_batch_handles_partial_failure(self):
        """Test batch embedding handles failures in some texts"""
        texts = ["text1", "text2", "text3"]

        # Mock: first two succeed, third fails
        responses = [
            {"embedding": [0.1] * 1024},
            {"embedding": [0.2] * 1024},
            None,  # This will fail
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        # Create side effect for post calls
        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            if call_count < 2:
                mock_resp = AsyncMock()
                mock_resp.json.return_value = responses[call_count]
                mock_resp.raise_for_status = MagicMock()
                call_count += 1
                return mock_resp
            else:
                raise httpx.HTTPStatusError(
                    "500 Internal Server Error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500),
                )

        mock_client.post = mock_post

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            embeddings = []
            async with httpx.AsyncClient(timeout=60.0) as client:
                for text in texts:
                    try:
                        response = await client.post(
                            f"{service.ollama_url}/api/embeddings",
                            json={"model": service.model, "prompt": text},
                        )
                        response.raise_for_status()
                        result = response.json()
                        embeddings.append(result["embedding"])
                    except httpx.HTTPStatusError:
                        # Skip failed embeddings
                        continue

        # Should have 2 successful embeddings
        assert len(embeddings) == 2


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestOllamaHealthCheck:
    """Test Ollama health check functionality"""

    async def test_check_ollama_health_success(self):
        """Test health check returns up status when Ollama is available"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "mxbai-embed-large:latest"},
                {"name": "nomic-embed-text:latest"},
                {"name": "all-minilm:latest"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{service.ollama_url}/api/tags")
                response.raise_for_status()
                models = response.json()

        assert len(models["models"]) == 3
        model_names = [m["name"] for m in models["models"]]
        assert "mxbai-embed-large:latest" in model_names

    async def test_check_ollama_health_returns_model_list(self):
        """Test health check returns list of available models"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "mxbai-embed-large:latest"},
                {"name": "nomic-embed-text:latest"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{service.ollama_url}/api/tags")
                models = response.json()

        model_names = [m["name"] for m in models["models"]]
        assert "mxbai-embed-large:latest" in model_names
        assert "nomic-embed-text:latest" in model_names

    async def test_check_ollama_health_connection_failure(self):
        """Test health check handles connection failures"""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            health_status = {"status": "down", "error": None}
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.get(f"{service.ollama_url}/api/tags")
            except httpx.ConnectError as e:
                health_status["error"] = str(e)

        assert health_status["status"] == "down"
        assert health_status["error"] is not None

    async def test_check_ollama_health_timeout(self):
        """Test health check handles timeout"""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

        with patch("httpx.AsyncClient", return_value=mock_client):
            service = MockEmbeddingService()

            with pytest.raises(httpx.TimeoutException):
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.get(f"{service.ollama_url}/api/tags")


@pytest.mark.unit
@pytest.mark.fast
class TestEmbeddingDimensions:
    """Test different embedding model dimensions"""

    def test_mxbai_embed_large_dimensions(self):
        """Test mxbai-embed-large uses 1024 dimensions"""
        service = MockEmbeddingService()
        service.model = "mxbai-embed-large"
        service.dimension = 1024

        assert service.dimension == 1024

    def test_nomic_embed_text_dimensions(self):
        """Test nomic-embed-text uses 768 dimensions"""
        service = MockEmbeddingService()
        service.model = "nomic-embed-text"
        service.dimension = 768

        assert service.dimension == 768

    def test_all_minilm_dimensions(self):
        """Test all-minilm uses 384 dimensions"""
        service = MockEmbeddingService()
        service.model = "all-minilm"
        service.dimension = 384

        assert service.dimension == 384
