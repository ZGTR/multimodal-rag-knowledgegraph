#!/usr/bin/env python3
"""
Test script for temporal search API endpoints
"""

import requests
import json
import time
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"
TEMPORAL_BASE = f"{BASE_URL}/temporal"

def test_temporal_search():
    """Test temporal search endpoint"""
    print("\n=== Testing Temporal Search ===")
    
    payload = {
        "query": "artificial intelligence",
        "max_results": 5
    }
    
    try:
        response = requests.post(f"{TEMPORAL_BASE}/search", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Query: {result['query']}")
            print(f"Results Count: {result['results_count']}")
            
            for i, search_result in enumerate(result['results'][:3]):  # Show first 3
                print(f"  {i+1}. Video: {search_result['video_id']}")
                print(f"     Time: {search_result['start_time']:.1f}s - {search_result['end_time']:.1f}s")
                print(f"     Text: {search_result['matched_text'][:100]}...")
                print(f"     Entities: {search_result['entities']}")
                print()
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Temporal search failed: {e}")
        return False

def test_entity_search():
    """Test entity search endpoint"""
    print("\n=== Testing Entity Search ===")
    
    payload = {
        "entity": "Elon Musk",
        "max_results": 3
    }
    
    try:
        response = requests.post(f"{TEMPORAL_BASE}/search-entity", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Query: {result['query']}")
            print(f"Results Count: {result['results_count']}")
            
            for i, search_result in enumerate(result['results']):
                print(f"  {i+1}. Video: {search_result['video_id']}")
                print(f"     Time: {search_result['start_time']:.1f}s - {search_result['end_time']:.1f}s")
                print(f"     Context: {search_result['matched_text'][:100]}...")
                print()
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Entity search failed: {e}")
        return False

def test_topic_search():
    """Test topic search endpoint"""
    print("\n=== Testing Topic Search ===")
    
    payload = {
        "topic": "machine learning",
        "max_results": 3
    }
    
    try:
        response = requests.post(f"{TEMPORAL_BASE}/search-topic", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Query: {result['query']}")
            print(f"Results Count: {result['results_count']}")
            
            for i, search_result in enumerate(result['results']):
                print(f"  {i+1}. Video: {search_result['video_id']}")
                print(f"     Time: {search_result['start_time']:.1f}s - {search_result['end_time']:.1f}s")
                print(f"     Context: {search_result['matched_text'][:100]}...")
                print()
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Topic search failed: {e}")
        return False

def test_video_timeline():
    """Test video timeline endpoint"""
    print("\n=== Testing Video Timeline ===")
    
    video_id = "dQw4w9WgXcQ"
    
    try:
        response = requests.get(f"{TEMPORAL_BASE}/video-timeline/{video_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            timeline = response.json()
            print(f"Video: {video_id}")
            print(f"Segments: {len(timeline)}")
            
            for i, segment in enumerate(timeline[:5]):  # Show first 5 segments
                print(f"  {i+1}. {segment['start_time']:.1f}s - {segment['end_time']:.1f}s")
                if segment['entities']:
                    print(f"     Entities: {', '.join(segment['entities'])}")
                print()
            
            if len(timeline) > 5:
                print(f"  ... and {len(timeline) - 5} more segments")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Video timeline failed: {e}")
        return False

def test_video_info():
    """Test video info endpoint"""
    print("\n=== Testing Video Info ===")
    
    video_id = "dQw4w9WgXcQ"
    
    try:
        response = requests.get(f"{TEMPORAL_BASE}/video-info/{video_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            info = response.json()
            print(f"Video ID: {info['video_id']}")
            print(f"Title: {info['title']}")
            print(f"Duration: {info['duration']} seconds")
            print(f"Author: {info['author']}")
            print(f"Segment Count: {info['segment_count']}")
            print(f"Total Entities: {len(info['total_entities'])}")
            print(f"Entities: {info['total_entities'][:10]}...")  # Show first 10
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Video info failed: {e}")
        return False

def test_search_suggestions():
    """Test search suggestions endpoint"""
    print("\n=== Testing Search Suggestions ===")
    
    query = "artificial"
    
    try:
        response = requests.get(f"{TEMPORAL_BASE}/search-suggestions", params={"query": query})
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            suggestions = response.json()
            print(f"Query: {suggestions['query']}")
            print(f"Suggestions: {suggestions['suggestions']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Search suggestions failed: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    print("\n=== Testing Stats ===")
    
    try:
        response = requests.get(f"{TEMPORAL_BASE}/stats")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print("System Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Stats failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("Temporal Search API Test")
    print("=" * 50)
    
    # Test results
    results = {}
    
    # Run tests
    results['health'] = test_health_check()
    
    if results['health']:
        results['ingestion'] = test_video_ingestion()
        results['temporal_search'] = test_temporal_search()
        results['entity_search'] = test_entity_search()
        results['topic_search'] = test_topic_search()
        results['timeline'] = test_video_timeline()
        results['video_info'] = test_video_info()
        results['suggestions'] = test_search_suggestions()
        results['stats'] = test_stats()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    print(f"\nOverall: {passed_count}/{total_count} tests passed")

if __name__ == "__main__":
    main() 