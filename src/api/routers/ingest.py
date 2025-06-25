from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import subprocess, sys
from src.bootstrap.logger import get_logger
from src.api.task_tracker import get_task_tracker
from src.ingest.youtube import YouTubeVideoSource
import asyncio
import time
from typing import List, Optional

router = APIRouter()
logger = get_logger("api.ingest")

class IngestRequest(BaseModel):
    videos: list[str] | None = None
    twitter: list[str] | None = None
    ig: list[str] | None = None

class IngestResponse(BaseModel):
    status: str
    task_id: str
    cmd: list[str]
    message: str

class VideoIngestRequest(BaseModel):
    video_ids: List[str]
    process_segments: bool = True
    segment_duration: Optional[float] = 30.0

class VideoIngestResponse(BaseModel):
    status: str
    message: str
    video_id: str
    segments_processed: int
    entities_found: List[str]
    duration: float

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

@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest, bg: BackgroundTasks):
    logger.info(f"Received ingest request: {req}")
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
        task_id=task_id,
        cmd=cmd,
        message=f"Background task queued with ID: {task_id}"
    )

@router.post("/ingest/video", response_model=VideoIngestResponse)
async def ingest_video(request: VideoIngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a YouTube video with temporal processing (segments, entities, etc.)
    """
    start_time = time.time()
    logger.info(f"Video ingest request received: {len(request.video_ids)} videos")
    logger.info(f"Request parameters: process_segments={request.process_segments}, segment_duration={request.segment_duration}")
    try:
        video_source = YouTubeVideoSource()
        video_item = None
        logger.info(f"Processing first video: {request.video_ids[0]}")
        for item in video_source.fetch_video([request.video_ids[0]]):
            video_item = item
            break
        if not video_item:
            logger.error(f"Video not found or could not be processed: {request.video_ids[0]}")
            raise HTTPException(status_code=404, detail="Video not found or could not be processed")
        all_entities = []
        for segment in video_item.segments:
            all_entities.extend(segment.entities)
        all_entities = list(set(all_entities))
        logger.info(f"Video processed successfully: {video_item.title}")
        logger.info(f"Found {len(video_item.segments)} segments and {len(all_entities)} unique entities")
        if len(request.video_ids) > 1:
            logger.info(f"Adding background task for {len(request.video_ids) - 1} remaining videos")
            metadata = {
                "video_ids": request.video_ids[1:],
                "process_segments": request.process_segments,
                "segment_duration": request.segment_duration,
                "request_type": "temporal_video_ingest"
            }
            tracker = get_task_tracker()
            cmd = ["background_video_processing", "--videos"] + request.video_ids[1:]
            task_id = await tracker.add_task(cmd, metadata=metadata)
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

def process_remaining_videos(video_ids: List[str], task_id: str):
    """Process remaining videos in the background with task tracking"""
    tracker = get_task_tracker()
    try:
        asyncio.run(tracker.start_task(task_id))
        asyncio.run(tracker.update_progress(task_id, f"Starting background processing for {len(video_ids)} videos"))
        logger.info(f"Background processing started for {len(video_ids)} videos")
        start_time = time.time()
        video_source = YouTubeVideoSource()
        for i, video_item in enumerate(video_source.fetch_video(video_ids), 1):
            progress_msg = f"Processing video {i}/{len(video_ids)}: {video_item.id}"
            asyncio.run(tracker.update_progress(task_id, progress_msg))
            logger.info(f"Background processed video {i}/{len(video_ids)}: {video_item.id}")
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