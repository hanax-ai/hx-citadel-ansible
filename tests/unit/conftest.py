"""
Pytest configuration for unit tests

Sets up common test fixtures and imports for all unit tests.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add tests directory to path for common_types import
# common_types.py is located in tests/ directory
TESTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TESTS_DIR))

try:
    import importlib.util

    spec = importlib.util.find_spec("common_types")
    COMMON_TYPES_AVAILABLE = spec is not None
except (ImportError, ValueError):
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
