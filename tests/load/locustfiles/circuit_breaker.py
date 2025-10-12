#!/usr/bin/env python3
"""
Circuit Breaker Load Test Scenarios

Implements 5 scenarios from tests/load/load_test_plan.md:
1. Normal Load (Circuit CLOSED)
2. Gradual Failures (Circuit Opens)
3. Recovery (Half-Open → Closed)
4. High Load with Failures
5. Flapping Protection

Part of Sprint 2.2 TASK-034: Load Testing
"""

from locust import HttpUser, task, between, events
import os
import time


class CircuitBreakerUser(HttpUser):
    """
    Test circuit breaker behavior under various failure scenarios

    Usage:
    - Normal load: locust -f circuit_breaker.py --users 100 --spawn-rate 10 --run-time 60s
    - Stress test: locust -f circuit_breaker.py --users 500 --spawn-rate 50 --run-time 300s
    """

    host = os.getenv("MCP_SERVER_URL", "http://hx-mcp1-server:8081")
    wait_time = between(1, 3)

    @task
    def test_tool_with_circuit_breaker(self):
        """
        Test MCP tool that uses circuit breaker for orchestrator calls

        This simulates Scenario 1 (Normal Load) or Scenario 4 (High Load)
        depending on user count and orchestrator availability.
        """
        payload = {"query": "Test circuit breaker behavior", "mode": "hybrid"}

        start_time = time.time()

        with self.client.post(
            "/tools/lightrag_query",
            json=payload,
            catch_response=True,
            name="lightrag_query_with_circuit_breaker",
        ) as response:
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                response.success()
            elif response.status_code == 202:
                response.success()
            elif "circuit" in response.text.lower():
                if response_time < 100:
                    response.success()
                    events.request.fire(
                        request_type="POST",
                        name="circuit_breaker_fast_fail",
                        response_time=response_time,
                        response_length=len(response.content),
                        exception=None,
                    )
                else:
                    response.failure(f"Circuit breaker slow ({response_time:.0f}ms)")
            else:
                response.failure(f"Request failed: {response.status_code}")

    @task(5)
    def check_circuit_breaker_state(self):
        """
        Monitor circuit breaker state via health endpoint

        High frequency to track state transitions
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "circuit_breakers" in data:
                        cb_state = data["circuit_breakers"].get("orchestrator", {})
                        state = cb_state.get("state", "unknown")

                        events.request.fire(
                            request_type="GET",
                            name=f"circuit_breaker_state_{state}",
                            response_time=0,
                            response_length=0,
                            exception=None,
                        )
                    response.success()
                except Exception as e:
                    response.failure(f"Health parse error: {e}")
            else:
                response.failure(f"Health check failed: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print circuit breaker test info"""
    print("\n" + "=" * 60)
    print("Circuit Breaker Load Test")
    print("=" * 60)
    print(f"Target: {CircuitBreakerUser.host}")
    print("\nExpected behavior:")
    print("- If orchestrator is UP: All requests succeed (circuit CLOSED)")
    print("- If orchestrator is DOWN:")
    print("  - First 5 requests timeout (~30s each)")
    print("  - Subsequent requests fail fast (<100ms)")
    print("  - Circuit state: OPEN")
    print("=" * 60 + "\n")
