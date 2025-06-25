from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import subprocess, sys
from src.bootstrap.logger import get_logger
from src.api.task_tracker import get_task_tracker
import asyncio

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

async def run_ingest_worker(cmd: list[str], task_id: str):
    """Run the ingest worker and track its progress"""
    tracker = get_task_tracker()
    
    try:
        # Mark task as started
        await tracker.start_task(task_id)
        await tracker.update_progress(task_id, "Starting ingest worker...")
        
        logger.info(f"Starting background task {task_id}: {cmd}")
        
        # Run the subprocess
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
    
    # Build command
    cmd = [sys.executable, "-m", "src.worker.ingest_worker"]
    if req.videos:
        cmd += ["--videos"] + req.videos
    if req.twitter:
        cmd += ["--twitter"] + req.twitter
    if req.ig:
        cmd += ["--ig"] + req.ig
    
    # Create metadata for tracking
    metadata = {
        "videos": req.videos,
        "twitter": req.twitter,
        "ig": req.ig,
        "request_type": "ingest"
    }
    
    # Add task to tracker
    tracker = get_task_tracker()
    task_id = await tracker.add_task(cmd, metadata=metadata)
    
    logger.info(f"Queuing background task {task_id}: {cmd}")
    
    # Add to FastAPI background tasks
    bg.add_task(run_ingest_worker, cmd, task_id)
    
    return IngestResponse(
        status="queued",
        task_id=task_id,
        cmd=cmd,
        message=f"Background task queued with ID: {task_id}"
    ) 