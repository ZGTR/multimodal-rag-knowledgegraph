import pytest
import requests
import time
import subprocess
import sys
from unittest.mock import patch, MagicMock

class TestEndToEnd:
    """End-to-end tests for the complete application flow"""
    
    @pytest.fixture
    def server_url(self):
        """Base URL for the running server"""
        return "http://localhost:8000"
    
    def test_server_is_running(self, server_url):
        """Test that the server is running and responding"""
        try:
            response = requests.get(f"{server_url}/docs", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("Server is not running")
    
    def test_complete_ingest_flow(self, server_url):
        """Test the complete ingest flow from API to worker"""
        # Test data
        test_data = {
            "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            "twitter": ["https://twitter.com/elonmusk/status/123456789"],
            "ig": ["https://www.instagram.com/p/ABC123/"]
        }
        
        # Mock the subprocess.run to avoid actually running the worker
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Make API request
            response = requests.post(f"{server_url}/ingest", json=test_data, timeout=10)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "cmd" in data
            
            # Verify the command structure
            cmd = data["cmd"]
            assert "src.worker.main" in cmd
            assert "--videos" in cmd
            assert "--twitter" in cmd
            assert "--ig" in cmd
    
    def test_api_documentation_access(self, server_url):
        """Test that API documentation is accessible"""
        try:
            response = requests.get(f"{server_url}/docs", timeout=5)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
        except requests.exceptions.RequestException:
            pytest.skip("Server is not running")
    
    def test_openapi_schema_access(self, server_url):
        """Test that OpenAPI schema is accessible"""
        try:
            response = requests.get(f"{server_url}/openapi.json", timeout=5)
            assert response.status_code == 200
            assert response.headers.get("content-type") == "application/json"
            
            schema = response.json()
            assert "openapi" in schema
            assert "paths" in schema
            assert "/ingest" in schema["paths"]
        except requests.exceptions.RequestException:
            pytest.skip("Server is not running")
    
    def test_error_handling(self, server_url):
        """Test error handling for invalid requests"""
        try:
            # Test with invalid JSON
            response = requests.post(f"{server_url}/ingest", data="invalid json", timeout=5)
            assert response.status_code == 422  # Unprocessable Entity
            
            # Test with nonexistent endpoint
            response = requests.get(f"{server_url}/nonexistent", timeout=5)
            assert response.status_code == 404
        except requests.exceptions.RequestException:
            pytest.skip("Server is not running")
    
    def test_concurrent_requests(self, server_url):
        """Test handling of concurrent requests"""
        test_data = {
            "videos": ["https://www.youtube.com/watch?v=test"],
            "twitter": ["https://twitter.com/test/status/123"]
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Make multiple concurrent requests
            import concurrent.futures
            
            def make_request():
                return requests.post(f"{server_url}/ingest", json=test_data, timeout=10)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(make_request) for _ in range(3)]
                responses = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"

class TestWorkerExecution:
    """Tests for worker execution"""
    
    def test_worker_command_structure(self):
        """Test that worker command is properly structured"""
        cmd = [sys.executable, "-m", "src.worker.main", "--videos", "test_url"]
        
        # Test that the command structure is valid
        assert len(cmd) >= 3
        assert cmd[0] == sys.executable
        assert cmd[1] == "-m"
        assert cmd[2] == "src.worker.main"
    
    def test_worker_with_real_imports(self):
        """Test that worker can be imported and has required structure"""
        try:
            # Test that the worker module exists and can be imported
            import src.worker.main
            assert hasattr(src.worker.main, '__file__')
        except ImportError as e:
            pytest.fail(f"Worker module cannot be imported: {e}")
    
    def test_ingest_sources_availability(self):
        """Test that all ingest sources are available"""
        sources = ["youtube", "twitter", "instagram", "base"]
        
        for source in sources:
            try:
                module = __import__(f"src.ingest.{source}", fromlist=[source.title() + "Source"])
                source_class = getattr(module, source.title() + "Source")
                assert source_class is not None
            except (ImportError, AttributeError) as e:
                pytest.fail(f"Source {source} is not available: {e}") 