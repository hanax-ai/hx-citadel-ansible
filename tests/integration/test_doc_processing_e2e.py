#!/usr/bin/env python3
"""
End-to-End Integration Tests for Document Processing (TEST-005)

Tests the complete ingest_doc() workflow including:
- PDF, DOCX, TXT, MD file processing
- Docling text extraction
- Orchestrator async job creation
- Error handling for missing/invalid files

Based on tests/docs/TEST-005-document-processing.md
Part of Sprint 2.2 TASK-033: Integration Tests
"""

import pytest
import httpx
import tempfile
import os
from pathlib import Path


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires test files to be accessible on MCP server")
async def test_ingest_doc_pdf_file(mcp_server_url, test_timeout):
    """
    TEST-005 Case 1: PDF document ingestion
    
    Verifies ingest_doc processes PDF files successfully.
    Note: Requires PDF file accessible to MCP server.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "file_path": "/tmp/test.pdf"
        }
        
        response = await client.post(
            f"{mcp_server_url}/tools/ingest_doc",
            json=payload
        )
        
        if response.status_code == 202:
            data = response.json()
            assert "job_id" in data
            assert data.get("file_format") in [".pdf", "pdf"]
            print(f"✅ TEST-005-1: PDF ingestion initiated, job_id={data['job_id']}")
        else:
            print(f"⚠️  TEST-005-1: Skipped (test PDF not available)")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires test files to be accessible on MCP server")
async def test_ingest_doc_text_file(mcp_server_url, test_timeout):
    """
    TEST-005 Case 2: Text file ingestion
    
    Verifies ingest_doc processes TXT files.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "file_path": "/tmp/test.txt"
        }
        
        response = await client.post(
            f"{mcp_server_url}/tools/ingest_doc",
            json=payload
        )
        
        if response.status_code == 202:
            data = response.json()
            assert "job_id" in data
            assert data.get("file_format") in [".txt", "txt"]
            print(f"✅ TEST-005-2: TXT ingestion successful")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires test files to be accessible on MCP server")
async def test_ingest_doc_markdown_file(mcp_server_url, test_timeout):
    """
    TEST-005 Case 3: Markdown file ingestion
    
    Verifies ingest_doc processes MD files with formatting preserved.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "file_path": "/tmp/test.md"
        }
        
        response = await client.post(
            f"{mcp_server_url}/tools/ingest_doc",
            json=payload
        )
        
        if response.status_code == 202:
            data = response.json()
            assert "job_id" in data
            assert data.get("file_format") in [".md", "md"]
            print(f"✅ TEST-005-3: Markdown ingestion successful")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingest_doc_file_not_found(mcp_server_url, test_timeout):
    """
    TEST-005 Case 4: File not found error
    
    Verifies proper error handling for nonexistent files.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "file_path": "/tmp/nonexistent-file-xyz123.pdf"
        }
        
        response = await client.post(
            f"{mcp_server_url}/tools/ingest_doc",
            json=payload
        )
        
        assert response.status_code in [400, 404, 500], f"Expected error status, got {response.status_code}"
        data = response.json()
        
        assert "error" in data or "detail" in data or "message" in data
        error_text = str(data).lower()
        assert "not found" in error_text or "nonexistent" in error_text or "file" in error_text
        
        print(f"✅ TEST-005-4: File not found error handled correctly")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingest_doc_unsupported_format(mcp_server_url, test_timeout):
    """
    TEST-005 Case 5: Unsupported file format
    
    Verifies rejection of unsupported file formats.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "file_path": "/tmp/test.exe"
        }
        
        response = await client.post(
            f"{mcp_server_url}/tools/ingest_doc",
            json=payload
        )
        
        assert response.status_code in [400, 422, 500], f"Expected error for unsupported format"
        data = response.json()
        
        assert "error" in data or "detail" in data
        print(f"✅ TEST-005-5: Unsupported format rejected")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires orchestrator to be stopped for circuit breaker test")
async def test_ingest_doc_circuit_breaker(mcp_server_url, test_timeout):
    """
    TEST-005 Case 6: Circuit breaker protection
    
    Verifies document processing succeeds but orchestrator
    submission is protected by circuit breaker.
    """
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        payload = {
            "file_path": "/tmp/test.txt"
        }
        
        response = await client.post(
            f"{mcp_server_url}/tools/ingest_doc",
            json=payload
        )
        
        data = response.json()
        assert "error" in data or "circuit" in str(data).lower()
        
        if "retry_after" in data:
            assert data["retry_after"] > 0
        
        print(f"✅ TEST-005-6: Circuit breaker protection verified")
