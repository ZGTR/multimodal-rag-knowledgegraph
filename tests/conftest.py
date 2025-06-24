import pytest
from fastapi.testclient import TestClient
from src.api.handler import app
import tempfile
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)

@pytest.fixture
def sample_ingest_request():
    """Sample ingest request data"""
    return {
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "twitter": ["https://twitter.com/elonmusk/status/123456789"],
        "ig": ["https://www.instagram.com/p/ABC123/"]
    }

@pytest.fixture
def sample_video_only_request():
    """Sample request with only video URLs"""
    return {
        "videos": ["https://www.youtube.com/watch?v=9bZkp7q19f0"]
    }

@pytest.fixture
def sample_twitter_only_request():
    """Sample request with only Twitter URLs"""
    return {
        "twitter": ["https://twitter.com/OpenAI/status/123456789"]
    }

@pytest.fixture
def sample_empty_request():
    """Sample request with no URLs"""
    return {}

@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir 