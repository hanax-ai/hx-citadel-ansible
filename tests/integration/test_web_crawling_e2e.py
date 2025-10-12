#!/usr/bin/env python3
"""
End-to-End Integration Tests for Web Crawling (TEST-004)

Tests the complete crawl_web() workflow including:
- MCP server crawl_web tool
- Orchestrator async job processing
- Circuit breaker protection
- Error handling scenarios

Based on tests/docs/TEST-004-web-crawling.md
Part of Sprint 2.2 TASK-033: Integration Tests
"""

import pytest
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_crawl_web_basic_happy_path(mcp_server_url, test_timeout):
    """
    TEST-004 Case 1: Basic web crawl (happy path)

    Verifies crawl_web successfully crawls a public website,
    returns job_id, and follows HTTP 202 async pattern.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "url": "https://example.com",
            "max_pages": 5,
            "allowed_domains": ["example.com"],
            "max_depth": 2,
        }

        response = await client.post(f"{mcp_server_url}/tools/crawl_web", json=payload)

        assert response.status_code in [
            200,
            202,
        ], f"Expected 200/202, got {response.status_code}"
        data = response.json()

        if response.status_code == 202:
            assert "job_id" in data, "Async response missing job_id"
            assert "status" in data, "Missing status field"
            assert (
                data["status"] == "accepted"
            ), f"Expected status='accepted', got {data['status']}"
            assert "pages_crawled" in data or "message" in data
            print(f"✅ TEST-004-1: Basic crawl initiated, job_id={data['job_id']}")
        else:
            assert "content" in data or "chunks" in data
            print("✅ TEST-004-1: Basic crawl completed synchronously")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crawl_web_single_page(mcp_server_url, test_timeout):
    """
    TEST-004 Case 2: Single page crawl

    Verifies crawl_web handles single-page crawl efficiently.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {"url": "https://httpbin.org/html", "max_pages": 1}

        response = await client.post(f"{mcp_server_url}/tools/crawl_web", json=payload)

        assert response.status_code in [
            200,
            202,
        ], f"Unexpected status: {response.status_code}"
        data = response.json()

        if "pages_crawled" in data:
            assert data["pages_crawled"] <= 1, "Should crawl at most 1 page"

        print("✅ TEST-004-2: Single page crawl successful")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crawl_web_invalid_url(mcp_server_url, test_timeout):
    """
    TEST-004 Case 3: Invalid URL handling

    Verifies crawl_web rejects invalid URLs with proper error.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {"url": "not-a-valid-url", "max_pages": 5}

        response = await client.post(f"{mcp_server_url}/tools/crawl_web", json=payload)

        assert response.status_code in [
            400,
            422,
        ], f"Expected 400/422 for invalid URL, got {response.status_code}"
        data = response.json()

        assert (
            "error" in data or "detail" in data
        ), "Error response missing error details"
        print("✅ TEST-004-3: Invalid URL properly rejected")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.skip(reason="Requires testing against unreachable domain")
async def test_crawl_web_unreachable_website(mcp_server_url, test_timeout):
    """
    TEST-004 Case 4: Unreachable website handling

    Verifies graceful error handling for network timeouts.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {"url": "https://nonexistent-website-12345.com", "max_pages": 5}

        response = await client.post(f"{mcp_server_url}/tools/crawl_web", json=payload)

        data = response.json()
        assert (
            "error" in data or "message" in data
        ), "Should return error for unreachable site"
        print("✅ TEST-004-4: Unreachable website handled gracefully")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires orchestrator to be stopped for circuit breaker test")
async def test_crawl_web_circuit_breaker_protection(mcp_server_url, test_timeout):
    """
    TEST-004 Case 5: Circuit breaker protection

    Verifies fast-fail when orchestrator is unavailable.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {"url": "https://example.com", "max_pages": 2}

        import time

        start = time.time()

        response = await client.post(f"{mcp_server_url}/tools/crawl_web", json=payload)

        elapsed = time.time() - start

        data = response.json()

        assert elapsed < 1.0, f"Circuit breaker should fast-fail, took {elapsed}s"
        assert "error" in data or "circuit" in str(data).lower()

        if "retry_after" in data:
            assert data["retry_after"] > 0

        print(
            f"✅ TEST-004-5: Circuit breaker protection verified (fast-fail in {elapsed:.3f}s)"
        )
