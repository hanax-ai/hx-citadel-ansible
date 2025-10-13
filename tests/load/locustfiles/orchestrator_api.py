#!/usr/bin/env python3
"""
Load tests for Orchestrator API endpoints

Tests:
- Health check
- Job status lookup
- Job listing

Part of Sprint 2.2 TASK-034: Load Testing
"""

from locust import HttpUser, task, between
import os


class OrchestratorUser(HttpUser):
    """Simulate interactions with Orchestrator API"""

    host = os.getenv("ORCHESTRATOR_URL", "http://hx-orchestrator-server:8000")
    wait_time = between(1, 3)

    @task(5)
    def health_check(self):
        """Health check endpoint"""
        with self.client.get("/healthz", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(3)
    def get_job_status(self):
        """Get job status"""
        job_id = "test-job-12345"
        with self.client.get(f"/jobs/{job_id}", catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Job status failed: {response.status_code}")

    @task(1)
    def list_jobs(self):
        """List recent jobs"""
        with self.client.get("/jobs?limit=10", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List jobs failed: {response.status_code}")
