#!/usr/bin/env python3
"""
Test script for AWS Neptune connection and basic operations.
Run this to verify your Neptune setup is working correctly.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.kg.gremlin_client import GremlinKG
from src.bootstrap.settings import get_settings

def test_neptune_connection():
    """Test Neptune connection and basic operations."""
    print("🧪 Testing AWS Neptune Connection")
    print("=" * 40)
    
    # Load settings
    settings = get_settings()
    
    print(f"Neptune Endpoint: {settings.NEPTUNE_CLUSTER_ENDPOINT}")
    print(f"Neptune Port: {settings.NEPTUNE_PORT}")
    print(f"Neptune Region: {settings.NEPTUNE_REGION}")
    print(f"Use SSL: {settings.NEPTUNE_USE_SSL}")
    print()
    
    try:
        # Initialize knowledge graph
        print("🔌 Initializing GremlinKG...")
        kg = GremlinKG()
        
        if kg.in_memory:
            print("⚠️  Using in-memory fallback (Neptune not available)")
            return False
        
        print("✅ Neptune connection successful!")
        
        # Test basic operations
        print("\n🧪 Testing basic operations...")
        
        # Test entity retrieval
        print("📊 Getting all entities...")
        entities = kg.get_all_entities()
        print(f"Found {len(entities)} entities")
        
        # Test graph retrieval
        print("📊 Getting whole graph...")
        graph = kg.get_whole_graph()
        print(f"Graph has {graph['total_nodes']} nodes and {graph['total_edges']} edges")
        
        print("\n✅ All tests passed! Neptune is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Neptune test failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if Neptune cluster is running")
        print("2. Verify security group allows port 8182")
        print("3. Confirm endpoint is correct")
        print("4. Check SSL configuration")
        return False

def test_local_gremlin():
    """Test local Gremlin server connection."""
    print("\n🧪 Testing Local Gremlin Server")
    print("=" * 40)
    
    try:
        # Temporarily set local endpoint
        os.environ['KG_URI'] = 'ws://localhost:8182'
        
        kg = GremlinKG()
        
        if kg.in_memory:
            print("⚠️  Local Gremlin server not available")
            print("💡 To run local Gremlin server:")
            print("   docker run -p 8182:8182 tinkerpop/gremlin-server")
            return False
        
        print("✅ Local Gremlin server connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Local Gremlin test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Neptune Connection Test Suite")
    print("=" * 50)
    
    # Test Neptune first
    neptune_success = test_neptune_connection()
    
    # Test local Gremlin as fallback
    if not neptune_success:
        local_success = test_local_gremlin()
        
        if not local_success:
            print("\n❌ No graph database available!")
            print("Please set up either:")
            print("1. AWS Neptune cluster (run ./setup_neptune.sh)")
            print("2. Local Gremlin server (docker run -p 8182:8182 tinkerpop/gremlin-server)")
    else:
        print("\n🎉 Neptune is ready to use!")
        print("You can now run your application with:")
        print("python -m uvicorn src.api.handler:app --reload --host 0.0.0.0 --port 8000") 