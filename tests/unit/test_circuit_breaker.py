"""
Unit tests for Circuit Breaker functionality

Tests the circuit breaker protection for orchestrator API calls,
including state transitions, fast-fail behavior, and recovery.

Phase 2 Sprint 2.2: Automated Testing (TASK-032)
"""

import pytest
import httpx
import pybreaker


@pytest.mark.unit
@pytest.mark.circuit_breaker
@pytest.mark.fast
class TestCircuitBreakerStates:
    """Test circuit breaker state machine"""

    def test_circuit_breaker_initial_state_closed(self):
        """Test circuit breaker starts in closed state (normal operation)"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=60, name="test_breaker"
        )

        assert breaker.current_state == "closed"
        assert breaker.fail_counter == 0

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after fail_max consecutive failures"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=3, reset_timeout=60, name="test_breaker"
        )

        def failing_function():
            raise Exception("Test failure")

        for _ in range(3):
            try:
                breaker.call(failing_function)
            except Exception:
                pass

        assert breaker.current_state == "open"
        assert breaker.fail_counter == 3

    def test_circuit_breaker_fast_fail_when_open(self):
        """Test circuit breaker fails fast when open without calling function"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=1, reset_timeout=60, name="test_breaker"
        )

        call_count = 0

        def failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Test failure")

        # Trip the breaker
        try:
            breaker.call(failing_function)
        except Exception:
            pass

        assert breaker.current_state == "open"
        assert call_count == 1

        # When breaker is open, subsequent calls should NOT execute the function
        call_count = 0
        with pytest.raises(pybreaker.CircuitBreakerError):
            breaker.call(failing_function)

        # Assert function was NOT called (fast fail behavior)
        assert call_count == 0, "Function should not be called when breaker is open"
        assert breaker.current_state == "open"

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker allows trial call after reset timeout"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=1, reset_timeout=1, name="test_breaker"
        )

        call_count = 0

        def failing_function():
            nonlocal call_count
            call_count += 1
            import time

            time.sleep(0.01)
            raise Exception("Test failure")

        # Trip the breaker
        try:
            breaker.call(failing_function)
        except Exception:
            pass

        assert breaker.current_state == "open"
        assert call_count == 1

        # While in OPEN state, function should NOT be called (fast fail)
        call_count = 0
        with pytest.raises(pybreaker.CircuitBreakerError):
            breaker.call(failing_function)
        assert call_count == 0, "Fast fail should not call function"

        # Wait for reset timeout to transition to HALF_OPEN
        import time

        time.sleep(1.1)

        # In HALF_OPEN state, function SHOULD be called (trial attempt)
        call_count = 0
        with pytest.raises(pybreaker.CircuitBreakerError):
            breaker.call(failing_function)
        assert call_count == 1, "Half-open state should allow trial call"
        # After failed trial, should transition back to OPEN
        assert breaker.current_state == "open"

    def test_circuit_breaker_closes_on_success_in_half_open(self):
        """Test circuit breaker closes after successful retry"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=1, reset_timeout=1, success_threshold=1, name="test_breaker"
        )

        def failing_function():
            raise Exception("Test failure")

        try:
            breaker.call(failing_function)
        except Exception:
            pass

        assert breaker.current_state == "open"

        import time

        time.sleep(1.1)

        def success_function():
            return "success"

        result = breaker.call(success_function)
        assert result == "success"
        assert breaker.current_state == "closed"


@pytest.mark.unit
@pytest.mark.circuit_breaker
@pytest.mark.fast
class TestCircuitBreakerMetrics:
    """Test circuit breaker metrics and monitoring"""

    def test_circuit_breaker_fail_counter(self):
        """Test fail_counter increments on failures"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=60, name="test_breaker"
        )

        def failing_function():
            raise Exception("Test failure")

        assert breaker.fail_counter == 0

        for i in range(3):
            try:
                breaker.call(failing_function)
            except Exception:
                pass
            assert breaker.fail_counter == i + 1

    def test_circuit_breaker_fail_counter_resets_on_success(self):
        """Test fail_counter resets to 0 on successful call"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=60, name="test_breaker"
        )

        def failing_function():
            raise Exception("Test failure")

        try:
            breaker.call(failing_function)
        except Exception:
            pass

        assert breaker.fail_counter == 1

        def success_function():
            return "success"

        breaker.call(success_function)
        assert breaker.fail_counter == 0

    def test_circuit_breaker_configuration(self):
        """Test circuit breaker configuration parameters"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=60, success_threshold=2, name="test_breaker"
        )

        assert breaker._fail_max == 5
        assert breaker._reset_timeout == 60
        assert breaker._success_threshold == 2
        assert breaker.name == "test_breaker"


@pytest.mark.unit
@pytest.mark.circuit_breaker
@pytest.mark.asyncio
class TestCircuitBreakerWithHTTP:
    """Test circuit breaker with HTTP calls"""

    async def test_circuit_breaker_with_successful_http_call(
        self, mock_http, orchestrator_url
    ):
        """Test circuit breaker allows successful HTTP calls"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=60, name="test_breaker"
        )

        mock_http.post(f"{orchestrator_url}/test").respond(json={"status": "success"})

        def make_request():
            with httpx.Client() as client:
                response = client.post(f"{orchestrator_url}/test")
                response.raise_for_status()
                return response.json()

        result = breaker.call(make_request)
        assert result["status"] == "success"
        assert breaker.current_state == "closed"

    async def test_circuit_breaker_with_http_failures(
        self, mock_http, orchestrator_url
    ):
        """Test circuit breaker opens after HTTP failures"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=3, reset_timeout=60, name="test_breaker"
        )

        mock_http.post(f"{orchestrator_url}/test").respond(status_code=503)

        def make_request():
            with httpx.Client() as client:
                response = client.post(f"{orchestrator_url}/test")
                response.raise_for_status()
                return response.json()

        for _ in range(3):
            try:
                breaker.call(make_request)
            except Exception:
                pass

        assert breaker.current_state == "open"

        with pytest.raises(pybreaker.CircuitBreakerError):
            breaker.call(make_request)

    async def test_circuit_breaker_protects_against_timeouts(
        self, mock_http, orchestrator_url
    ):
        """Test circuit breaker protects against timeout errors"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=2, reset_timeout=60, name="test_breaker"
        )

        mock_http.post(f"{orchestrator_url}/test").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        def make_request():
            with httpx.Client(timeout=1.0) as client:
                response = client.post(f"{orchestrator_url}/test")
                return response.json()

        for _ in range(2):
            try:
                breaker.call(make_request)
            except Exception:
                pass

        assert breaker.current_state == "open"


@pytest.mark.unit
@pytest.mark.circuit_breaker
@pytest.mark.fast
class TestCircuitBreakerErrorHandling:
    """Test circuit breaker error handling"""

    def test_circuit_breaker_error_contains_state_info(self):
        """Test CircuitBreakerError is raised when circuit is open"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=1, reset_timeout=60, name="orchestrator_api"
        )

        def failing_function():
            raise Exception("Test failure")

        try:
            breaker.call(failing_function)
        except Exception:
            pass

        with pytest.raises(pybreaker.CircuitBreakerError) as exc_info:
            breaker.call(lambda: "test")

        assert exc_info.value is not None
        assert breaker.current_state == "open"

    def test_circuit_breaker_allows_call_in_closed_state(self):
        """Test circuit breaker allows calls in closed state"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=60, name="test_breaker"
        )

        def success_function():
            return "success"

        result = breaker.call(success_function)
        assert result == "success"
        assert breaker.current_state == "closed"

    def test_circuit_breaker_blocks_call_in_open_state(self):
        """Test circuit breaker blocks calls in open state"""
        breaker = pybreaker.CircuitBreaker(
            fail_max=1, reset_timeout=60, name="test_breaker"
        )

        def failing_function():
            raise Exception("Test failure")

        try:
            breaker.call(failing_function)
        except Exception:
            pass

        assert breaker.current_state == "open"

        with pytest.raises(pybreaker.CircuitBreakerError):
            breaker.call(lambda: "test")
