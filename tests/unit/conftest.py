"""
Pytest configuration for unit tests

Sets up common test fixtures and imports for all unit tests.
"""

import pytest
import sys
import tempfile
import os

# Add common_types module to path (deployed location)
# Configurable via COMMON_TYPES_PATH environment variable for testing flexibility
COMMON_TYPES_PATH = os.getenv("COMMON_TYPES_PATH", "/tmp/common_types_test")
sys.path.insert(0, COMMON_TYPES_PATH)

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
