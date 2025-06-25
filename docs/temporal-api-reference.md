# Temporal Search API Reference

## Overview

The Temporal Search API provides endpoints for ingesting YouTube videos and performing temporal search operations. All endpoints are prefixed with `/temporal`.

## Base URL

```
http://localhost:8000/temporal
```

## Authentication

Currently, no authentication is required for the API endpoints.

## Endpoints

### 1. Ingest Video

**POST** `/ingest-video`

Ingest a YouTube video with temporal processing, extracting segments, entities, and embeddings.

#### Request Body

```json
{
  "video_ids": ["dQw4w9WgXcQ"],
  "process_segments": true,
  "segment_duration": 30.0
}
```

#### Parameters

- `video_ids` (array, required): List of YouTube video IDs to process
- `process_segments` (boolean, optional): Whether to process into temporal segments (default: true)
- `segment_duration` (float, optional): Duration of each segment in seconds (default: 30.0)

#### Response

```json
{
  "status": "success",
  "message": "Video 'Example Video Title' processed successfully",
  "video_id": "dQw4w9WgXcQ",
  "segments_processed": 12,
  "entities_found": ["Elon Musk", "OpenAI", "Artificial Intelligence"],
  "duration": 360.5
}
```

#### Example

```bash
curl -X POST "http://localhost:8000/temporal/ingest-video" \
  -H "Content-Type: application/json" \
  -d '{
    "video_ids": ["dQw4w9WgXcQ"],
    "process_segments": true,
    "segment_duration": 30.0
  }'
```

### 2. Temporal Search

**POST** `/search`

Perform semantic search across video content with temporal precision.

#### Request Body

```json
{
  "query": "artificial intelligence",
  "video_ids": ["dQw4w9WgXcQ"],
  "entity_filter": "OpenAI",
  "topic_filter": "machine learning",
  "time_range": [60, 300],
  "max_results": 10
}
```

#### Parameters

- `query` (string, required): Search query
- `video_ids` (array, optional): Filter to specific videos
- `entity_filter` (string, optional): Filter by specific entity
- `topic_filter` (string, optional): Filter by specific topic
- `time_range` (array, optional): Time range in seconds [start, end]
- `max_results` (integer, optional): Maximum number of results (default: 10)

#### Response

```json
{
  "query": "artificial intelligence",
  "results_count": 3,
  "results": [
    {
      "video_id": "dQw4w9WgXcQ",
      "video_title": "Example Video",
      "video_url": "https://youtu.be/dQw4w9WgXcQ",
      "start_time": 120.5,
      "end_time": 150.0,
      "matched_text": "In this segment we discuss artificial intelligence...",
      "entities": ["OpenAI", "GPT-4"],
      "topics": ["machine learning"],
      "confidence": 0.95,
      "segment_id": "dQw4w9WgXcQ_120.5_150.0"
    }
  ]
}
```

#### Example

```bash
curl -X POST "http://localhost:8000/temporal/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "max_results": 5
  }'
```

### 3. Entity Search

**POST** `/search-entity`

Search for specific entity mentions in videos.

#### Request Body

```json
{
  "entity": "Elon Musk",
  "video_ids": ["dQw4w9WgXcQ"],
  "max_results": 10
}
```

#### Parameters

- `entity` (string, required): Entity to search for
- `video_ids` (array, optional): Filter to specific videos
- `max_results` (integer, optional): Maximum number of results (default: 10)

#### Response

Same format as temporal search response.

#### Example

```bash
curl -X POST "http://localhost:8000/temporal/search-entity" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "Elon Musk",
    "max_results": 5
  }'
```

### 4. Topic Search

**POST** `/search-topic`

Search for specific topic discussions in videos.

#### Request Body

```json
{
  "topic": "machine learning",
  "video_ids": ["dQw4w9WgXcQ"],
  "max_results": 10
}
```

#### Parameters

- `topic` (string, required): Topic to search for
- `video_ids` (array, optional): Filter to specific videos
- `max_results` (integer, optional): Maximum number of results (default: 10)

#### Response

Same format as temporal search response.

#### Example

```bash
curl -X POST "http://localhost:8000/temporal/search-topic" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "machine learning",
    "max_results": 5
  }'
```

### 5. Video Timeline

**GET** `/video-timeline/{video_id}`

Get complete timeline of a video with all segments and entities.

#### Parameters

- `video_id` (string, required): YouTube video ID

#### Response

```json
[
  {
    "video_id": "dQw4w9WgXcQ",
    "video_title": "Example Video",
    "video_url": "https://youtu.be/dQw4w9WgXcQ",
    "start_time": 0.0,
    "end_time": 30.0,
    "matched_text": "Welcome to this video about...",
    "entities": ["OpenAI"],
    "topics": ["introduction"],
    "confidence": 0.95,
    "segment_id": "dQw4w9WgXcQ_0.0_30.0"
  }
]
```

#### Example

```bash
curl -X GET "http://localhost:8000/temporal/video-timeline/dQw4w9WgXcQ"
```

### 6. Video Info

**GET** `/video-info/{video_id}`

Get comprehensive information about a video.

#### Parameters

- `video_id` (string, required): YouTube video ID

#### Response

```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Example Video Title",
  "description": "This is an example video description...",
  "duration": 360.5,
  "author": "Example Channel",
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "segment_count": 12,
  "total_entities": ["Elon Musk", "OpenAI", "Artificial Intelligence"]
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/temporal/video-info/dQw4w9WgXcQ"
```

### 7. Search Suggestions

**GET** `/search-suggestions`

Get search suggestions based on available entities and topics.

#### Query Parameters

- `query` (string, required): Base query for suggestions
- `max_suggestions` (integer, optional): Maximum number of suggestions (default: 10)

#### Response

```json
{
  "query": "artificial",
  "suggestions": [
    "artificial intelligence",
    "artificial neural networks",
    "artificial general intelligence"
  ]
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/temporal/search-suggestions?query=artificial&max_suggestions=5"
```

### 8. System Stats

**GET** `/stats`

Get statistics about the temporal search system.

#### Response

```json
{
  "total_videos": 25,
  "total_segments": 300,
  "total_entities": 150,
  "total_topics": 50,
  "avg_segments_per_video": 12.0,
  "avg_entities_per_segment": 2.5,
  "search_queries_today": 45,
  "most_searched_entities": ["Elon Musk", "OpenAI", "Google"],
  "most_searched_topics": ["artificial intelligence", "machine learning"]
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/temporal/stats"
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (video not found)
- `500`: Internal Server Error
- `503`: Service Unavailable (temporal search service not available)

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## Testing

Use the provided test script to verify API functionality:

```bash
python scripts/test_temporal_api.py
```

## Interactive Documentation

When the API is running, visit `http://localhost:8000/docs` for interactive Swagger documentation.

## Examples

### Complete Workflow

1. **Ingest a video:**
```bash
curl -X POST "http://localhost:8000/temporal/ingest-video" \
  -H "Content-Type: application/json" \
  -d '{"video_ids": ["dQw4w9WgXcQ"]}'
```

2. **Search for entity mentions:**
```bash
curl -X POST "http://localhost:8000/temporal/search-entity" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Elon Musk", "max_results": 5}'
```

3. **Get video timeline:**
```bash
curl -X GET "http://localhost:8000/temporal/video-timeline/dQw4w9WgXcQ"
```

### Advanced Search

```bash
curl -X POST "http://localhost:8000/temporal/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "entity_filter": "OpenAI",
    "time_range": [60, 300],
    "max_results": 10
  }'
```

This searches for "machine learning" content, filtered by OpenAI mentions, within the time range 60-300 seconds. 