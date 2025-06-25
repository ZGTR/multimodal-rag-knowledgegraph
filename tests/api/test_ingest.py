import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from src.api.routers.ingest import router as ingest_router
from src.api.main import app

class TestIngestEndpoint:
    def test_ingest_with_all_sources(self, client, sample_ingest_request):
        with patch('subprocess.run') as mock_run:
            response = client.post("/ingest", json=sample_ingest_request)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "cmd" in data
            assert "src.worker.ingest_worker" in data["cmd"]
            assert "--videos" in data["cmd"]
            assert "--twitter" in data["cmd"]
            assert "--ig" in data["cmd"]
    # ... (repeat for all other /ingest tests from test_handler.py) 

class TestYouTubeIngestStrategy:
    def test_store_content_with_entities_called(self):
        from src.worker.strategies.youtube import YouTubeIngestStrategy
        # Mock vector store and KG
        mock_vectordb = MagicMock()
        mock_kg = MagicMock()
        # Patch the YouTubeVideoSource to return a mock video item
        mock_video_item = MagicMock()
        mock_video_item.id = "testid"
        mock_video_item.title = "Test Title"
        mock_video_item.description = "Test Description"
        mock_video_item.url = "http://youtube.com/testid"
        mock_video_item.author = "Test Author"
        mock_video_item.duration = 123
        mock_video_item.thumbnail_url = "http://img"
        mock_video_item.published_at = MagicMock()
        mock_video_item.published_at.isoformat.return_value = "2024-01-01T00:00:00Z"
        mock_segment = MagicMock()
        mock_segment.start_time = 0.0
        mock_segment.end_time = 10.0
        mock_segment.text = "Test segment text"
        mock_segment.entities = ["Test Entity"]
        mock_segment.topics = []
        mock_segment.visual_entities = []
        mock_segment.confidence = 1.0
        mock_video_item.segments = [mock_segment]
        
        with patch("src.worker.strategies.youtube.YouTubeVideoSource") as mock_source_cls:
            mock_source = MagicMock()
            mock_source.fetch_video.return_value = [mock_video_item]
            mock_source_cls.return_value = mock_source
            strategy = YouTubeIngestStrategy(vectordb=mock_vectordb, kg=mock_kg)
            strategy.ingest(["testid"])
            # Assert store_content_with_entities called for video and segment
            assert mock_kg.store_content_with_entities.call_count >= 1 