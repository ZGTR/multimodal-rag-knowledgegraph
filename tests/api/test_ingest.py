import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
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