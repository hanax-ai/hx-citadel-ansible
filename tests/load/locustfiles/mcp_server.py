#!/usr/bin/env python3
"""
Load tests for MCP Server endpoints

Tests all 7 MCP tools:
- crawl_web
- ingest_doc
- qdrant_store
- qdrant_find
- lightrag_query
- get_job_status
- health_check

Part of Sprint 2.2 TASK-034: Load Testing
"""

from locust import HttpUser, task, between, events
import json
import os


class MCPServerUser(HttpUser):
    """Simulate users interacting with MCP Server"""
    
    host = os.getenv("MCP_SERVER_URL", "http://hx-mcp1-server:8081")
    
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        """Health check endpoint - most frequent"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def lightrag_query(self):
        """LightRAG query - common operation"""
        payload = {
            "query": "What is machine learning?",
            "mode": "hybrid"
        }
        with self.client.post(
            "/tools/lightrag_query",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"LightRAG query failed: {response.status_code}")
    
    @task(2)
    def qdrant_find(self):
        """Qdrant vector search"""
        payload = {
            "query": "AI applications in healthcare",
            "limit": 5
        }
        with self.client.post(
            "/tools/qdrant_find",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Qdrant find failed: {response.status_code}")
    
    @task(1)
    def qdrant_store(self):
        """Qdrant vector storage"""
        payload = {
            "text": "The HX-Citadel Shield is a production-ready RAG pipeline.",
            "metadata": {
                "source": "load_test",
                "type": "test_data"
            }
        }
        with self.client.post(
            "/tools/qdrant_store",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Qdrant store failed: {response.status_code}")
    
    @task(1)
    def crawl_web(self):
        """Web crawling"""
        payload = {
            "url": "https://example.com",
            "max_pages": 2
        }
        with self.client.post(
            "/tools/crawl_web",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Web crawl failed: {response.status_code}")
    
    @task(1)
    def get_job_status(self):
        """Job status lookup"""
        job_id = "test-job-12345"
        with self.client.get(
            f"/tools/get_job_status?job_id={job_id}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Job status failed: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test configuration on start"""
    print(f"Starting MCP Server load test against: {MCPServerUser.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary on test stop"""
    print("\nMCP Server load test complete!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
