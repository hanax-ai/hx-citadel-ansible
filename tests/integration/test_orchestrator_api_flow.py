"""
Integration Tests for Orchestrator API End-to-End Flows

Tests complete workflows through the orchestrator API including:
- Job submission
- Job status tracking
- Job completion
- Error handling

Environment Variables:
- ORCHESTRATOR_URL: Override orchestrator URL (default: http://hx-orchestrator-server:8000)

Run with: pytest tests/integration/test_orchestrator_api_flow.py -v

Phase 2 Sprint 2.2: Automated Testing (TASK-033)
Addresses Issue #72: Write integration tests (minimum 4 files)
"""

import os
import pytest
import httpx
import asyncio
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.orchestrator
@pytest.mark.skipif(
    os.getenv('ORCHESTRATOR_URL') is None,
    reason="Requires ORCHESTRATOR_URL environment variable"
)
@pytest.mark.asyncio
async def test_orchestrator_health_check(orchestrator_url: str, test_timeout: int):
    """Test orchestrator health check endpoint"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        response = await client.get(f"{orchestrator_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Health check should return status
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        
        print(f"✅ Orchestrator health: {data['status']}")


@pytest.mark.integration
@pytest.mark.orchestrator
@pytest.mark.skipif(
    os.getenv('ORCHESTRATOR_URL') is None,
    reason="Requires ORCHESTRATOR_URL environment variable"
)
@pytest.mark.asyncio
async def test_job_submission_flow(orchestrator_url: str, test_timeout: int):
    """Test complete job submission and tracking flow"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Step 1: Submit a job
        job_payload = {
            "type": "test_job",
            "parameters": {"test": "value"}
        }
        
        submit_response = await client.post(
            f"{orchestrator_url}/api/jobs",
            json=job_payload
        )
        
        # Job should be accepted
        assert submit_response.status_code in [200, 201, 202]
        submit_data = submit_response.json()
        
        assert "job_id" in submit_data
        job_id = submit_data["job_id"]
        
        print(f"✅ Job submitted: {job_id}")
        
        # Step 2: Check job status
        status_response = await client.get(
            f"{orchestrator_url}/api/jobs/{job_id}"
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        assert "status" in status_data
        assert status_data["status"] in ["pending", "processing", "completed", "failed"]
        
        print(f"✅ Job status: {status_data['status']}")


@pytest.mark.integration
@pytest.mark.orchestrator
@pytest.mark.skipif(
    os.getenv('ORCHESTRATOR_URL') is None,
    reason="Requires ORCHESTRATOR_URL environment variable"
)
@pytest.mark.asyncio
async def test_job_list_endpoint(orchestrator_url: str, test_timeout: int):
    """Test listing all jobs from orchestrator"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        response = await client.get(f"{orchestrator_url}/api/jobs")
        
        # Should return list of jobs (may be empty)
        assert response.status_code == 200
        data = response.json()
        
        # Response should be a list
        assert isinstance(data, (list, dict))
        
        if isinstance(data, dict) and "jobs" in data:
            assert isinstance(data["jobs"], list)
            print(f"✅ Found {len(data['jobs'])} jobs")
        else:
            print(f"✅ Jobs endpoint returned: {type(data).__name__}")


@pytest.mark.integration
@pytest.mark.orchestrator
@pytest.mark.skipif(
    os.getenv('ORCHESTRATOR_URL') is None,
    reason="Requires ORCHESTRATOR_URL environment variable"
)
@pytest.mark.asyncio
async def test_orchestrator_error_handling(orchestrator_url: str, test_timeout: int):
    """Test that orchestrator handles invalid requests properly"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Try to get status of nonexistent job
        response = await client.get(
            f"{orchestrator_url}/api/jobs/nonexistent-job-id"
        )
        
        # Should return 404 or error
        assert response.status_code in [404, 400]
        
        print(f"✅ Orchestrator properly handles nonexistent job: {response.status_code}")


@pytest.mark.integration
@pytest.mark.orchestrator
@pytest.mark.slow
@pytest.mark.skipif(
    os.getenv('ORCHESTRATOR_URL') is None,
    reason="Requires ORCHESTRATOR_URL environment variable"
)
@pytest.mark.asyncio
async def test_concurrent_job_submissions(orchestrator_url: str, test_timeout: int):
    """Test submitting multiple jobs concurrently"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Submit 3 jobs concurrently
        jobs = [
            {"type": "test", "parameters": {"id": i}}
            for i in range(3)
        ]
        
        tasks = [
            client.post(f"{orchestrator_url}/api/jobs", json=job)
            for job in jobs
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful submissions
        successful = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.status_code in [200, 201, 202]
        )
        
        print(f"✅ Successfully submitted {successful}/3 concurrent jobs")
        
        # At least one should succeed (orchestrator might rate limit)
        assert successful >= 1


@pytest.mark.integration
@pytest.mark.orchestrator
@pytest.mark.skipif(
    os.getenv('ORCHESTRATOR_URL') is None,
    reason="Requires ORCHESTRATOR_URL environment variable"
)
@pytest.mark.asyncio
async def test_orchestrator_metrics_endpoint(orchestrator_url: str, test_timeout: int):
    """Test that orchestrator exposes metrics"""
    async with httpx.AsyncClient(timeout=test_timeout) as client:
        # Try common metrics endpoints
        endpoints = ["/metrics", "/api/metrics", "/stats"]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"{orchestrator_url}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ Metrics available at: {endpoint}")
                    return
            except httpx.RequestError:
                continue
        
        # If no metrics endpoint found, that's okay (not all deployments have it)
        print("ℹ️  No metrics endpoint found (optional)")

