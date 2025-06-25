from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.api.task_tracker import get_task_tracker, TaskStatus, TaskInfo
from src.bootstrap.logger import get_logger

router = APIRouter(prefix="/tasks", tags=["task-monitoring"])
logger = get_logger("api.tasks")

# Response Models
class TaskStatusResponse(BaseModel):
    task_id: str
    command: List[str]
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskStatsResponse(BaseModel):
    total_tasks: int
    running_tasks: int
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float

class TaskListResponse(BaseModel):
    tasks: List[TaskStatusResponse]
    total_count: int

@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_stats():
    """
    Get overall task statistics
    
    Returns:
    - total_tasks: Total number of tasks tracked
    - running_tasks: Number of currently running tasks
    - pending_tasks: Number of pending tasks
    - completed_tasks: Number of completed tasks
    - failed_tasks: Number of failed tasks
    - success_rate: Percentage of successful tasks
    """
    logger.info("Task stats request received")
    
    try:
        tracker = get_task_tracker()
        stats = await tracker.get_task_stats()
        
        logger.info(f"Task stats: {stats}")
        return TaskStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task stats: {str(e)}")

@router.get("/running", response_model=TaskListResponse)
async def get_running_tasks():
    """
    Get all currently running background tasks
    
    Returns a list of tasks that are currently being executed.
    """
    logger.info("Running tasks request received")
    
    try:
        tracker = get_task_tracker()
        tasks = await tracker.get_running_tasks()
        
        task_responses = [
            TaskStatusResponse(
                task_id=task.task_id,
                command=task.command,
                status=task.status.value,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                error_message=task.error_message,
                progress=task.progress,
                metadata=task.metadata
            )
            for task in tasks
        ]
        
        logger.info(f"Found {len(tasks)} running tasks")
        return TaskListResponse(tasks=task_responses, total_count=len(tasks))
        
    except Exception as e:
        logger.error(f"Failed to get running tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get running tasks: {str(e)}")

@router.get("/pending", response_model=TaskListResponse)
async def get_pending_tasks():
    """
    Get all pending background tasks
    
    Returns a list of tasks that are queued but not yet started.
    """
    logger.info("Pending tasks request received")
    
    try:
        tracker = get_task_tracker()
        tasks = await tracker.get_pending_tasks()
        
        task_responses = [
            TaskStatusResponse(
                task_id=task.task_id,
                command=task.command,
                status=task.status.value,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                error_message=task.error_message,
                progress=task.progress,
                metadata=task.metadata
            )
            for task in tasks
        ]
        
        logger.info(f"Found {len(tasks)} pending tasks")
        return TaskListResponse(tasks=task_responses, total_count=len(tasks))
        
    except Exception as e:
        logger.error(f"Failed to get pending tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending tasks: {str(e)}")

@router.get("/all", response_model=TaskListResponse)
async def get_all_tasks(include_completed: bool = True, limit: Optional[int] = 50):
    """
    Get all background tasks
    
    Args:
    - include_completed: Whether to include completed and failed tasks
    - limit: Maximum number of tasks to return (default: 50)
    
    Returns a list of all tracked tasks, sorted by creation time (newest first).
    """
    logger.info(f"All tasks request received: include_completed={include_completed}, limit={limit}")
    
    try:
        tracker = get_task_tracker()
        tasks = await tracker.get_all_tasks(include_completed=include_completed, limit=limit)
        
        task_responses = [
            TaskStatusResponse(
                task_id=task.task_id,
                command=task.command,
                status=task.status.value,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                error_message=task.error_message,
                progress=task.progress,
                metadata=task.metadata
            )
            for task in tasks
        ]
        
        logger.info(f"Found {len(tasks)} tasks")
        return TaskListResponse(tasks=task_responses, total_count=len(tasks))
        
    except Exception as e:
        logger.error(f"Failed to get all tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get all tasks: {str(e)}")

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of a specific background task
    
    Args:
    - task_id: The unique identifier of the task
    
    Returns detailed information about the specified task.
    """
    logger.info(f"Task status request received for task: {task_id}")
    
    try:
        tracker = get_task_tracker()
        task = await tracker.get_task(task_id)
        
        if not task:
            logger.warning(f"Task not found: {task_id}")
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        
        task_response = TaskStatusResponse(
            task_id=task.task_id,
            command=task.command,
            status=task.status.value,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message,
            progress=task.progress,
            metadata=task.metadata
        )
        
        logger.info(f"Task {task_id} status: {task.status.value}")
        return task_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.get("/count/running")
async def get_running_task_count():
    """
    Get the count of currently running background tasks
    
    Returns a simple count of tasks that are currently being executed.
    """
    logger.info("Running task count request received")
    
    try:
        tracker = get_task_tracker()
        running_tasks = await tracker.get_running_tasks()
        count = len(running_tasks)
        
        logger.info(f"Running task count: {count}")
        return {"running_tasks": count}
        
    except Exception as e:
        logger.error(f"Failed to get running task count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get running task count: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_tasks(days: int = 7):
    """
    Clean up old completed and failed tasks
    
    Args:
    - days: Remove tasks older than this many days (default: 7)
    
    Returns the number of tasks that were cleaned up.
    """
    logger.info(f"Task cleanup request received: days={days}")
    
    try:
        tracker = get_task_tracker()
        cleaned_count = await tracker.cleanup_old_tasks(days=days)
        
        logger.info(f"Cleaned up {cleaned_count} old tasks")
        return {"cleaned_tasks": cleaned_count, "days": days}
        
    except Exception as e:
        logger.error(f"Failed to cleanup old tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old tasks: {str(e)}") 