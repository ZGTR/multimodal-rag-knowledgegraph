from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Tuple
from src.rag.temporal_search import get_temporal_search_service, TemporalSearchQuery, TemporalSearchResult
from src.ingest.youtube import YouTubeVideoSource
from src.bootstrap.logger import get_logger
from src.api.task_tracker import get_task_tracker
import json
import time

router = APIRouter(prefix="/temporal", tags=["temporal-search"])
logger = get_logger("api.temporal")

# Request Models
class VideoIngestRequest(BaseModel):
    video_ids: List[str]
    process_segments: bool = True
    segment_duration: Optional[float] = 30.0

class TemporalSearchRequest(BaseModel):
    query: str
    video_ids: Optional[List[str]] = None
    entity_filter: Optional[str] = None
    topic_filter: Optional[str] = None
    time_range: Optional[Tuple[float, float]] = None
    max_results: int = 10

class EntitySearchRequest(BaseModel):
    entity: str
    video_ids: Optional[List[str]] = None
    max_results: int = 10

class TopicSearchRequest(BaseModel):
    topic: str
    video_ids: Optional[List[str]] = None
    max_results: int = 10

class VideoInfoRequest(BaseModel):
    video_id: str

# Response Models
class VideoIngestResponse(BaseModel):
    status: str
    message: str
    video_id: str
    segments_processed: int
    entities_found: List[str]
    duration: float

class VideoInfoResponse(BaseModel):
    video_id: str
    title: str
    description: str
    duration: float
    author: Optional[str]
    url: str
    thumbnail_url: Optional[str]
    segment_count: int
    total_entities: List[str]

class SearchResponse(BaseModel):
    query: str
    results_count: int
    results: List[TemporalSearchResult]

@router.post("/ingest-video", response_model=VideoIngestResponse)
async def ingest_video(request: VideoIngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a YouTube video with temporal processing
    
    This endpoint processes a YouTube video and extracts:
    - Temporal segments (default 30 seconds each)
    - Named entities from each segment
    - Vector embeddings for semantic search
    - Metadata for knowledge graph storage
    """
    start_time = time.time()
    logger.info(f"Video ingest request received: {len(request.video_ids)} videos")
    logger.info(f"Request parameters: process_segments={request.process_segments}, segment_duration={request.segment_duration}")
    
    try:
        video_source = YouTubeVideoSource()
        
        # Process the first video for immediate response
        video_item = None
        logger.info(f"Processing first video: {request.video_ids[0]}")
        
        for item in video_source.fetch_video([request.video_ids[0]]):
            video_item = item
            break
        
        if not video_item:
            logger.error(f"Video not found or could not be processed: {request.video_ids[0]}")
            raise HTTPException(status_code=404, detail="Video not found or could not be processed")
        
        # Collect all entities from segments
        all_entities = []
        for segment in video_item.segments:
            all_entities.extend(segment.entities)
        all_entities = list(set(all_entities))  # Remove duplicates
        
        logger.info(f"Video processed successfully: {video_item.title}")
        logger.info(f"Found {len(video_item.segments)} segments and {len(all_entities)} unique entities")
        
        # Add background task for processing remaining videos
        if len(request.video_ids) > 1:
            logger.info(f"Adding background task for {len(request.video_ids) - 1} remaining videos")
            
            # Create metadata for tracking
            metadata = {
                "video_ids": request.video_ids[1:],
                "process_segments": request.process_segments,
                "segment_duration": request.segment_duration,
                "request_type": "temporal_video_ingest"
            }
            
            # Add task to tracker
            tracker = get_task_tracker()
            cmd = ["background_video_processing", "--videos"] + request.video_ids[1:]
            task_id = await tracker.add_task(cmd, metadata=metadata)
            
            # Add to FastAPI background tasks
            background_tasks.add_task(process_remaining_videos, request.video_ids[1:], task_id)
            
            logger.info(f"Background task {task_id} queued for remaining videos")
        
        processing_time = time.time() - start_time
        logger.info(f"Video ingestion completed in {processing_time:.2f}s")
        
        return VideoIngestResponse(
            status="success",
            message=f"Video '{video_item.title}' processed successfully",
            video_id=video_item.id,
            segments_processed=len(video_item.segments),
            entities_found=all_entities,
            duration=video_item.duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video ingestion failed: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def temporal_search(request: TemporalSearchRequest):
    """
    Perform temporal search across video content
    
    Search for content in videos with temporal precision, including:
    - Semantic search across video segments
    - Entity and topic filtering
    - Time range filtering
    - Video-specific filtering
    """
    start_time = time.time()
    logger.info(f"Temporal search request received: '{request.query}'")
    logger.info(f"Search parameters: max_results={request.max_results}, video_ids={request.video_ids}")
    
    if request.entity_filter:
        logger.info(f"Entity filter: {request.entity_filter}")
    if request.topic_filter:
        logger.info(f"Topic filter: {request.topic_filter}")
    if request.time_range:
        logger.info(f"Time range: {request.time_range[0]:.1f}s - {request.time_range[1]:.1f}s")
    
    service = get_temporal_search_service()
    if not service:
        logger.error("Temporal search service not available")
        raise HTTPException(status_code=503, detail="Temporal search service not available")
    
    try:
        query = TemporalSearchQuery(
            query=request.query,
            video_ids=request.video_ids,
            entity_filter=request.entity_filter,
            topic_filter=request.topic_filter,
            time_range=request.time_range,
            max_results=request.max_results
        )
        
        results = service.search_entities(query)
        
        search_time = time.time() - start_time
        logger.info(f"Temporal search completed in {search_time:.2f}s")
        logger.info(f"Returning {len(results)} results")
        
        return SearchResponse(
            query=request.query,
            results_count=len(results),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Temporal search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/search-entity", response_model=SearchResponse)
async def search_entity(request: EntitySearchRequest):
    """
    Search for specific entity mentions in videos
    
    Find all occurrences of a specific entity (person, organization, location, etc.)
    with precise timestamps indicating when they appear or are discussed.
    """
    start_time = time.time()
    logger.info(f"Entity search request received: '{request.entity}'")
    logger.info(f"Search parameters: max_results={request.max_results}, video_ids={request.video_ids}")
    
    service = get_temporal_search_service()
    if not service:
        logger.error("Temporal search service not available")
        raise HTTPException(status_code=503, detail="Temporal search service not available")
    
    try:
        results = service.search_by_entity(request.entity, request.video_ids)
        
        search_time = time.time() - start_time
        logger.info(f"Entity search completed in {search_time:.2f}s")
        logger.info(f"Found {len(results)} mentions of '{request.entity}'")
        
        return SearchResponse(
            query=f"entity:{request.entity}",
            results_count=len(results),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Entity search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Entity search failed: {str(e)}")

@router.post("/search-topic", response_model=SearchResponse)
async def search_topic(request: TopicSearchRequest):
    """
    Search for specific topic discussions in videos
    
    Find all segments where specific topics are discussed with precise timestamps.
    """
    start_time = time.time()
    logger.info(f"Topic search request received: '{request.topic}'")
    logger.info(f"Search parameters: max_results={request.max_results}, video_ids={request.video_ids}")
    
    service = get_temporal_search_service()
    if not service:
        logger.error("Temporal search service not available")
        raise HTTPException(status_code=503, detail="Temporal search service not available")
    
    try:
        results = service.search_by_topic(request.topic, request.video_ids)
        
        search_time = time.time() - start_time
        logger.info(f"Topic search completed in {search_time:.2f}s")
        logger.info(f"Found {len(results)} discussions of '{request.topic}'")
        
        return SearchResponse(
            query=f"topic:{request.topic}",
            results_count=len(results),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Topic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Topic search failed: {str(e)}")

@router.get("/video-timeline/{video_id}", response_model=List[TemporalSearchResult])
async def get_video_timeline(video_id: str):
    """
    Get complete timeline of a video with all segments and entities
    
    Returns all temporal segments of a video with their associated entities,
    topics, and timestamps for comprehensive video analysis.
    """
    start_time = time.time()
    logger.info(f"Video timeline request received for: {video_id}")
    
    service = get_temporal_search_service()
    if not service:
        logger.error("Temporal search service not available")
        raise HTTPException(status_code=503, detail="Temporal search service not available")
    
    try:
        timeline = service.get_video_timeline(video_id)
        
        if not timeline:
            logger.warning(f"Video timeline not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video timeline not found")
        
        timeline_time = time.time() - start_time
        logger.info(f"Video timeline retrieved in {timeline_time:.2f}s")
        logger.info(f"Returning {len(timeline)} segments for video {video_id}")
        
        return timeline
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video timeline retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Timeline retrieval failed: {str(e)}")

@router.get("/video-info/{video_id}", response_model=VideoInfoResponse)
async def get_video_info(video_id: str):
    """
    Get comprehensive information about a video
    
    Returns video metadata including title, description, duration,
    segment count, and all entities found across segments.
    """
    start_time = time.time()
    logger.info(f"Video info request received for: {video_id}")
    
    try:
        video_source = YouTubeVideoSource()
        
        # Fetch video info
        logger.info(f"Fetching video info for: {video_id}")
        video_item = None
        for item in video_source.fetch_video([video_id]):
            video_item = item
            break
        
        if not video_item:
            logger.error(f"Video not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Collect all entities from segments
        all_entities = []
        for segment in video_item.segments:
            all_entities.extend(segment.entities)
        all_entities = list(set(all_entities))  # Remove duplicates
        
        info_time = time.time() - start_time
        logger.info(f"Video info retrieved in {info_time:.2f}s")
        logger.info(f"Video: {video_item.title}, {len(video_item.segments)} segments, {len(all_entities)} entities")
        
        return VideoInfoResponse(
            video_id=video_item.id,
            title=video_item.title,
            description=video_item.description,
            duration=video_item.duration,
            author=video_item.author,
            url=str(video_item.url),
            thumbnail_url=video_item.thumbnail_url,
            segment_count=len(video_item.segments),
            total_entities=all_entities
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video info retrieval failed: {str(e)}")

@router.get("/search-suggestions")
async def get_search_suggestions(query: str, max_suggestions: int = 10):
    """
    Get search suggestions based on available entities and topics
    
    Returns suggested search terms based on entities and topics
    found in the ingested videos.
    """
    logger.info(f"Search suggestions request received for: '{query}'")
    logger.info(f"Parameters: max_suggestions={max_suggestions}")
    
    service = get_temporal_search_service()
    if not service:
        logger.error("Temporal search service not available")
        raise HTTPException(status_code=503, detail="Temporal search service not available")
    
    try:
        # This is a placeholder - in a real implementation, you would
        # query the vector store or knowledge graph for suggestions
        suggestions = [
            f"{query} artificial intelligence",
            f"{query} machine learning",
            f"{query} data science",
            f"{query} neural networks",
            f"{query} deep learning"
        ]
        
        logger.info(f"Returning {len(suggestions[:max_suggestions])} suggestions")
        
        return {
            "query": query,
            "suggestions": suggestions[:max_suggestions]
        }
        
    except Exception as e:
        logger.error(f"Search suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search suggestions failed: {str(e)}")

@router.get("/stats")
async def get_temporal_search_stats():
    """
    Get statistics about the temporal search system
    
    Returns metrics about processed videos, segments, entities, and search performance.
    """
    logger.info("Temporal search stats request received")
    
    try:
        # This is a placeholder - in a real implementation, you would
        # query the database for actual statistics
        stats = {
            "total_videos": 0,
            "total_segments": 0,
            "total_entities": 0,
            "total_topics": 0,
            "avg_segments_per_video": 0,
            "avg_entities_per_segment": 0,
            "search_queries_today": 0,
            "most_searched_entities": [],
            "most_searched_topics": []
        }
        
        logger.info("Returning temporal search statistics")
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

# Helper function for background processing
async def process_remaining_videos(video_ids: List[str], task_id: str):
    """Process remaining videos in the background with task tracking"""
    tracker = get_task_tracker()
    
    try:
        # Mark task as started
        await tracker.start_task(task_id)
        await tracker.update_progress(task_id, f"Starting background processing for {len(video_ids)} videos")
        
        logger.info(f"Background processing started for {len(video_ids)} videos")
        start_time = time.time()
        
        video_source = YouTubeVideoSource()
        for i, video_item in enumerate(video_source.fetch_video(video_ids), 1):
            progress_msg = f"Processing video {i}/{len(video_ids)}: {video_item.id}"
            await tracker.update_progress(task_id, progress_msg)
            logger.info(f"Background processed video {i}/{len(video_ids)}: {video_item.id}")
        
        background_time = time.time() - start_time
        completion_msg = f"Background video processing completed in {background_time:.2f}s"
        await tracker.update_progress(task_id, completion_msg)
        await tracker.complete_task(task_id, success=True)
        logger.info(f"Background video processing completed in {background_time:.2f}s")
        
    except Exception as e:
        error_msg = f"Background video processing failed: {e}"
        await tracker.update_progress(task_id, error_msg)
        await tracker.complete_task(task_id, success=False, error_message=error_msg)
        logger.error(f"Background video processing failed: {e}") 