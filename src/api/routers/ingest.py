from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import subprocess, sys
from src.bootstrap.logger import get_logger
from src.api.task_tracker import get_task_tracker
from src.ingest.youtube import YouTubeVideoSource
from src.worker.strategies.youtube import YouTubeIngestStrategy
from src.rag.vector_store import get_vectorstore
from src.kg.gremlin_client import GremlinKG
import asyncio
import time
from typing import List, Optional, Dict, Any

router = APIRouter()
logger = get_logger("api.ingest")

class IngestRequest(BaseModel):
    videos: list[str] | None = None
    twitter: list[str] | None = None
    ig: list[str] | None = None
    process_segments: bool = True
    segment_duration: Optional[float] = 30.0

class IngestResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None
    cmd: Optional[list[str]] = None
    video_id: Optional[str] = None
    segments_processed: Optional[int] = None
    entities_found: Optional[List[str]] = None
    duration: Optional[float] = None

async def run_ingest_worker(cmd: list[str], task_id: str):
    """Run the ingest worker and track its progress"""
    tracker = get_task_tracker()
    try:
        await tracker.start_task(task_id)
        await tracker.update_progress(task_id, "Starting ingest worker...")
        logger.info(f"Starting background task {task_id}: {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            await tracker.update_progress(task_id, "Task completed successfully")
            await tracker.complete_task(task_id, success=True)
            logger.info(f"Background task {task_id} completed successfully")
        else:
            error_msg = f"Task failed with return code {result.returncode}: {result.stderr}"
            await tracker.update_progress(task_id, f"Task failed: {error_msg}")
            await tracker.complete_task(task_id, success=False, error_message=error_msg)
            logger.error(f"Background task {task_id} failed: {error_msg}")
    except Exception as e:
        error_msg = f"Task execution failed: {str(e)}"
        await tracker.update_progress(task_id, f"Task execution error: {error_msg}")
        await tracker.complete_task(task_id, success=False, error_message=error_msg)
        logger.error(f"Background task {task_id} execution failed: {e}")

def process_videos_background(video_ids: List[str], task_id: str, process_segments: bool, segment_duration: float):
    """Process all videos in background using YouTube ingestion strategy"""
    tracker = get_task_tracker()
    try:
        asyncio.run(tracker.start_task(task_id))
        asyncio.run(tracker.update_progress(task_id, f"Starting background processing for {len(video_ids)} videos"))
        logger.info(f"Background processing started for {len(video_ids)} videos")
        
        start_time = time.time()
        
        # Initialize vector store and knowledge graph
        vectordb = get_vectorstore()
        kg = GremlinKG()
        
        # Use YouTube ingestion strategy to process videos
        strategy = YouTubeIngestStrategy(vectordb=vectordb, kg=kg)
        
        for i, video_id in enumerate(video_ids, 1):
            progress_msg = f"Processing video {i}/{len(video_ids)}: {video_id}"
            asyncio.run(tracker.update_progress(task_id, progress_msg))
            logger.info(f"Background processing video {i}/{len(video_ids)}: {video_id}")
            
            # Process single video
            strategy.ingest([video_id])
        
        background_time = time.time() - start_time
        completion_msg = f"Background video processing completed in {background_time:.2f}s"
        asyncio.run(tracker.update_progress(task_id, completion_msg))
        asyncio.run(tracker.complete_task(task_id, success=True))
        logger.info(f"Background video processing completed in {background_time:.2f}s")
        
    except Exception as e:
        error_msg = f"Background video processing failed: {e}"
        asyncio.run(tracker.update_progress(task_id, error_msg))
        asyncio.run(tracker.complete_task(task_id, success=False, error_message=error_msg))
        logger.error(f"Background video processing failed: {e}")

async def process_video_ingestion(videos: List[str], process_segments: bool, segment_duration: float, bg: BackgroundTasks) -> IngestResponse:
    """Handle video ingestion with background processing for all videos"""
    logger.info(f"Queuing {len(videos)} videos for background processing")
    
    metadata = {
        "video_ids": videos,
        "process_segments": process_segments,
        "segment_duration": segment_duration,
        "request_type": "temporal_video_ingest"
    }
    
    tracker = get_task_tracker()
    cmd = ["background_video_processing", "--videos"] + videos
    task_id = await tracker.add_task(cmd, metadata=metadata)
    
    bg.add_task(process_videos_background, videos, task_id, process_segments, segment_duration)
    logger.info(f"Background task {task_id} queued for {len(videos)} videos")
    
    return IngestResponse(
        status="queued",
        message=f"Background task queued for {len(videos)} videos with ID: {task_id}",
        task_id=task_id,
        cmd=cmd
    )

async def process_generic_ingestion(req: IngestRequest, bg: BackgroundTasks) -> IngestResponse:
    """Handle generic ingestion (Twitter, IG, etc.)"""
    cmd = [sys.executable, "-m", "src.worker.ingest_worker"]
    if req.videos:
        cmd += ["--videos"] + req.videos
    if req.twitter:
        cmd += ["--twitter"] + req.twitter
    if req.ig:
        cmd += ["--ig"] + req.ig
    
    metadata = {
        "videos": req.videos,
        "twitter": req.twitter,
        "ig": req.ig,
        "request_type": "ingest"
    }
    
    tracker = get_task_tracker()
    task_id = await tracker.add_task(cmd, metadata=metadata)
    logger.info(f"Queuing background task {task_id}: {cmd}")
    bg.add_task(run_ingest_worker, cmd, task_id)
    
    return IngestResponse(
        status="queued",
        message=f"Background task queued with ID: {task_id}",
        task_id=task_id,
        cmd=cmd
    )

@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest, bg: BackgroundTasks):
    """Unified ingestion endpoint for videos, Twitter, and Instagram"""
    logger.info(f"Received ingest request: {req}")
    
    # If videos are provided, do temporal video processing in background
    if req.videos:
        return await process_video_ingestion(req.videos, req.process_segments, req.segment_duration, bg)
    
    # Otherwise, handle Twitter/IG ingestion
    return await process_generic_ingestion(req, bg) 