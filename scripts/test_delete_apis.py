#!/usr/bin/env python3
"""
Test script for the delete APIs
Tests both vector store and knowledge graph deletion endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_vector_store_delete():
    """Test deleting all documents from vector store"""
    print("🧹 Testing Vector Store Delete API...")
    
    # First check current document count
    try:
        response = requests.get(f"{BASE_URL}/search?query=test&k=1")
        print(f"   Search response status: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Could not test search: {e}")
    
    # Delete all documents
    try:
        response = requests.delete(f"{BASE_URL}/search")
        print(f"   Delete response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Delete successful: {data}")
            print(f"   📊 Deleted {data.get('deleted_count', 0)} documents")
            print(f"   ⏱️  Processing time: {data.get('processing_time', 'N/A')}")
        else:
            print(f"   ❌ Delete failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Delete request failed: {e}")

def test_knowledge_graph_delete():
    """Test deleting all nodes and edges from knowledge graph"""
    print("\n🧹 Testing Knowledge Graph Delete API...")
    
    # First check current graph state
    try:
        response = requests.get(f"{BASE_URL}/graph/debug")
        print(f"   Debug response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Current state: {data.get('node_count', 0)} nodes, {data.get('total_edges', 0)} edges")
    except Exception as e:
        print(f"   ⚠️  Could not check current state: {e}")
    
    # Delete all graph data
    try:
        response = requests.delete(f"{BASE_URL}/graph")
        print(f"   Delete response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Delete successful: {data}")
            print(f"   📊 Deleted {data.get('deleted_nodes', 0)} nodes and {data.get('deleted_edges', 0)} edges")
            print(f"   ⏱️  Processing time: {data.get('processing_time', 'N/A')}")
        else:
            print(f"   ❌ Delete failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Delete request failed: {e}")

def test_both_deletes():
    """Test both delete APIs in sequence"""
    print("🧹 Testing Both Delete APIs...")
    
    # Test vector store delete
    test_vector_store_delete()
    
    # Wait a moment
    time.sleep(1)
    
    # Test knowledge graph delete
    test_knowledge_graph_delete()
    
    print("\n✅ Delete API tests completed!")

if __name__ == "__main__":
    print("🧪 Testing Delete APIs")
    print("=" * 50)
    
    try:
        test_both_deletes()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test script finished") 