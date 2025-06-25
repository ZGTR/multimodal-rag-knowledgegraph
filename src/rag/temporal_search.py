from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from datetime import datetime
from src.rag.vector_store import get_vectorstore
from src.bootstrap.logger import get_logger
import json
import time

logger = get_logger("temporal_search")

class TemporalSearchResult(BaseModel):
    """Result of a temporal search query"""
    video_id: str
    video_title: str
    video_url: str
    start_time: float
    end_time: float
    matched_text: str
    entities: List[str]
    topics: List[str]
    confidence: float
    segment_id: str

class TemporalSearchQuery(BaseModel):
    """Query for temporal search"""
    query: str
    video_ids: Optional[List[str]] = None  # If None, search all videos
    entity_filter: Optional[str] = None    # Specific entity to search for
    topic_filter: Optional[str] = None     # Specific topic to search for
    time_range: Optional[Tuple[float, float]] = None  # Time range in seconds
    max_results: int = 10

class TemporalSearchService:
    """Service for searching video content with temporal precision"""
    
    def __init__(self):
        logger.info("Initializing TemporalSearchService")
        self.vectorstore = get_vectorstore()
        if self.vectorstore:
            logger.info("TemporalSearchService initialized with vector store")
        else:
            logger.warning("TemporalSearchService initialized without vector store")
    
    def search_entities(self, query: TemporalSearchQuery) -> List[TemporalSearchResult]:
        """Search for specific entities in video content"""
        start_time = time.time()
        logger.info(f"Starting temporal search: '{query.query}'")
        logger.info(f"Search parameters: max_results={query.max_results}, video_ids={query.video_ids}")
        
        if query.entity_filter:
            logger.info(f"Entity filter: {query.entity_filter}")
        if query.topic_filter:
            logger.info(f"Topic filter: {query.topic_filter}")
        if query.time_range:
            logger.info(f"Time range: {query.time_range[0]:.1f}s - {query.time_range[1]:.1f}s")
        
        if not self.vectorstore:
            logger.error("Vector store not available for temporal search")
            return []
        
        try:
            # Search vector store for relevant segments
            search_query = query.query
            if query.entity_filter:
                search_query += f" {query.entity_filter}"
            if query.topic_filter:
                search_query += f" {query.topic_filter}"
            
            logger.info(f"Executing vector search with query: '{search_query}'")
            
            # Get search results
            results = self.vectorstore.search(search_query, k=query.max_results * 2)  # Get more to filter
            logger.info(f"Vector search returned {len(results)} initial results")
            
            # Filter and process results
            temporal_results = []
            filtered_count = 0
            seen_segments = set()  # Track seen segments to avoid duplicates
            
            for i, doc in enumerate(results):
                metadata = doc.metadata
                
                # Skip if not a video segment
                if metadata.get("segment_type") != "video_segment":
                    logger.debug(f"Skipping non-video segment: {metadata.get('segment_type', 'unknown')}")
                    continue
                
                # Apply video filter
                if query.video_ids and metadata.get("video_id") not in query.video_ids:
                    logger.debug(f"Filtering out video {metadata.get('video_id')} (not in requested list)")
                    filtered_count += 1
                    continue
                
                # Apply time range filter
                if query.time_range:
                    start_time_segment = metadata.get("start_time", 0)
                    if not (query.time_range[0] <= start_time_segment <= query.time_range[1]):
                        logger.debug(f"Filtering out segment at {start_time_segment:.1f}s (outside time range)")
                        filtered_count += 1
                        continue
                
                # Apply entity filter
                if query.entity_filter:
                    entities = metadata.get("entities", [])
                    if query.entity_filter.lower() not in [e.lower() for e in entities]:
                        logger.debug(f"Filtering out segment (entity '{query.entity_filter}' not found)")
                        filtered_count += 1
                        continue
                
                # Check for duplicates based on video_id, start_time, and end_time
                video_id = metadata.get("video_id", "")
                start_time = metadata.get("start_time", 0)
                end_time = metadata.get("end_time", 0)
                segment_key = (video_id, start_time, end_time)
                
                if segment_key in seen_segments:
                    logger.debug(f"Filtering out duplicate segment: {video_id} at {start_time:.1f}s - {end_time:.1f}s")
                    filtered_count += 1
                    continue
                
                seen_segments.add(segment_key)
                
                # Create temporal result
                result = TemporalSearchResult(
                    video_id=video_id,
                    video_title=metadata.get("video_title", ""),
                    video_url=f"https://youtu.be/{video_id}",
                    start_time=start_time,
                    end_time=end_time,
                    matched_text=doc.page_content,
                    entities=metadata.get("entities", []),
                    topics=metadata.get("topics", []),
                    confidence=1.0,  # Could be enhanced with actual confidence scores
                    segment_id=doc.metadata.get("doc_id", "")
                )
                
                temporal_results.append(result)
                logger.debug(f"Added result {len(temporal_results)}: {result.video_id} at {result.start_time:.1f}s")
            
            # Sort by relevance and limit results
            temporal_results = sorted(temporal_results, key=lambda x: x.confidence, reverse=True)
            final_results = temporal_results[:query.max_results]
            
            search_time = time.time() - start_time
            logger.info(f"Temporal search completed in {search_time:.2f}s")
            logger.info(f"Results: {len(final_results)}/{len(temporal_results)} (filtered out {filtered_count} total, including duplicates)")
            
            # Log summary of results
            if final_results:
                video_ids_found = list(set(r.video_id for r in final_results))
                logger.info(f"Found results in {len(video_ids_found)} videos: {video_ids_found}")
                
                # Log time ranges
                time_ranges = [(r.start_time, r.end_time) for r in final_results]
                logger.info(f"Time ranges: {time_ranges[:3]}..." if len(time_ranges) > 3 else f"Time ranges: {time_ranges}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Failed to perform temporal search: {e}")
            return []
    
    def search_by_entity(self, entity: str, video_ids: Optional[List[str]] = None, max_results: int = 10) -> List[TemporalSearchResult]:
        """Search for specific entity mentions across videos"""
        logger.info(f"Searching for entity: '{entity}'")
        if video_ids:
            logger.info(f"Filtering to videos: {video_ids}")
        
        query = TemporalSearchQuery(
            query=entity,
            video_ids=video_ids,
            entity_filter=entity,
            max_results=max_results
        )
        return self.search_entities(query)
    
    def search_by_topic(self, topic: str, video_ids: Optional[List[str]] = None, max_results: int = 10) -> List[TemporalSearchResult]:
        """Search for specific topic discussions across videos"""
        logger.info(f"Searching for topic: '{topic}'")
        if video_ids:
            logger.info(f"Filtering to videos: {video_ids}")
        
        query = TemporalSearchQuery(
            query=topic,
            video_ids=video_ids,
            topic_filter=topic,
            max_results=max_results
        )
        return self.search_entities(query)
    
    def get_video_timeline(self, video_id: str) -> List[TemporalSearchResult]:
        """Get all segments of a video with their entities and topics"""
        logger.info(f"Getting timeline for video: {video_id}")
        start_time = time.time()
        
        if not self.vectorstore:
            logger.error("Vector store not available for timeline retrieval")
            return []
        
        try:
            # Search for all segments of this video
            logger.info(f"Searching for all segments of video {video_id}")
            results = self.vectorstore.search("", k=1000)  # Get all segments
            
            timeline = []
            seen_segments = set()  # Track seen segments to avoid duplicates
            
            for doc in results:
                metadata = doc.metadata
                if (metadata.get("segment_type") == "video_segment" and 
                    metadata.get("video_id") == video_id):
                    
                    # Check for duplicates based on start_time and end_time
                    start_time = metadata.get("start_time", 0)
                    end_time = metadata.get("end_time", 0)
                    segment_key = (video_id, start_time, end_time)
                    
                    if segment_key in seen_segments:
                        logger.debug(f"Filtering out duplicate segment: {video_id} at {start_time:.1f}s - {end_time:.1f}s")
                        continue
                    
                    seen_segments.add(segment_key)
                    
                    result = TemporalSearchResult(
                        video_id=video_id,
                        video_title=metadata.get("video_title", ""),
                        video_url=f"https://youtu.be/{video_id}",
                        start_time=start_time,
                        end_time=end_time,
                        matched_text=doc.page_content,
                        entities=metadata.get("entities", []),
                        topics=metadata.get("topics", []),
                        confidence=1.0,
                        segment_id=doc.metadata.get("doc_id", "")
                    )
                    timeline.append(result)
            
            # Sort by start time
            timeline.sort(key=lambda x: x.start_time)
            
            timeline_time = time.time() - start_time
            logger.info(f"Timeline retrieval completed in {timeline_time:.2f}s")
            logger.info(f"Found {len(timeline)} segments for video {video_id} (duplicates filtered out)")
            
            if timeline:
                total_duration = timeline[-1].end_time
                logger.info(f"Video duration: {total_duration:.1f}s")
                
                # Log entity statistics
                all_entities = []
                for segment in timeline:
                    all_entities.extend(segment.entities)
                unique_entities = list(set(all_entities))
                logger.info(f"Total unique entities found: {len(unique_entities)}")
                if unique_entities:
                    logger.info(f"Entities: {unique_entities[:10]}..." if len(unique_entities) > 10 else f"Entities: {unique_entities}")
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get video timeline: {e}")
            return []

def get_temporal_search_service() -> Optional[TemporalSearchService]:
    """Get temporal search service instance"""
    try:
        logger.info("Creating temporal search service instance")
        service = TemporalSearchService()
        if service.vectorstore is None:
            logger.error("Vector store not properly initialized for temporal search")
            return None
        logger.info("Temporal search service created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create temporal search service: {e}")
        return None 