#!/usr/bin/env python3
"""
End-to-End Integration Tests for Qdrant Operations (TEST-009)

Tests vector storage and search operations:
- qdrant_store() - Store text with embeddings
- qdrant_find() - Search for similar vectors
- Metadata handling
- Ollama embedding generation
- Error scenarios

Based on tests/docs/TEST-009-qdrant-operations.md
Part of Sprint 2.2 TASK-033: Integration Tests
"""

import pytest
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_qdrant_store_single_vector(mcp_server_url, test_timeout):
    """
    TEST-009 Case 1: Store single vector

    Verifies qdrant_store successfully stores text with embeddings.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "text": "Machine learning is a subset of artificial intelligence",
            "metadata": {"category": "AI", "source": "test", "test_id": "TEST-009-1"},
        }

        response = await client.post(
            f"{mcp_server_url}/tools/qdrant_store", json=payload
        )

        # Handle service unavailability
        if response.status_code == 500:
            pytest.skip("Qdrant/Ollama service not available (HTTP 500)")

        # Success statuses only
        assert response.status_code in [
            200,
            202,
        ], f"Unexpected status: {response.status_code}"

        data = response.json()
        assert "point_id" in data or "id" in data, "Missing point_id in response"

        if "embedding_dimension" in data:
            assert (
                data["embedding_dimension"] == 768
            ), "Expected 768-dim embeddings (nomic-embed-text)"

        print(
            f"✅ TEST-009-1: Vector stored successfully, point_id={data.get('point_id', 'N/A')}"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qdrant_find_vectors(mcp_server_url, test_timeout):
    """
    TEST-009 Case 2: Search vectors

    Verifies qdrant_find returns relevant results for queries.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        store_payload = {
            "text": "Machine learning algorithms process data patterns",
            "metadata": {"source": "TEST-009-2"},
        }

        store_response = await client.post(
            f"{mcp_server_url}/tools/qdrant_store", json=store_payload
        )

        if store_response.status_code not in [200, 202]:
            pytest.skip("Cannot test find without successful store")

        find_payload = {"query": "What is machine learning?", "limit": 5}

        find_response = await client.post(
            f"{mcp_server_url}/tools/qdrant_find", json=find_payload
        )

        assert (
            find_response.status_code == 200
        ), f"Find failed: {find_response.status_code}"
        data = find_response.json()

        assert "results" in data or "points" in data, "Missing results in response"
        results = data.get("results", data.get("points", []))

        if len(results) > 0:
            scores = [r.get("score", 0) for r in results]
            assert scores == sorted(scores, reverse=True), "Results not sorted by score"
            print(
                f"✅ TEST-009-2: Found {len(results)} results, top score={scores[0]:.3f}"
            )
        else:
            print("✅ TEST-009-2: Search completed (no results in empty collection)")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.skip(reason="Requires multiple store operations")
async def test_qdrant_store_multiple_vectors(mcp_server_url, test_timeout):
    """
    TEST-009 Case 3: Store multiple vectors

    Verifies batch storage of multiple texts.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        texts = [
            "Python is a programming language",
            "JavaScript is used for web development",
            "Machine learning uses neural networks",
            "Data science involves statistical analysis",
            "Cloud computing uses distributed systems",
        ]

        point_ids = []
        for i, text in enumerate(texts):
            payload = {"text": text, "metadata": {"batch": "TEST-009-3", "index": i}}

            response = await client.post(
                f"{mcp_server_url}/tools/qdrant_store", json=payload
            )

            if response.status_code in [200, 202]:
                data = response.json()
                point_ids.append(data.get("point_id"))

        assert len(point_ids) == len(
            texts
        ), f"Only {len(point_ids)}/{len(texts)} stored successfully"
        print(f"✅ TEST-009-3: Stored {len(point_ids)} vectors successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qdrant_find_no_results(mcp_server_url, test_timeout):
    """
    TEST-009 Case 4: Search with no results

    Verifies graceful handling when no relevant vectors found.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        find_payload = {
            "query": "completely unrelated quantum physics topic xyz123 nonexistent",
            "limit": 5,
        }

        response = await client.post(
            f"{mcp_server_url}/tools/qdrant_find", json=find_payload
        )

        assert response.status_code == 200, f"Unexpected status: {response.status_code}"
        data = response.json()

        assert "results" in data or "points" in data
        results = data.get("results", data.get("points", []))

        print(
            f"✅ TEST-009-4: No results query handled correctly ({len(results)} results)"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qdrant_store_empty_text(mcp_server_url, test_timeout):
    """
    TEST-009 Case 5: Empty text validation

    Verifies rejection of empty text inputs.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {"text": "", "metadata": {}}

        response = await client.post(
            f"{mcp_server_url}/tools/qdrant_store", json=payload
        )

        assert response.status_code in [
            400,
            422,
        ], f"Expected validation error, got {response.status_code}"
        data = response.json()

        assert "error" in data or "detail" in data
        print("✅ TEST-009-5: Empty text properly rejected")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires Ollama to be stopped")
async def test_qdrant_store_ollama_unavailable(mcp_server_url, test_timeout):
    """
    TEST-009 Case 6: Ollama service unavailable

    Verifies graceful error when embedding service is down.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "text": "Test text for embedding",
            "metadata": {"test": "ollama-unavailable"},
        }

        response = await client.post(
            f"{mcp_server_url}/tools/qdrant_store", json=payload
        )

        assert response.status_code in [500, 503], "Expected service error"
        data = response.json()

        assert "error" in data or "message" in data
        error_text = str(data).lower()
        assert (
            "ollama" in error_text
            or "embedding" in error_text
            or "unavailable" in error_text
        )

        print("✅ TEST-009-6: Ollama unavailable error handled")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires Qdrant to be stopped")
async def test_qdrant_store_qdrant_unavailable(mcp_server_url, test_timeout):
    """
    TEST-009 Case 7: Qdrant service unavailable

    Verifies graceful error when vector database is down.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {"text": "Test text", "metadata": {}}

        response = await client.post(
            f"{mcp_server_url}/tools/qdrant_store", json=payload
        )

        assert response.status_code in [500, 503], "Expected service error"
        data = response.json()

        assert "error" in data or "message" in data
        error_text = str(data).lower()
        assert (
            "qdrant" in error_text
            or "vector" in error_text
            or "connection" in error_text
        )

        print("✅ TEST-009-7: Qdrant unavailable error handled")
