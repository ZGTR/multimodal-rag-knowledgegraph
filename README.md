# Multimodal RAG with Knowledge Graph

This is a lightweight experimentation repo for multimodal retrieval-augmented generation (RAG) system that ingests data from YouTube, Twitter, and Instagram, stores embeddings in a vector database, and builds a knowledge graph using Gremlin.

This is not aimed to be prod-ready (though it can be). Albeit, we have to move the Neptune and Postgres deployments to other repos to correctly manage their IaC, add tests, follow DDD principles, etc. 

I may evolve this overtime. If you like to ask questions, please don't hesitate to send me an email: mohammadshakergtr@gmail.com

For everything deployment and local dev setup, please check [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md).

## Features

- **Multimodal Ingestion**: YouTube videos, Twitter posts, Instagram content. Both text and video.
- **Vector Search**: Semantic search using PostgreSQL with pgvector
- **Knowledge Graph**: Entity extraction and relationship mapping using Gremlin/Neptune
- **RESTful API**: FastAPI-based endpoints for ingestion and search
- **Scalable Architecture**: Worker-based ingestion with strategy pattern
- **Infrastructure as Code**: Complete Terraform setup for AWS deployment
- **Multi-Environment Support**: Local, dev, staging, and production environments
- **Temporal Video Search**: Search for entities and topics with precise timestamps
- **Entity Extraction**: Automatic identification of people, organizations, locations
- **Comprehensive Logging**: Detailed progress tracking for all operations

## Temporal Video Search

The system now supports **temporal video search** - the ability to search for specific topics or entities within videos and receive precise timestamps indicating when they appear or are discussed.

### Key Capabilities

- **Precise Timestamps**: Find exactly when entities/topics appear in videos
- **Semantic Search**: Use natural language to find relevant content
- **Entity Filtering**: Search for specific people, organizations, locations
- **Topic Filtering**: Find discussions of specific topics
- **Video Timeline**: Get complete timeline of any video with all segments
- **Background Processing**: Process multiple videos asynchronously
- **Detailed Logging**: Comprehensive progress tracking for all operations

### Quick Demo

```bash
# Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Ingest a YouTube video with temporal processing
curl -X POST "http://localhost:8000/temporal/ingest-video" \
  -H "Content-Type: application/json" \
  -d '{"video_ids": ["dQw4w9WgXcQ"]}'

# Search for entity mentions with timestamps
curl -X POST "http://localhost:8000/temporal/search-entity" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Elon Musk", "max_results": 5}'

# Get video timeline
curl -X GET "http://localhost:8000/temporal/video-timeline/dQw4w9WgXcQ"
```

### API Endpoints

#### Temporal Search (`/temporal`)
- `POST /temporal/ingest-video` - Ingest videos with temporal processing
- `POST /temporal/search` - Semantic search with temporal precision
- `POST /temporal/search-entity` - Search for specific entity mentions
- `POST /temporal/search-topic` - Search for specific topic discussions
- `GET /temporal/video-timeline/{video_id}` - Get complete video timeline
- `GET /temporal/video-info/{video_id}` - Get video metadata and statistics
- `GET /temporal/search-suggestions` - Get search suggestions
- `GET /temporal/stats` - Get system statistics

#### General Search (`/search`)
- `GET /search/` - General search endpoint (backward compatible)
- `POST /search/general` - Enhanced search with options
- `GET /search/suggestions` - Get search suggestions
- `GET /search/stats` - Get search statistics

For complete API documentation, see [Temporal API Reference](docs/temporal-api-reference.md).

## Enhanced Logging

The system now includes comprehensive logging for all operations, providing detailed visibility into:

### Video Processing Logs
- **Step-by-step progress**: Each processing step is logged with timestamps
- **Metadata extraction**: Video title, duration, upload date, author
- **Transcript processing**: Number of entries, total duration, average words per entry
- **Temporal segmentation**: Segment creation with time ranges
- **Entity extraction**: Entities found in each segment
- **Storage operations**: Vector store and knowledge graph storage progress

### Search Operation Logs
- **Query details**: Search parameters, filters, and time ranges
- **Processing time**: Performance metrics for each operation
- **Result statistics**: Number of results, filtering details
- **Entity and topic tracking**: Specific entities and topics found

### Example Log Output
```
[2024-01-15 10:30:15] INFO youtube_strategy: Starting YouTube ingestion for 1 items
[2024-01-15 10:30:15] INFO youtube_strategy: Extracted video IDs: ['dQw4w9WgXcQ']
[2024-01-15 10:30:16] INFO youtube: [1/1] Processing video: dQw4w9WgXcQ
[2024-01-15 10:30:16] INFO youtube: [dQw4w9WgXcQ] Step 1/5: Extracting video metadata...
[2024-01-15 10:30:17] INFO youtube: [dQw4w9WgXcQ] Metadata extracted: 'Example Video' by Example Channel
[2024-01-15 10:30:17] INFO youtube: [dQw4w9WgXcQ] Step 2/5: Retrieving transcript...
[2024-01-15 10:30:18] INFO youtube: [dQw4w9WgXcQ] Transcript retrieved: 45 entries
[2024-01-15 10:30:18] INFO youtube: [dQw4w9WgXcQ] Step 3/5: Processing temporal segments...
[2024-01-15 10:30:19] INFO youtube: [dQw4w9WgXcQ] Created 12 temporal segments
[2024-01-15 10:30:20] INFO youtube: [dQw4w9WgXcQ] Step 5/5: Video processing completed in 4.23s
```

### Testing Enhanced Logging

```bash
# Test logging functionality
python scripts/test_logging.py

# Run with detailed logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
exec(open('scripts/test_logging.py').read())
"
```

## Architecture

The system uses **both** Knowledge Graph and Vector Database components working together:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   YouTube API   │    │   Twitter API   │    │ Instagram API   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Ingest Worker  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Content Items  │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Vector Store   │    │ Entity Extractor│    │ Knowledge Graph │
│ (PostgreSQL +   │    │                 │    │ (Gremlin/       │
│   pgvector)     │    │                 │    │   Neptune)      │
│                 │    │                 │    │                 │
│ • Semantic      │    │ • Named Entity  │    │ • Entity        │
│   Search        │    │   Recognition   │    │   Extraction    │
│ • Embeddings    │    │ • Entity        │    │   Queries       │
│ • Similarity    │    │   Extraction    │    │   Graph         │
│ • Temporal      │    │ • Temporal      │    │ • Temporal      │
│   Segments      │    │   Processing    │    │   Relationships │
│ • Detailed      │    │ • Progress      │    │ • Operation     │
│   Logging       │    │   Logging       │    │ • Logging       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI App   │
                    │                 │
                    │ • Temporal      │
                    │   Search API    │
                    │ • General       │
                    │   Search API    │
                    │ • Ingestion API │
                    │ • Request/      │
                    │   Response      │
                    │   Logging       │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   REST API      │
                    └─────────────────┘
```

### Component Roles

**Vector Database (PostgreSQL + pgvector)**
- Stores document embeddings for semantic search
- Enables similarity-based content retrieval
- Handles large-scale text search and matching
- **NEW**: Stores temporal video segments with precise timestamps
- **NEW**: Detailed logging of storage and search operations

**Knowledge Graph (Gremlin/Neptune)**
- Extracts and stores named entities (people, places, organizations)
- Maps relationships between entities
- Enables graph-based queries and entity exploration
- **NEW**: Tracks temporal relationships between entities and video segments
- **NEW**: Comprehensive operation logging

**Temporal Search Service**
- **NEW**: Processes videos into temporal segments (default: 30 seconds)
- **NEW**: Extracts entities from each segment with timestamps
- **NEW**: Enables precise temporal search across video content
- **NEW**: Provides video timeline and metadata services
- **NEW**: Detailed performance and progress logging

**Both components are required** - they serve different but complementary purposes in the multimodal RAG system.

## Project Structure

```
├── infra/                      # Infrastructure configuration
│   ├── local-dev/              # Local development configurations
│   │   ├── neptune/            # Neptune Docker setup
│   │   └── postgres/           # PostgreSQL Docker configuration
│   └── terraform/              # Terraform infrastructure as code
│       ├── main.tf             # Main Terraform configuration
│       ├── variables.tf        # Variable definitions
│       ├── environments/       # Environment-specific configurations
│       ├── modules/            # Terraform modules
│       │   ├── vpc/           # VPC and networking
│       │   ├── neptune/       # Neptune cluster
│       │   ├── postgresql/    # PostgreSQL RDS with pgvector
│       │   ├── alb/           # Application Load Balancer
│       │   └── ecs/           # ECS cluster and service
│       └── scripts/           # Deployment scripts
├── scripts/                    # Utility scripts
│   ├── local-dev.sh           # Local development setup script
│   ├── demo_temporal_search.py # Temporal search demo
│   ├── test_temporal_api.py   # API testing script
│   └── test_logging.py        # Logging test script
├── src/                        # Application source code
│   ├── api/                   # FastAPI application
│   │   ├── main.py            # Main app configuration
│   │   └── routers/           # API route handlers
│   │       ├── temporal.py    # Temporal search endpoints
│   │       ├── search.py      # General search endpoints
│   │       └── ...
│   ├── ingest/                # Content ingestion
│   │   ├── youtube.py         # Enhanced: Temporal video processing
│   │   └── base.py           # Video-specific models
│   ├── rag/                   # RAG components
│   │   ├── temporal_search.py # Temporal search service
│   │   └── vector_store.py   # Enhanced: Vector database operations
│   ├── kg/                    # Knowledge graph
│   │   ├── entity_extraction.py # Enhanced: Entity extraction with logging
│   │   └── gremlin_client.py
│   └── worker/                # Background processing
│       └── strategies/
│           └── youtube.py     # Enhanced: Temporal processing strategy
├── docs/                       # Documentation
│   ├── temporal-video-search.md # Temporal search architecture
│   └── temporal-api-reference.md # API reference
├── tests/                      # Test files
├── DEPLOYMENT_GUIDE.md         # Comprehensive deployment guide
└── README.md                   # This file
```


## Prerequisites

### Local Development
- Python 3.11+
- Docker and Docker Compose
- Git

### AWS Deployment
- AWS Account with appropriate permissions
- Terraform (>= 1.0)
- AWS CLI configured


## Quick Start

### Local Development and Deployments
For detailed deployment instructions, see [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md).


### Test the Setup

```bash
# Test the API
curl http://localhost:8000/health

# Ingest a YouTube video (legacy)
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]}'

# Search for content (legacy)
curl "http://localhost:8000/search?query=trump&k=5"

# Temporal video search
curl -X POST "http://localhost:8000/temporal/ingest-video" \
  -H "Content-Type: application/json" \
  -d '{"video_ids": ["dQw4w9WgXcQ"]}'

# Search for entity mentions with timestamps
curl -X POST "http://localhost:8000/temporal/search-entity" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Elon Musk", "max_results": 5}'
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/api/

# Test temporal search API
python scripts/test_temporal_api.py

# Run temporal search demo
python scripts/demo_temporal_search.py

# Test enhanced logging
python scripts/test_logging.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Logging Configuration

### Log Levels
- **INFO**: General progress and important events
- **DEBUG**: Detailed step-by-step operations
- **WARNING**: Non-critical issues and fallbacks
- **ERROR**: Critical failures and exceptions

### Log Format
```
[2024-01-15 10:30:15] INFO component_name: Message description
```

### Customizing Log Levels
```python
import logging
# Set debug level for detailed logging
logging.basicConfig(level=logging.DEBUG)

# Set info level for general progress
logging.basicConfig(level=logging.INFO)
```

## Documentation

- [Temporal Video Search Architecture](docs/temporal-video-search.md) - Comprehensive guide to temporal search functionality
- [Temporal API Reference](docs/temporal-api-reference.md) - Complete API documentation
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Infrastructure and deployment instructions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 