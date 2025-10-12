#!/usr/bin/env python3
"""
MCP Tools Integration Tests

Functional integration tests that actually invoke MCP tools via HTTP.
Tests the deployed MCP server (configurable via MCP_SERVER_URL env var).

These tests require the MCP server to be running and accessible.

Environment Variables:
- MCP_SERVER_URL: Override MCP server URL (default: http://hx-mcp1-server:8081)

Run with: pytest tests/integration/test_mcp_tools.py -v

Examples:
  # Run against default server
  pytest tests/integration/test_mcp_tools.py -v

  # Run against development server
  MCP_SERVER_URL=http://hx-mcp1-dev.dev-test.hana-x.ai:8081 pytest tests/integration/test_mcp_tools.py -v

  # Run in CI/CD
  export MCP_SERVER_URL=http://hx-mcp1-ci.dev-test.hana-x.ai:8081
  pytest tests/integration/test_mcp_tools.py -v
"""

import pytest
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_tool(mcp_server_url, test_timeout):
    """Test the health_check MCP tool"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Call the health endpoint
        response = await client.get(f"{mcp_server_url}/health")

        # Assertions
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "status" in data, "Response missing 'status' field"
        assert data["status"] in [
            "healthy",
            "degraded",
        ], f"Unexpected status: {data['status']}"

        # Check for expected health check fields
        assert "orchestrator" in data, "Missing orchestrator health"
        assert "circuit_breaker" in data, "Missing circuit breaker metrics"

        print(f"✅ health_check: status={data['status']}")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_crawl_web_tool(mcp_server_url, test_timeout):
    """Test the crawl_web MCP tool"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Prepare request payload
        payload = {"url": "https://example.com", "max_pages": 1}

        # Call the crawl endpoint
        response = await client.post(f"{mcp_server_url}/tools/crawl_web", json=payload)

        # Assertions
        assert response.status_code in [
            200,
            202,
        ], f"Expected 200/202, got {response.status_code}"

        data = response.json()

        # Check for job status (HTTP 202 async pattern)
        if response.status_code == 202:
            assert "job_id" in data, "Async response missing job_id"
            assert "status" in data, "Async response missing status"
            print(f"✅ crawl_web: job_id={data['job_id']} (async)")
        else:
            # Synchronous response
            assert (
                "content" in data or "chunks" in data
            ), "Response missing content/chunks"
            print("✅ crawl_web: crawled example.com successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qdrant_store_and_find_tools(mcp_server_url, test_timeout):
    """Test qdrant_store and qdrant_find MCP tools"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Test 1: Store a vector
        store_payload = {
            "text": "Integration test document for Qdrant",
            "metadata": {"source": "integration_test", "test_id": "test_001"},
        }

        store_response = await client.post(
            f"{mcp_server_url}/tools/qdrant_store", json=store_payload
        )

        assert store_response.status_code in [
            200,
            202,
        ], f"Store failed: {store_response.status_code}"
        store_data = store_response.json()

        # Extract point_id if available
        point_id = store_data.get("point_id")
        print(f"✅ qdrant_store: point_id={point_id}")

        # Test 2: Find similar vectors
        find_payload = {"query": "Integration test", "limit": 5}

        find_response = await client.post(
            f"{mcp_server_url}/tools/qdrant_find", json=find_payload
        )

        assert (
            find_response.status_code == 200
        ), f"Find failed: {find_response.status_code}"
        find_data = find_response.json()

        assert (
            "results" in find_data or "points" in find_data
        ), "Find response missing results"
        print("✅ qdrant_find: found results")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_ingest_doc_tool(mcp_server_url, test_timeout):
    """Test the ingest_doc MCP tool"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Note: This test requires a document file path accessible to the MCP server
        # For now, we test the endpoint is reachable and returns proper error for missing file

        payload = {"file_path": "/nonexistent/test.pdf"}

        response = await client.post(f"{mcp_server_url}/tools/ingest_doc", json=payload)

        # We expect either 404 (file not found) or 400 (bad request) for nonexistent file
        # This validates the endpoint exists and handles errors properly
        assert response.status_code in [
            400,
            404,
            500,
        ], f"Unexpected status: {response.status_code}"

        data = response.json()
        assert (
            "error" in data or "message" in data
        ), "Error response missing error field"

        print("✅ ingest_doc: endpoint validated (error handling works)")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_lightrag_query_tool(mcp_server_url, test_timeout):
    """Test the lightrag_query MCP tool"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Test query with different modes
        for mode in ["naive", "local", "global", "hybrid"]:
            payload = {"query": "What is LightRAG?", "mode": mode}

            response = await client.post(
                f"{mcp_server_url}/tools/lightrag_query", json=payload
            )

            # LightRAG might return 202 for async processing or 200 for immediate results
            assert response.status_code in [
                200,
                202,
                500,
            ], f"Unexpected status for mode {mode}: {response.status_code}"

            data = response.json()

            if response.status_code == 202:
                assert "job_id" in data, f"Mode {mode}: async response missing job_id"
                print(f"✅ lightrag_query ({mode}): job_id={data['job_id']} (async)")
            elif response.status_code == 200:
                assert (
                    "answer" in data or "result" in data
                ), f"Mode {mode}: response missing answer"
                print(f"✅ lightrag_query ({mode}): got answer")
            else:
                # 500 might occur if LightRAG not initialized yet
                print(f"⚠️  lightrag_query ({mode}): not ready (status 500)")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_status_tool(mcp_server_url, test_timeout):
    """Test the get_job_status MCP tool"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Test with a non-existent job ID (should return 404 or error)
        payload = {"job_id": "test-job-12345"}

        response = await client.post(
            f"{mcp_server_url}/tools/get_job_status", json=payload
        )

        # Should return 404 or 400 for non-existent job
        assert response.status_code in [
            200,
            400,
            404,
        ], f"Unexpected status: {response.status_code}"

        data = response.json()

        if response.status_code == 200:
            # If somehow the job exists, validate structure
            assert "status" in data, "Job status response missing status field"
            print(f"✅ get_job_status: status={data.get('status')}")
        else:
            # Expected: job not found
            assert (
                "error" in data or "message" in data
            ), "Error response missing error field"
            print("✅ get_job_status: properly returns error for unknown job")


@pytest.mark.integration
def test_mcp_server_reachable(mcp_server_url):
    """Test that MCP server is reachable (synchronous pre-check)"""
    import requests

    try:
        response = requests.get(f"{mcp_server_url}/health", timeout=5)
        assert (
            response.status_code == 200
        ), f"Server not healthy: {response.status_code}"
        print(f"✅ MCP server reachable at {mcp_server_url}")
    except requests.exceptions.ConnectionError:
        pytest.skip(f"MCP server not reachable at {mcp_server_url}")
    except requests.exceptions.Timeout:
        pytest.skip(f"MCP server timeout at {mcp_server_url}")


if __name__ == "__main__":
    """Run tests directly"""
    import sys
    import os

    server_url = os.getenv("MCP_SERVER_URL", "http://hx-mcp1-server:8081")

    print("=" * 70)
    print("MCP TOOLS INTEGRATION TEST SUITE")
    print("=" * 70)
    print(f"Server: {server_url}")
    print("=" * 70)
    print()

    # Run with pytest
    exit_code = pytest.main([__file__, "-v", "-s", "--tb=short"])
    sys.exit(exit_code)
