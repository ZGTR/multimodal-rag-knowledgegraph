import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

class TestIngestEndpoint:
    """Test cases for the /ingest endpoint"""
    
    def test_ingest_with_all_sources(self, client, sample_ingest_request):
        """Test ingest endpoint with all data sources"""
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", json=sample_ingest_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "cmd" in data
            assert "src.worker.main" in data["cmd"]
            assert "--videos" in data["cmd"]
            assert "--twitter" in data["cmd"]
            assert "--ig" in data["cmd"]
    
    def test_ingest_with_videos_only(self, client, sample_video_only_request):
        """Test ingest endpoint with only video URLs"""
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", json=sample_video_only_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "--videos" in data["cmd"]
            assert "--twitter" not in data["cmd"]
            assert "--ig" not in data["cmd"]
    
    def test_ingest_with_twitter_only(self, client, sample_twitter_only_request):
        """Test ingest endpoint with only Twitter URLs"""
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", json=sample_twitter_only_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "--twitter" in data["cmd"]
            assert "--videos" not in data["cmd"]
            assert "--ig" not in data["cmd"]
    
    def test_ingest_with_empty_request(self, client, sample_empty_request):
        """Test ingest endpoint with empty request"""
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", json=sample_empty_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "src.worker.main" in data["cmd"]
            # Should not have any source-specific flags
            assert "--videos" not in data["cmd"]
            assert "--twitter" not in data["cmd"]
            assert "--ig" not in data["cmd"]
    
    def test_ingest_with_partial_data(self, client):
        """Test ingest endpoint with partial data (only videos and Twitter)"""
        request_data = {
            "videos": ["https://www.youtube.com/watch?v=test1"],
            "twitter": ["https://twitter.com/test/status/123"]
        }
        
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "--videos" in data["cmd"]
            assert "--twitter" in data["cmd"]
            assert "--ig" not in data["cmd"]
    
    def test_ingest_with_multiple_urls_per_source(self, client):
        """Test ingest endpoint with multiple URLs per source"""
        request_data = {
            "videos": [
                "https://www.youtube.com/watch?v=test1",
                "https://www.youtube.com/watch?v=test2"
            ],
            "twitter": [
                "https://twitter.com/test1/status/123",
                "https://twitter.com/test2/status/456"
            ],
            "ig": [
                "https://www.instagram.com/p/ABC123/",
                "https://www.instagram.com/p/DEF456/"
            ]
        }
        
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            cmd = data["cmd"]
            
            # Check that all URLs are included in the command
            cmd_str = " ".join(cmd)
            assert "test1" in cmd_str
            assert "test2" in cmd_str
            assert "ABC123" in cmd_str
            assert "DEF456" in cmd_str
    
    def test_ingest_with_invalid_json(self, client):
        """Test ingest endpoint with invalid JSON"""
        response = client.post("/ingest", data="invalid json")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_ingest_with_missing_content_type(self, client, sample_ingest_request):
        """Test ingest endpoint without Content-Type header"""
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", data=json.dumps(sample_ingest_request))
            assert response.status_code == 200  # FastAPI should still process it
    
    def test_ingest_with_none_values(self, client):
        """Test ingest endpoint with None values"""
        request_data = {
            "videos": None,
            "twitter": None,
            "ig": None
        }
        
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            # Should not have any source-specific flags
            assert "--videos" not in data["cmd"]
            assert "--twitter" not in data["cmd"]
            assert "--ig" not in data["cmd"]

class TestAPIEndpoints:
    """Test cases for other API endpoints"""
    
    def test_docs_endpoint(self, client):
        """Test that the docs endpoint is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_endpoint(self, client):
        """Test that the OpenAPI schema endpoint is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/ingest" in data["paths"]
    
    def test_root_endpoint_not_found(self, client):
        """Test that root endpoint returns 404"""
        response = client.get("/")
        assert response.status_code == 404
    
    def test_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404 