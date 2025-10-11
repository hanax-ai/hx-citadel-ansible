"""
Test helper utilities

Phase 2 Sprint 2.2: Automated Testing (TASK-031)
"""

import asyncio
import json
import time
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import httpx


async def wait_for_service(
    url: str,
    timeout: int = 30,
    interval: float = 1.0
) -> bool:
    """
    Wait for a service to become available (healthy and responding with 2xx)

    Args:
        url: Service URL to check (typically a health endpoint)
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds

    Returns:
        True if service is healthy (2xx response), False otherwise

    Notes:
        Only accepts 2xx status codes as "healthy". Client errors (4xx) and
        server errors (5xx) indicate the service is not operational.
    """
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        while time.time() - start_time < timeout:
            try:
                response = await client.get(url, timeout=5.0)
                # Only accept 2xx status codes as healthy
                if 200 <= response.status_code < 300:
                    return True
            except (httpx.RequestError, httpx.TimeoutException):
                pass
            await asyncio.sleep(interval)
    return False


async def poll_until(
    condition: Callable[[], bool],
    timeout: int = 30,
    interval: float = 1.0
) -> bool:
    """
    Poll until a condition is met or timeout

    Args:
        condition: Callable that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds

    Returns:
        True if condition met, False on timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition():
            return True
        await asyncio.sleep(interval)
    return False


def load_test_data(filename: str) -> Dict[str, Any]:
    """
    Load test data from a file

    Args:
        filename: Name of the test data file

    Returns:
        Test data as dictionary

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file extension is not supported
        json.JSONDecodeError: If JSON parsing fails
    """
    test_data_dir = Path(__file__).parent.parent / "fixtures"
    file_path = test_data_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")

    # Detect file extension and load accordingly
    extension = file_path.suffix.lower()
    
    if extension == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise ValueError(
            f"Unsupported fixture format: {extension}. "
            f"Supported formats: .json"
        )


def assert_response_structure(
    response: Dict[str, Any],
    required_keys: list[str],
    optional_keys: Optional[list[str]] = None
) -> None:
    """
    Assert that a response has the required structure

    Args:
        response: Response dictionary to validate
        required_keys: Keys that must be present
        optional_keys: Keys that may be present
    """
    missing_keys = set(required_keys) - set(response.keys())
    if missing_keys:
        raise AssertionError(f"Missing required keys: {missing_keys}")

    if optional_keys:
        all_allowed = set(required_keys) | set(optional_keys)
        extra_keys = set(response.keys()) - all_allowed
        if extra_keys:
            print(f"Warning: Unexpected keys in response: {extra_keys}")


async def make_async_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs
) -> httpx.Response:
    """
    Make an async HTTP request with error handling

    Args:
        client: HTTP client
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        **kwargs: Additional request parameters

    Returns:
        HTTP response
    """
    try:
        response = await client.request(method, url, **kwargs)
        return response
    except httpx.RequestError as e:
        raise RuntimeError(f"Request failed: {e}") from e


def get_test_url(service: str, path: str = "") -> str:
    """
    Get a test URL for a specific service

    Args:
        service: Service name (mcp, orchestrator, qdrant, etc.)
        path: URL path

    Returns:
        Complete URL
    """
    base_urls = {
        "mcp": "http://hx-mcp1-server:8081",
        "orchestrator": "http://hx-orchestrator-server:8000",
        "qdrant": "http://hx-vectordb-server:6333",
        "ollama": "http://hx-ollama1:11434",
    }

    base_url = base_urls.get(service)
    if not base_url:
        raise ValueError(f"Unknown service: {service}")

    # Normalize base_url: strip trailing slashes
    normalized_base = base_url.rstrip("/")
    
    # Normalize path: strip whitespace and ensure single leading slash
    normalized_path = path.strip()
    if normalized_path:
        # Ensure path starts with exactly one slash
        normalized_path = "/" + normalized_path.lstrip("/")
    
    return f"{normalized_base}{normalized_path}"


class TestTimer:
    """Context manager for timing test execution"""

    def __init__(self, name: str = "Test"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"{self.name} completed in {duration:.3f}s")

    @property
    def duration(self) -> float:
        """Get the duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
