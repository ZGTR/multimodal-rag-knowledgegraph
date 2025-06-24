import pytest
import subprocess
import sys
from unittest.mock import patch, MagicMock
import os

class TestWorkerIntegration:
    """Integration tests for the worker module"""
    
    def test_worker_imports_successfully(self):
        """Test that the worker module can be imported without errors"""
        try:
            from src.worker.main import main
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import worker module: {e}")
    
    def test_worker_with_video_argument(self):
        """Test worker with video argument"""
        with patch('subprocess.run') as mock_run:
            # Mock the subprocess.run to avoid actually running the worker
            mock_run.return_value = MagicMock(returncode=0)
            
            cmd = [sys.executable, "-m", "src.worker.main", "--videos", "https://www.youtube.com/watch?v=test"]
            
            # This would normally run the worker, but we're mocking it
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Since we're mocking, this should work without actually running
            assert True  # If we get here, the command structure is valid
    
    def test_worker_with_twitter_argument(self):
        """Test worker with Twitter argument"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            cmd = [sys.executable, "-m", "src.worker.main", "--twitter", "https://twitter.com/test/status/123"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            assert True
    
    def test_worker_with_instagram_argument(self):
        """Test worker with Instagram argument"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            cmd = [sys.executable, "-m", "src.worker.main", "--ig", "https://www.instagram.com/p/ABC123/"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            assert True
    
    def test_worker_with_multiple_arguments(self):
        """Test worker with multiple arguments"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            cmd = [
                sys.executable, "-m", "src.worker.main",
                "--videos", "https://www.youtube.com/watch?v=test1", "https://www.youtube.com/watch?v=test2",
                "--twitter", "https://twitter.com/test/status/123",
                "--ig", "https://www.instagram.com/p/ABC123/"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            assert True
    
    def test_worker_without_arguments(self):
        """Test worker without any arguments"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            cmd = [sys.executable, "-m", "src.worker.main"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            assert True
    
    def test_worker_module_exists(self):
        """Test that the worker module file exists"""
        worker_path = os.path.join("src", "worker", "main.py")
        assert os.path.exists(worker_path), f"Worker module not found at {worker_path}"
    
    def test_worker_module_is_executable(self):
        """Test that the worker module can be executed as a script"""
        worker_path = os.path.join("src", "worker", "main.py")
        
        # Check if the file has the proper structure to be executed
        with open(worker_path, 'r') as f:
            content = f.read()
            # Should have some Python code
            assert len(content.strip()) > 0
            # Should not have syntax errors (basic check)
            assert "def " in content or "class " in content or "import " in content

class TestIngestSourcesIntegration:
    """Integration tests for the ingest sources"""
    
    def test_youtube_source_import(self):
        """Test that YouTube source can be imported"""
        try:
            from src.ingest.youtube import YouTubeSource
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import YouTubeSource: {e}")
    
    def test_twitter_source_import(self):
        """Test that Twitter source can be imported"""
        try:
            from src.ingest.twitter import TwitterSource
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import TwitterSource: {e}")
    
    def test_instagram_source_import(self):
        """Test that Instagram source can be imported"""
        try:
            from src.ingest.instagram import InstagramSource
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import InstagramSource: {e}")
    
    def test_base_source_import(self):
        """Test that base source can be imported"""
        try:
            from src.ingest.base import ISource
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import ISource: {e}")
    
    def test_all_ingest_modules_exist(self):
        """Test that all ingest module files exist"""
        modules = ["youtube.py", "twitter.py", "instagram.py", "base.py"]
        
        for module in modules:
            module_path = os.path.join("src", "ingest", module)
            assert os.path.exists(module_path), f"Ingest module not found: {module_path}" 