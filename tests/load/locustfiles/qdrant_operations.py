#!/usr/bin/env python3
"""
Load tests for Qdrant vector database operations

Tests:
- Collection health
- Vector search
- Collection listing

Part of Sprint 2.2 TASK-034: Load Testing
"""

from locust import HttpUser, task, between
import os


class QdrantUser(HttpUser):
    """Simulate Qdrant vector database operations"""
    
    host = os.getenv("QDRANT_URL", "http://hx-vectordb-server:6333")
    wait_time = between(0.5, 2)
    
    @task(3)
    def health_check(self):
        """Qdrant health check"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def list_collections(self):
        """List collections"""
        with self.client.get("/collections", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List collections failed: {response.status_code}")
    
    @task(5)
    def search_vectors(self):
        """Search for similar vectors"""
        collection = "shield_knowledge_base"
        payload = {
            "vector": [0.1] * 768,
            "limit": 5
        }
        with self.client.post(
            f"/collections/{collection}/points/search",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Vector search failed: {response.status_code}")
