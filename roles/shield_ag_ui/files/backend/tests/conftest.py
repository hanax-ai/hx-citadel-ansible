"""Pytest configuration and fixtures"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient

from src.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_redis_consumer():
    """Mock Redis consumer for testing"""
    pass
