#!/usr/bin/env python3
"""
Test script to demonstrate enhanced logging during video processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest.youtube import YouTubeVideoSource
from src.rag.temporal_search import get_temporal_search_service, TemporalSearchQuery
from src.bootstrap.logger import get_logger
import time

logger = get_logger("test_logging")

def test_video_ingestion_logging():
    """Test video ingestion with detailed logging"""
    print("=== Testing Video Ingestion Logging ===")
    
    # Example YouTube video ID
    video_id = "dQw4w9WgXcQ"
    
    print(f"Starting video ingestion for: {video_id}")
    
    try:
        # Create video source
        video_source = YouTubeVideoSource()
        
        # Fetch video content
        for video_item in video_source.fetch_video([video_id]):
            print(f"\n✅ Video processed successfully!")
            print(f"   Title: {video_item.title}")
            print(f"   Duration: {video_item.duration:.1f}s")
            print(f"   Segments: {len(video_item.segments)}")
            
            # Show entity summary
            all_entities = []
            for segment in video_item.segments:
                all_entities.extend(segment.entities)
            unique_entities = list(set(all_entities))
            print(f"   Unique entities found: {len(unique_entities)}")
            if unique_entities:
                print(f"   Entities: {', '.join(unique_entities[:10])}...")
            
            break  # Just process first video for demo
        
    except Exception as e:
        print(f"❌ Error during video ingestion: {e}")
        logger.error(f"Video ingestion failed: {e}")

def test_temporal_search_logging():
    """Test temporal search with detailed logging"""
    print("\n=== Testing Temporal Search Logging ===")
    
    service = get_temporal_search_service()
    if not service:
        print("❌ Temporal search service not available")
        return
    
    # Example search query
    query = "artificial intelligence"
    print(f"Searching for: '{query}'")
    
    try:
        # Perform temporal search
        temporal_query = TemporalSearchQuery(
            query=query,
            max_results=5
        )
        
        results = service.search_entities(temporal_query)
        
        print(f"\n✅ Search completed!")
        print(f"   Results found: {len(results)}")
        
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. Video: {result.video_id}")
            print(f"      Time: {result.start_time:.1f}s - {result.end_time:.1f}s")
            print(f"      Entities: {result.entities}")
            print()
            
    except Exception as e:
        print(f"❌ Error during search: {e}")
        logger.error(f"Search failed: {e}")

def test_entity_search_logging():
    """Test entity search with detailed logging"""
    print("\n=== Testing Entity Search Logging ===")
    
    service = get_temporal_search_service()
    if not service:
        print("❌ Temporal search service not available")
        return
    
    # Example entity
    entity = "Elon Musk"
    print(f"Searching for entity: '{entity}'")
    
    try:
        results = service.search_by_entity(entity, max_results=3)
        
        print(f"\n✅ Entity search completed!")
        print(f"   Mentions found: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. Video: {result.video_id}")
            print(f"      Time: {result.start_time:.1f}s - {result.end_time:.1f}s")
            print(f"      Context: {result.matched_text[:100]}...")
            print()
            
    except Exception as e:
        print(f"❌ Error during entity search: {e}")
        logger.error(f"Entity search failed: {e}")

def test_video_timeline_logging():
    """Test video timeline with detailed logging"""
    print("\n=== Testing Video Timeline Logging ===")
    
    service = get_temporal_search_service()
    if not service:
        print("❌ Temporal search service not available")
        return
    
    # Example video ID
    video_id = "dQw4w9WgXcQ"
    print(f"Getting timeline for video: {video_id}")
    
    try:
        timeline = service.get_video_timeline(video_id)
        
        print(f"\n✅ Timeline retrieved!")
        print(f"   Segments: {len(timeline)}")
        
        if timeline:
            total_duration = timeline[-1].end_time
            print(f"   Duration: {total_duration:.1f}s")
            
            # Show first few segments
            for i, segment in enumerate(timeline[:5], 1):
                print(f"   {i}. {segment.start_time:.1f}s - {segment.end_time:.1f}s")
                if segment.entities:
                    print(f"      Entities: {', '.join(segment.entities)}")
                print()
            
            if len(timeline) > 5:
                print(f"   ... and {len(timeline) - 5} more segments")
        else:
            print("   No timeline data available")
            
    except Exception as e:
        print(f"❌ Error getting video timeline: {e}")
        logger.error(f"Timeline retrieval failed: {e}")

def main():
    """Run all logging tests"""
    print("Enhanced Logging Test")
    print("=" * 50)
    print("This test demonstrates the detailed logging that occurs during:")
    print("- Video ingestion and processing")
    print("- Entity extraction")
    print("- Temporal search operations")
    print("- Vector store operations")
    print()
    print("Watch the terminal output for detailed progress logs!")
    print()
    
    # Run tests
    test_video_ingestion_logging()
    test_temporal_search_logging()
    test_entity_search_logging()
    test_video_timeline_logging()
    
    print("\n" + "=" * 50)
    print("Logging test completed!")
    print("Check the terminal output above for detailed logging information.")

if __name__ == "__main__":
    main() 