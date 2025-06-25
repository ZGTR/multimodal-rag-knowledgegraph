# Temporal Video Search Architecture

## Overview

This document describes the architecture for ingesting YouTube videos and enabling temporal search for entities and topics within video content. The system allows users to search for specific topics or entities and receive precise timestamps indicating when they appear or are discussed in videos.

## Architecture Components

### 1. Data Models

#### VideoSegment
Represents a temporal segment of a video with associated content:
- `start_time`: Start time in seconds
- `end_time`: End time in seconds  
- `text`: Transcript text for this segment
- `confidence`: Confidence score for transcript accuracy
- `entities`: List of entities mentioned in this segment
- `topics`: List of topics discussed in this segment
- `visual_entities`: List of entities visible in this segment (future enhancement)
- `embedding`: Vector embedding for semantic search

#### VideoContentItem
Extended content item specifically for video content:
- `id`: Video identifier
- `source`: Source platform (e.g., "youtube")
- `url`: Video URL
- `title`: Video title
- `description`: Video description
- `duration`: Video duration in seconds
- `segments`: List of VideoSegment objects
- `thumbnail_url`: Video thumbnail URL
- `raw`: Raw metadata from source

### 2. Video Ingestion Pipeline

#### YouTubeVideoSource
Enhanced YouTube source that processes videos with temporal precision:

1. **Video Metadata Extraction**: Uses `yt-dlp` to extract comprehensive video metadata
2. **Transcript Processing**: Retrieves transcripts with precise timestamps using `youtube-transcript-api`
3. **Temporal Segmentation**: Groups transcript entries into configurable time segments (default: 30 seconds)
4. **Entity Extraction**: Uses spaCy to extract named entities from each segment
5. **Vector Embedding**: Generates embeddings for each segment for semantic search
6. **Storage**: Stores segments in vector database with temporal metadata

#### Processing Flow
```
YouTube Video → Metadata Extraction → Transcript Retrieval → 
Temporal Segmentation → Entity Extraction → Embedding Generation → 
Vector Store Storage → Knowledge Graph Storage
```

### 3. Temporal Search Service

#### TemporalSearchService
Core service for searching video content with temporal precision:

- **Semantic Search**: Uses vector similarity to find relevant segments
- **Entity Filtering**: Filter results by specific entities
- **Topic Filtering**: Filter results by specific topics
- **Time Range Filtering**: Filter results within specific time ranges
- **Video Filtering**: Search within specific videos only

#### Search Capabilities
1. **General Search**: Search for any content across all videos
2. **Entity Search**: Find specific entity mentions with timestamps
3. **Topic Search**: Find discussions of specific topics
4. **Video Timeline**: Get complete timeline of a video with all segments

### 4. API Endpoints

#### Temporal Search Endpoints
- `POST /temporal-search`: General temporal search with filters
- `POST /search-entity`: Search for specific entity mentions
- `POST /search-topic`: Search for specific topic discussions
- `GET /video-timeline/{video_id}`: Get complete video timeline

#### Legacy Compatibility
- `GET /search`: Backward-compatible search endpoint

### 5. Data Storage

#### Vector Store (PostgreSQL + pgvector)
Stores video segments with temporal metadata:
- Segment text content
- Start/end timestamps
- Extracted entities
- Topics
- Video metadata
- Vector embeddings

#### Knowledge Graph (Neptune)
Stores relationships between:
- Videos and their segments
- Entities mentioned in segments
- Topics discussed
- Temporal relationships

## Usage Examples

### 1. Ingest a YouTube Video
```bash
# Using the API
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"videos": ["dQw4w9WgXcQ"]}'

# Using the worker directly
python -m src.worker.ingest_worker --videos dQw4w9WgXcQ
```

### 2. Search for Entity Mentions
```bash
curl -X POST "http://localhost:8000/search-entity" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Elon Musk", "max_results": 5}'
```

### 3. Search for Topic Discussions
```bash
curl -X POST "http://localhost:8000/search-topic" \
  -H "Content-Type: application/json" \
  -d '{"topic": "artificial intelligence", "max_results": 5}'
```

### 4. Get Video Timeline
```bash
curl -X GET "http://localhost:8000/video-timeline/dQw4w9WgXcQ"
```

### 5. General Temporal Search
```bash
curl -X POST "http://localhost:8000/temporal-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "entity_filter": "OpenAI",
    "time_range": [60, 300],
    "max_results": 10
  }'
```

## Configuration

### Environment Variables
```bash
# Vector Database
VECTORDB_URI=postgresql://user:pass@localhost:5432/vectordb

# OpenAI (for embeddings)
OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL_NAME=text-embedding-3-small

# Neptune (for knowledge graph)
NEPTUNE_ENDPOINT=your_neptune_endpoint
NEPTUNE_PORT=8182
NEPTUNE_USERNAME=your_username
NEPTUNE_PASSWORD=your_password
```

### Segment Configuration
Default segment duration is 30 seconds, but can be configured in `YouTubeVideoSource._process_segments()`.

## Future Enhancements

### 1. Computer Vision Integration
- Face recognition for person identification
- Object detection for visual entity extraction
- Scene understanding for topic classification

### 2. Advanced Topic Modeling
- LDA topic modeling for automatic topic discovery
- Hierarchical topic clustering
- Topic evolution tracking across video timeline

### 3. Multi-modal Search
- Audio-based search (speech-to-text)
- Visual search (image similarity)
- Combined audio-visual-text search

### 4. Real-time Processing
- Live video stream processing
- Real-time entity detection
- Streaming search results

### 5. Enhanced Metadata
- Speaker identification
- Sentiment analysis
- Language detection
- Content moderation

## Performance Considerations

### 1. Segment Size Optimization
- Smaller segments (10-15s) for precise search
- Larger segments (60s) for faster processing
- Adaptive segmentation based on content

### 2. Caching Strategy
- Cache frequently accessed video metadata
- Cache search results for common queries
- Implement Redis for session management

### 3. Batch Processing
- Process multiple videos in parallel
- Batch entity extraction operations
- Optimize vector store operations

## Monitoring and Analytics

### 1. Processing Metrics
- Video processing time
- Segment generation rate
- Entity extraction accuracy
- Embedding generation performance

### 2. Search Analytics
- Query frequency and patterns
- Result relevance scores
- User interaction metrics
- Search performance metrics

### 3. System Health
- Vector store performance
- Knowledge graph query performance
- API response times
- Error rates and types

## Troubleshooting

### Common Issues

1. **Transcript Not Available**
   - Check if video has captions enabled
   - Verify language settings
   - Use fallback transcription services

2. **Entity Extraction Failures**
   - Ensure spaCy model is properly installed
   - Check text preprocessing
   - Verify entity types in configuration

3. **Vector Store Connection Issues**
   - Verify PostgreSQL connection string
   - Check pgvector extension installation
   - Validate embedding model configuration

4. **Search Performance Issues**
   - Optimize segment size
   - Add appropriate indexes
   - Implement result caching

## Demo Script

Run the demo script to test the functionality:
```bash
python scripts/demo_temporal_search.py
```

This will demonstrate:
- Video ingestion with temporal processing
- Entity and topic search
- Video timeline generation
- Search result formatting 