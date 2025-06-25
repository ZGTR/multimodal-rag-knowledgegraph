"""
Integration tests for the API endpoints with real data and expected outputs.
These tests demonstrate the actual behavior of the API endpoints.
"""

import pytest
import requests
import time
import json
from typing import Dict, Any

# Base URL for the API
BASE_URL = "http://localhost:8000"

class TestAPIIntegration:
    """Integration tests for all API endpoints"""
    
    def test_health_check(self):
        """Test that the API server is running"""
        try:
            response = requests.get(f"{BASE_URL}/docs")
            assert response.status_code == 200
            print("✅ API server is running and accessible")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running. Start it with: python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
    
    def test_ingest_youtube_video(self):
        """Test ingesting a YouTube video and verify the expected output"""
        # Test data
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Make ingest request
        ingest_data = {
            "videos": [test_video_url]
        }
        
        response = requests.post(f"{BASE_URL}/ingest", json=ingest_data)
        
        # Expected output structure
        expected_output = {
            "status": "queued",
            "cmd": ["python", "-m", "src.worker.ingest_worker", "--videos", test_video_url]
        }
        
        print(f"\n📥 Ingest Request:")
        print(f"   URL: {test_video_url}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "cmd" in data
        assert "src.worker.ingest_worker" in data["cmd"]
        assert "--videos" in data["cmd"]
        assert test_video_url in data["cmd"]
        
        print("✅ Ingest request successful")
        
        # Wait for processing to complete
        print("⏳ Waiting for ingestion to complete...")
        time.sleep(15)
        
        return test_video_url
    
    def test_get_entities_after_ingestion(self):
        """Test retrieving entities after ingestion"""
        # First ingest a video
        video_url = self.test_ingest_youtube_video()
        
        # Get entities
        response = requests.get(f"{BASE_URL}/entities")
        
        print(f"\n📊 Entities Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Expected output structure
            expected_structure = {
                "status": str,  # "success" or "error"
                "count": int,
                "entities": list
            }
            
            # Verify response structure
            assert "status" in data
            assert "count" in data
            assert "entities" in data
            assert isinstance(data["count"], int)
            assert isinstance(data["entities"], list)
            
            if data["status"] == "success":
                print(f"✅ Found {data['count']} entities")
                
                # If entities exist, verify their structure
                if data["entities"]:
                    entity = data["entities"][0]
                    assert "id" in entity
                    assert "properties" in entity
                    
                    print(f"   Sample entity: {entity['id']}")
                    if "properties" in entity and entity["properties"]:
                        print(f"   Properties: {list(entity['properties'].keys())}")
            else:
                print(f"⚠️  Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ Failed to get entities: {response.status_code}")
            pytest.fail(f"Failed to get entities: {response.status_code}")
    
    def test_get_graph_after_ingestion(self):
        """Test retrieving the complete knowledge graph after ingestion"""
        # First ingest a video
        video_url = self.test_ingest_youtube_video()
        
        # Get graph
        response = requests.get(f"{BASE_URL}/graph")
        
        print(f"\n🕸️  Graph Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Expected output structure
            expected_structure = {
                "status": str,  # "success" or "error"
                "graph": {
                    "nodes": list,
                    "edges": list,
                    "total_nodes": int,
                    "total_edges": int
                }
            }
            
            # Verify response structure
            assert "status" in data
            assert "graph" in data
            assert "nodes" in data["graph"]
            assert "edges" in data["graph"]
            assert "total_nodes" in data["graph"]
            assert "total_edges" in data["graph"]
            
            if data["status"] == "success":
                graph = data["graph"]
                print(f"✅ Graph contains {graph['total_nodes']} nodes and {graph['total_edges']} edges")
                
                # If nodes exist, verify their structure
                if graph["nodes"]:
                    node = graph["nodes"][0]
                    assert "id" in node
                    print(f"   Sample node: {node['id']}")
                
                # If edges exist, verify their structure
                if graph["edges"]:
                    edge = graph["edges"][0]
                    assert "source" in edge
                    assert "target" in edge
                    print(f"   Sample edge: {edge['source']} -> {edge['target']}")
            else:
                print(f"⚠️  Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ Failed to get graph: {response.status_code}")
            pytest.fail(f"Failed to get graph: {response.status_code}")
    
    def test_search_documents(self):
        """Test searching documents in the vector store"""
        # First ingest a video to ensure we have data
        video_url = self.test_ingest_youtube_video()
        
        # Test search with different queries
        test_queries = [
            {"query": "test", "k": 5},
            {"query": "video", "k": 3},
            {"query": "content", "k": 10}
        ]
        
        for test_case in test_queries:
            query = test_case["query"]
            k = test_case["k"]
            
            response = requests.get(f"{BASE_URL}/search?query={query}&k={k}")
            
            print(f"\n🔍 Search Response (query='{query}', k={k}):")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                # Expected output structure
                expected_structure = {
                    "status": str,  # "success" or "error"
                    "query": str,
                    "count": int,
                    "results": list
                }
                
                # Verify response structure
                assert "status" in data
                assert "query" in data
                assert "count" in data
                assert "results" in data
                assert data["query"] == query
                assert isinstance(data["count"], int)
                assert isinstance(data["results"], list)
                
                if data["status"] == "success":
                    print(f"✅ Found {data['count']} results for query '{query}'")
                    
                    # If results exist, verify their structure
                    if data["results"]:
                        result = data["results"][0]
                        assert "content" in result
                        assert "metadata" in result
                        
                        print(f"   Sample result content: {result['content'][:100]}...")
                        print(f"   Sample result metadata: {list(result['metadata'].keys())}")
                else:
                    print(f"⚠️  Error: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ Failed to search: {response.status_code}")
    
    def test_search_with_default_parameters(self):
        """Test search with default k parameter"""
        response = requests.get(f"{BASE_URL}/search?query=test")
        
        print(f"\n🔍 Search with Default Parameters:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            assert data["status"] in ["success", "error"]
            assert data["query"] == "test"
            assert "count" in data
            assert "results" in data
            
            print("✅ Search with default parameters successful")
        else:
            print(f"❌ Failed to search with default parameters: {response.status_code}")
    
    def test_search_error_handling(self):
        """Test search error handling with invalid parameters"""
        # Test missing query parameter
        response = requests.get(f"{BASE_URL}/search")
        print(f"\n🔍 Search Error Handling - Missing Query:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Correctly rejected request with missing query parameter")
        else:
            print(f"⚠️  Unexpected response for missing query: {response.status_code}")
        
        # Test invalid k parameter
        response = requests.get(f"{BASE_URL}/search?query=test&k=invalid")
        print(f"\n🔍 Search Error Handling - Invalid k:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Correctly rejected request with invalid k parameter")
        else:
            print(f"⚠️  Unexpected response for invalid k: {response.status_code}")
    
    def test_api_documentation(self):
        """Test that API documentation is accessible"""
        response = requests.get(f"{BASE_URL}/docs")
        
        print(f"\n📚 API Documentation:")
        print(f"   Status Code: {response.status_code}")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        print("✅ API documentation is accessible")
        
        # Test OpenAPI schema
        response = requests.get(f"{BASE_URL}/openapi.json")
        
        print(f"\n📋 OpenAPI Schema:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data
            assert "paths" in data
            
            # Check that all our endpoints are documented
            expected_endpoints = ["/ingest", "/entities", "/graph", "/search"]
            for endpoint in expected_endpoints:
                assert endpoint in data["paths"]
            
            print("✅ OpenAPI schema is accessible and complete")
            print(f"   Available endpoints: {list(data['paths'].keys())}")
        else:
            print(f"❌ Failed to get OpenAPI schema: {response.status_code}")

def run_integration_tests():
    """Run all integration tests and show results"""
    print("🚀 Starting API Integration Tests")
    print("=" * 50)
    
    test_instance = TestAPIIntegration()
    
    try:
        # Test API health
        test_instance.test_health_check()
        
        # Test ingest functionality
        test_instance.test_ingest_youtube_video()
        
        # Test entity retrieval
        test_instance.test_get_entities_after_ingestion()
        
        # Test graph retrieval
        test_instance.test_get_graph_after_ingestion()
        
        # Test search functionality
        test_instance.test_search_documents()
        test_instance.test_search_with_default_parameters()
        test_instance.test_search_error_handling()
        
        # Test API documentation
        test_instance.test_api_documentation()
        
        print("\n" + "=" * 50)
        print("✅ All integration tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise

if __name__ == "__main__":
    run_integration_tests() 