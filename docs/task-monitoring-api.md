# Task Monitoring API

The Task Monitoring API provides comprehensive tracking and monitoring capabilities for background tasks in the Multimodal RAG Knowledge Graph system.

## Overview

The task monitoring system tracks all background tasks including:
- Video ingestion tasks
- Temporal video processing
- Data processing operations
- Any other background operations

## API Endpoints

### Task Statistics

#### GET `/tasks/stats`

Get overall task statistics including counts and success rates.

**Response:**
```json
{
  "total_tasks": 15,
  "running_tasks": 2,
  "pending_tasks": 1,
  "completed_tasks": 10,
  "failed_tasks": 2,
  "success_rate": 83.33
}
```

### Task Lists

#### GET `/tasks/running`

Get all currently running background tasks.

**Response:**
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "command": ["python", "-m", "src.worker.ingest_worker", "--videos", "dQw4w9WgXcQ"],
      "status": "running",
      "created_at": "2024-01-15T10:30:15",
      "started_at": "2024-01-15T10:30:16",
      "completed_at": null,
      "error_message": null,
      "progress": "Processing video segments...",
      "metadata": {
        "videos": ["dQw4w9WgXcQ"],
        "request_type": "ingest"
      }
    }
  ],
  "total_count": 1
}
```

#### GET `/tasks/pending`

Get all pending background tasks.

**Response:**
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440001",
      "command": ["background_video_processing", "--videos", "9bZkp7q19f0"],
      "status": "pending",
      "created_at": "2024-01-15T10:35:20",
      "started_at": null,
      "completed_at": null,
      "error_message": null,
      "progress": null,
      "metadata": {
        "video_ids": ["9bZkp7q19f0"],
        "request_type": "temporal_video_ingest"
      }
    }
  ],
  "total_count": 1
}
```

#### GET `/tasks/all`

Get all background tasks with optional filtering.

**Query Parameters:**
- `include_completed` (boolean, default: true): Include completed and failed tasks
- `limit` (integer, default: 50): Maximum number of tasks to return

**Response:**
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "command": ["python", "-m", "src.worker.ingest_worker", "--videos", "dQw4w9WgXcQ"],
      "status": "completed",
      "created_at": "2024-01-15T10:30:15",
      "started_at": "2024-01-15T10:30:16",
      "completed_at": "2024-01-15T10:32:45",
      "error_message": null,
      "progress": "Task completed successfully",
      "metadata": {
        "videos": ["dQw4w9WgXcQ"],
        "request_type": "ingest"
      }
    }
  ],
  "total_count": 1
}
```

### Individual Task Status

#### GET `/tasks/{task_id}`

Get detailed information about a specific task.

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "command": ["python", "-m", "src.worker.ingest_worker", "--videos", "dQw4w9WgXcQ"],
  "status": "running",
  "created_at": "2024-01-15T10:30:15",
  "started_at": "2024-01-15T10:30:16",
  "completed_at": null,
  "error_message": null,
  "progress": "Processing video segments...",
  "metadata": {
    "videos": ["dQw4w9WgXcQ"],
    "request_type": "ingest"
  }
}
```

### Task Counts

#### GET `/tasks/count/running`

Get a simple count of currently running tasks.

**Response:**
```json
{
  "running_tasks": 2
}
```

### Maintenance

#### DELETE `/tasks/cleanup`

Clean up old completed and failed tasks.

**Query Parameters:**
- `days` (integer, default: 7): Remove tasks older than this many days

**Response:**
```json
{
  "cleaned_tasks": 5,
  "days": 7
}
```

## Task Status Values

- `pending`: Task is queued but not yet started
- `running`: Task is currently being executed
- `completed`: Task finished successfully
- `failed`: Task failed with an error
- `cancelled`: Task was cancelled

## Integration with Background Tasks

The task monitoring system is automatically integrated with:

### Ingest API (`POST /ingest`)

When you make an ingest request, the system now returns a task ID:

```json
{
  "status": "queued",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "cmd": ["python", "-m", "src.worker.ingest_worker", "--videos", "dQw4w9WgXcQ"],
  "message": "Background task queued with ID: 550e8400-e29b-41d4-a716-446655440000"
}
```

### Temporal Video Ingest (`POST /temporal/ingest-video`)

The temporal video ingest endpoint also tracks background processing tasks for multiple videos.

## Usage Examples

### Monitor Running Tasks

```bash
# Get count of running tasks
curl -X GET "http://localhost:8000/tasks/count/running"

# Get detailed list of running tasks
curl -X GET "http://localhost:8000/tasks/running"
```

### Track Specific Task

```bash
# Get status of a specific task
curl -X GET "http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000"
```

### Get System Statistics

```bash
# Get overall task statistics
curl -X GET "http://localhost:8000/tasks/stats"
```

### Cleanup Old Tasks

```bash
# Clean up tasks older than 7 days
curl -X DELETE "http://localhost:8000/tasks/cleanup?days=7"
```

## Testing

Use the provided test script to verify the task monitoring functionality:

```bash
python scripts/test_task_monitoring.py
```

This script will:
1. Check initial task statistics
2. Trigger background tasks
3. Monitor task progress
4. Verify task completion
5. Test error handling

## Implementation Details

The task monitoring system uses:
- **In-memory storage**: Tasks are stored in memory for fast access
- **Async operations**: All operations are asynchronous for better performance
- **Thread-safe**: Uses asyncio locks for thread safety
- **Automatic cleanup**: Old tasks are automatically cleaned up
- **Progress tracking**: Real-time progress updates during task execution

## Error Handling

The API provides comprehensive error handling:
- 404 errors for non-existent tasks
- 500 errors for internal server issues
- Proper error messages in task status for failed operations
- Graceful handling of malformed requests 