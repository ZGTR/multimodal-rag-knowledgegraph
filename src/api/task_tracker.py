import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from src.bootstrap.logger import get_logger

logger = get_logger("task_tracker")

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    task_id: str
    command: List[str]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskTracker:
    """Track background tasks and their status"""
    
    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}
        self._lock = asyncio.Lock()
    
    async def add_task(self, command: List[str], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a new task to tracking"""
        async with self._lock:
            task_id = str(uuid.uuid4())
            task_info = TaskInfo(
                task_id=task_id,
                command=command,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            self._tasks[task_id] = task_info
            logger.info(f"Added task {task_id} to tracking: {command}")
            return task_id
    
    async def start_task(self, task_id: str) -> bool:
        """Mark a task as started"""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            logger.info(f"Task {task_id} started")
            return True
    
    async def complete_task(self, task_id: str, success: bool = True, error_message: Optional[str] = None) -> bool:
        """Mark a task as completed or failed"""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            task.completed_at = datetime.now()
            
            if success:
                task.status = TaskStatus.COMPLETED
                logger.info(f"Task {task_id} completed successfully")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = error_message
                logger.error(f"Task {task_id} failed: {error_message}")
            
            return True
    
    async def update_progress(self, task_id: str, progress: str) -> bool:
        """Update task progress"""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            task.progress = progress
            return True
    
    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information by ID"""
        async with self._lock:
            return self._tasks.get(task_id)
    
    async def get_all_tasks(self, include_completed: bool = True, limit: Optional[int] = None) -> List[TaskInfo]:
        """Get all tasks, optionally filtering by completion status"""
        async with self._lock:
            tasks = list(self._tasks.values())
            
            if not include_completed:
                tasks = [t for t in tasks if t.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]]
            
            # Sort by creation time (newest first)
            tasks.sort(key=lambda x: x.created_at, reverse=True)
            
            if limit:
                tasks = tasks[:limit]
            
            return tasks
    
    async def get_running_tasks(self) -> List[TaskInfo]:
        """Get all currently running tasks"""
        async with self._lock:
            return [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]
    
    async def get_pending_tasks(self) -> List[TaskInfo]:
        """Get all pending tasks"""
        async with self._lock:
            return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
    
    async def cleanup_old_tasks(self, days: int = 7) -> int:
        """Remove old completed/failed tasks"""
        cutoff_date = datetime.now() - timedelta(days=days)
        async with self._lock:
            old_tasks = [
                task_id for task_id, task in self._tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and task.completed_at < cutoff_date
            ]
            
            for task_id in old_tasks:
                del self._tasks[task_id]
            
            logger.info(f"Cleaned up {len(old_tasks)} old tasks")
            return len(old_tasks)
    
    async def get_task_stats(self) -> Dict[str, Any]:
        """Get task statistics"""
        async with self._lock:
            total_tasks = len(self._tasks)
            running_tasks = len([t for t in self._tasks.values() if t.status == TaskStatus.RUNNING])
            pending_tasks = len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING])
            completed_tasks = len([t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED])
            failed_tasks = len([t for t in self._tasks.values() if t.status == TaskStatus.FAILED])
            
            return {
                "total_tasks": total_tasks,
                "running_tasks": running_tasks,
                "pending_tasks": pending_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            }

# Global task tracker instance
task_tracker = TaskTracker()

def get_task_tracker() -> TaskTracker:
    """Get the global task tracker instance"""
    return task_tracker 