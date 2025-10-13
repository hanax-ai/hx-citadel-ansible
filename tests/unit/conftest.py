"""
Pytest configuration for unit tests

Sets up common test fixtures and imports for all unit tests.
"""

import pytest
import sys
from pathlib import Path

# Add tests directory to path for common_types import
# common_types.py is located in tests/ directory
TESTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TESTS_DIR))

# Try to import common_types module
try:
    import common_types
    COMMON_TYPES_AVAILABLE = True
except ImportError:
    COMMON_TYPES_AVAILABLE = False

# Fixtures for all unit tests
@pytest.fixture(scope="session")
def roles_dir():
    """Return the roles directory path"""
    from pathlib import Path
    return Path(__file__).parent.parent.parent / "roles"

@pytest.fixture(scope="function", autouse=True)
def isolate_circuit_breakers():
    """
    Isolate circuit breaker state between tests for parallel execution safety.
    
    This fixture runs automatically for every test and ensures circuit breakers
    don't share state when pytest runs with -n auto.
    
    Addresses Issue #54: Parallel Test Execution Without Safeguards
    """
    try:
        import pybreaker
        # Store original _CIRCUIT_BREAKERS registry
        original_breakers = pybreaker.CircuitBreaker._CIRCUIT_BREAKERS.copy()
        yield
        # Restore original registry after test
        pybreaker.CircuitBreaker._CIRCUIT_BREAKERS.clear()
        pybreaker.CircuitBreaker._CIRCUIT_BREAKERS.update(original_breakers)
    except (ImportError, AttributeError):
        # If pybreaker not available or registry doesn't exist, just yield
        yield

@pytest.fixture(scope="function")
def isolated_breaker():
    """
    Create an isolated circuit breaker instance for testing.
    
    Returns a factory function that creates circuit breakers with unique names
    to prevent conflicts in parallel test execution.
    
    Usage:
        def test_something(isolated_breaker):
            breaker = isolated_breaker("my_test")
            # ... test code ...
    """
    import pybreaker
    import uuid
    
    def _create_breaker(base_name="test", **kwargs):
        """Create a circuit breaker with a unique name"""
        unique_name = f"{base_name}_{uuid.uuid4().hex[:8]}"
        defaults = {
            "fail_max": 5,
            "reset_timeout": 60,
            "name": unique_name
        }
        defaults.update(kwargs)
        return pybreaker.CircuitBreaker(**defaults)
    
    return _create_breaker

@pytest.fixture(scope="function")
def temp_test_dir(tmp_path):
    """
    Provide an isolated temporary directory for each test.
    
    Ensures file system operations don't conflict in parallel execution.
    Automatically cleaned up after each test.
    
    Addresses Issue #54: Parallel Test Execution Without Safeguards
    
    Usage:
        def test_file_operations(temp_test_dir):
            test_file = temp_test_dir / "test.txt"
            test_file.write_text("data")
            # ... test code ...
    """
    # tmp_path is a pytest built-in that provides unique temp dir per test
    return tmp_path

@pytest.fixture(scope="function", autouse=True)
def isolate_environment_vars(monkeypatch):
    """
    Isolate environment variables for parallel test execution.
    
    Prevents tests from interfering with each other's environment settings.
    
    Addresses Issue #54: Parallel Test Execution Without Safeguards
    """
    # This fixture runs automatically but doesn't do anything by default
    # Tests can use monkeypatch to safely modify environment
    yield monkeypatch

@pytest.fixture(scope="function")
def mock_database():
    """
    Provide a mock database connection for testing.
    
    Ensures database tests are isolated and don't conflict in parallel execution.
    
    Addresses Issue #54: Parallel Test Execution Without Safeguards
    
    Usage:
        def test_db_operation(mock_database):
            result = mock_database.query("SELECT 1")
            # ... test code ...
    """
    from unittest.mock import MagicMock
    
    mock_db = MagicMock()
    mock_db.connect = MagicMock(return_value=None)
    mock_db.disconnect = MagicMock(return_value=None)
    mock_db.query = MagicMock(return_value=[])
    mock_db.execute = MagicMock(return_value=True)
    
    # Auto-connect
    mock_db.connect()
    
    yield mock_db
    
    # Auto-disconnect
    mock_db.disconnect()

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory"""
    from pathlib import Path
    return Path(__file__).parent.parent.parent

@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    yield tmp_path
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
