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
            assert "src.worker.ingest_worker" in data["cmd"]
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
            assert "src.worker.ingest_worker" in data["cmd"]
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

class TestEntitiesEndpoint:
    """Test cases for the /entities endpoint"""
    
    def test_get_entities_success(self, client):
        """Test successful retrieval of entities"""
        mock_entities = [
            {
                "id": "youtube:dQw4w9WgXcQ",
                "label": "Content",
                "properties": {
                    "node_type": "Content",
                    "title": "Test Video",
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                }
            },
            {
                "id": "entity:test_entity",
                "label": "Entity",
                "properties": {
                    "node_type": "Entity",
                    "name": "Test Entity",
                    "type": "extracted"
                }
            }
        ]
        
        with patch('src.api.handler.GremlinKG') as mock_kg:
            mock_kg_instance = MagicMock()
            mock_kg_instance.get_all_entities.return_value = mock_entities
            mock_kg.return_value = mock_kg_instance
            
            response = client.get("/entities")
            
            assert response.status_code == 200
            data = response.json()
            
            # Expected output structure
            expected_output = {
                "status": "success",
                "count": 2,
                "entities": mock_entities
            }
            
            assert data == expected_output
            assert data["status"] == "success"
            assert data["count"] == 2
            assert len(data["entities"]) == 2
            assert data["entities"][0]["id"] == "youtube:dQw4w9WgXcQ"
            assert data["entities"][1]["id"] == "entity:test_entity"
    
    def test_get_entities_empty(self, client):
        """Test retrieval of entities when knowledge graph is empty"""
        with patch('src.api.handler.GremlinKG') as mock_kg:
            mock_kg_instance = MagicMock()
            mock_kg_instance.get_all_entities.return_value = []
            mock_kg.return_value = mock_kg_instance
            
            response = client.get("/entities")
            
            assert response.status_code == 200
            data = response.json()
            
            expected_output = {
                "status": "success",
                "count": 0,
                "entities": []
            }
            
            assert data == expected_output
            assert data["status"] == "success"
            assert data["count"] == 0
            assert len(data["entities"]) == 0
    
    def test_get_entities_error(self, client):
        """Test entities endpoint when knowledge graph fails"""
        with patch('src.api.handler.GremlinKG') as mock_kg:
            mock_kg_instance = MagicMock()
            mock_kg_instance.get_all_entities.side_effect = Exception("Connection failed")
            mock_kg.return_value = mock_kg_instance
            
            response = client.get("/entities")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "error"
            assert "message" in data
            assert "Connection failed" in data["message"]
            assert data["entities"] == []

class TestGraphEndpoint:
    """Test cases for the /graph endpoint"""
    
    def test_get_graph_success(self, client):
        """Test successful retrieval of the complete knowledge graph"""
        mock_graph = {
            "nodes": [
                {
                    "id": "youtube:dQw4w9WgXcQ",
                    "label": "Content",
                    "properties": {"node_type": "Content"}
                },
                {
                    "id": "entity:test_entity",
                    "label": "Entity", 
                    "properties": {"node_type": "Entity"}
                }
            ],
            "edges": [
                {
                    "id": "edge:youtube:dQw4w9WgXcQ:entity:test_entity:contains_entity",
                    "source": "youtube:dQw4w9WgXcQ",
                    "target": "entity:test_entity",
                    "label": "contains_entity"
                }
            ],
            "total_nodes": 2,
            "total_edges": 1
        }
        
        with patch('src.api.handler.GremlinKG') as mock_kg:
            mock_kg_instance = MagicMock()
            mock_kg_instance.get_whole_graph.return_value = mock_graph
            mock_kg.return_value = mock_kg_instance
            
            response = client.get("/graph")
            
            assert response.status_code == 200
            data = response.json()
            
            expected_output = {
                "status": "success",
                "graph": mock_graph
            }
            
            assert data == expected_output
            assert data["status"] == "success"
            assert "graph" in data
            assert data["graph"]["total_nodes"] == 2
            assert data["graph"]["total_edges"] == 1
            assert len(data["graph"]["nodes"]) == 2
            assert len(data["graph"]["edges"]) == 1
    
    def test_get_graph_empty(self, client):
        """Test retrieval of graph when knowledge graph is empty"""
        empty_graph = {
            "nodes": [],
            "edges": [],
            "total_nodes": 0,
            "total_edges": 0
        }
        
        with patch('src.api.handler.GremlinKG') as mock_kg:
            mock_kg_instance = MagicMock()
            mock_kg_instance.get_whole_graph.return_value = empty_graph
            mock_kg.return_value = mock_kg_instance
            
            response = client.get("/graph")
            
            assert response.status_code == 200
            data = response.json()
            
            expected_output = {
                "status": "success",
                "graph": empty_graph
            }
            
            assert data == expected_output
            assert data["status"] == "success"
            assert data["graph"]["total_nodes"] == 0
            assert data["graph"]["total_edges"] == 0
    
    def test_get_graph_error(self, client):
        """Test graph endpoint when knowledge graph fails"""
        with patch('src.api.handler.GremlinKG') as mock_kg:
            mock_kg_instance = MagicMock()
            mock_kg_instance.get_whole_graph.side_effect = Exception("Graph retrieval failed")
            mock_kg.return_value = mock_kg_instance
            
            response = client.get("/graph")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "error"
            assert "message" in data
            assert "Graph retrieval failed" in data["message"]
            assert data["graph"]["total_nodes"] == 0
            assert data["graph"]["total_edges"] == 0

class TestSearchEndpoint:
    """Test cases for the /search endpoint"""
    
    def test_search_success(self, client):
        """Test successful document search"""
        mock_documents = [
            {
                "content": "This is a test document about AI and machine learning.",
                "metadata": {
                    "source": "youtube:dQw4w9WgXcQ",
                    "title": "AI Tutorial",
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                }
            },
            {
                "content": "Another document about artificial intelligence.",
                "metadata": {
                    "source": "youtube:test123",
                    "title": "ML Basics",
                    "url": "https://www.youtube.com/watch?v=test123"
                }
            }
        ]
        
        with patch('src.api.handler.get_vectorstore') as mock_get_vectorstore:
            mock_vectorstore = MagicMock()
            mock_vectorstore.search.return_value = [
                MagicMock(page_content=doc["content"], metadata=doc["metadata"])
                for doc in mock_documents
            ]
            mock_get_vectorstore.return_value = mock_vectorstore
            
            response = client.get("/search?query=AI&k=5")
            
            assert response.status_code == 200
            data = response.json()
            
            expected_output = {
                "status": "success",
                "query": "AI",
                "count": 2,
                "results": mock_documents
            }
            
            assert data == expected_output
            assert data["status"] == "success"
            assert data["query"] == "AI"
            assert data["count"] == 2
            assert len(data["results"]) == 2
            assert "AI" in data["results"][0]["content"]
    
    def test_search_with_default_k(self, client):
        """Test search with default k parameter"""
        mock_documents = [
            {
                "page_content": "Test document",
                "metadata": {"source": "test"}
            }
        ]
        
        with patch('src.api.handler.get_vectorstore') as mock_get_vectorstore:
            mock_vectorstore = MagicMock()
            mock_vectorstore.search.return_value = [
                MagicMock(page_content=doc["page_content"], metadata=doc["metadata"])
                for doc in mock_documents
            ]
            mock_get_vectorstore.return_value = mock_vectorstore
            
            response = client.get("/search?query=test")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert data["query"] == "test"
            assert data["count"] == 1
            # Verify that default k=5 was used
            mock_vectorstore.search.assert_called_with("test", k=5)
    
    def test_search_with_custom_k(self, client):
        """Test search with custom k parameter"""
        with patch('src.api.handler.get_vectorstore') as mock_get_vectorstore:
            mock_vectorstore = MagicMock()
            mock_vectorstore.search.return_value = []
            mock_get_vectorstore.return_value = mock_vectorstore
            
            response = client.get("/search?query=test&k=10")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert data["query"] == "test"
            assert data["count"] == 0
            # Verify that custom k=10 was used
            mock_vectorstore.search.assert_called_with("test", k=10)
    
    def test_search_empty_results(self, client):
        """Test search when no results are found"""
        with patch('src.api.handler.get_vectorstore') as mock_get_vectorstore:
            mock_vectorstore = MagicMock()
            mock_vectorstore.search.return_value = []
            mock_get_vectorstore.return_value = mock_vectorstore
            
            response = client.get("/search?query=nonexistent&k=5")
            
            assert response.status_code == 200
            data = response.json()
            
            expected_output = {
                "status": "success",
                "query": "nonexistent",
                "count": 0,
                "results": []
            }
            
            assert data == expected_output
            assert data["status"] == "success"
            assert data["count"] == 0
            assert len(data["results"]) == 0
    
    def test_search_vectorstore_unavailable(self, client):
        """Test search when vector store is not available"""
        with patch('src.api.handler.get_vectorstore') as mock_get_vectorstore:
            mock_get_vectorstore.return_value = None
            
            response = client.get("/search?query=test&k=5")
            
            assert response.status_code == 200
            data = response.json()
            
            expected_output = {
                "status": "error",
                "message": "Vector store not available",
                "results": []
            }
            
            assert data == expected_output
            assert data["status"] == "error"
            assert "Vector store not available" in data["message"]
    
    def test_search_error(self, client):
        """Test search when vector store throws an error"""
        with patch('src.api.handler.get_vectorstore') as mock_get_vectorstore:
            mock_vectorstore = MagicMock()
            mock_vectorstore.search.side_effect = Exception("Search failed")
            mock_get_vectorstore.return_value = mock_vectorstore
            
            response = client.get("/search?query=test&k=5")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "error"
            assert "message" in data
            assert "Search failed" in data["message"]
            assert data["results"] == []
    
    def test_search_missing_query(self, client):
        """Test search without query parameter"""
        response = client.get("/search")
        assert response.status_code == 422  # Validation error
    
    def test_search_invalid_k(self, client):
        """Test search with invalid k parameter"""
        response = client.get("/search?query=test&k=invalid")
        assert response.status_code == 422  # Validation error

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
        assert "/entities" in data["paths"]
        assert "/graph" in data["paths"]
        assert "/search" in data["paths"]
    
    def test_root_endpoint_not_found(self, client):
        """Test that root endpoint returns 404"""
        response = client.get("/")
        assert response.status_code == 404
    
    def test_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404 