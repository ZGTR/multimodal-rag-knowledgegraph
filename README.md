# Multi-Modal Knowledge Graph RAG Skeleton

A FastAPI-based application for ingesting and processing content from multiple sources (YouTube, Twitter, Instagram) and building a knowledge graph with RAG capabilities.

## Features

- **Multi-source ingestion**: YouTube videos, Twitter posts, Instagram posts
- **FastAPI REST API**: Clean, documented API endpoints
- **Background processing**: Asynchronous worker for content processing
- **Knowledge Graph integration**: Gremlin-based graph storage
- **RAG capabilities**: Vector search and retrieval
- **Comprehensive testing**: Unit, integration, and end-to-end tests

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp local.env .env

# Edit the .env file with your actual values
# You'll need to set up:
# - VECTORDB_URI: PostgreSQL connection string
# - KG_URI: Gremlin server connection
# - OPENAI_API_KEY: Your OpenAI API key
# - TWITTER_BEARER_TOKEN: Twitter API token (optional)
# - INSTAGRAM_ACCESS_TOKEN: Instagram API token (optional)
```

**Required Environment Variables:**
- `VECTORDB_URI`: PostgreSQL connection string (e.g., `postgresql://localhost:5432/vectordb`)
- `KG_URI`: Gremlin server connection (e.g., `ws://localhost:8182/gremlin`)
- `OPENAI_API_KEY`: Your OpenAI API key for embeddings

**Optional Environment Variables:**
- `TWITTER_BEARER_TOKEN`: For Twitter content ingestion
- `INSTAGRAM_ACCESS_TOKEN`: For Instagram content ingestion
- `BEDROCK_REGION` and `BEDROCK_MODEL_ID`: For AWS Bedrock integration

### 3. Run the Application

```bash
# Start the FastAPI server
uvicorn src.api.handler:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Main Endpoint**: `POST /ingest`

### 5. Test the API

```bash
# Test with sample data
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    "twitter": ["https://twitter.com/elonmusk/status/123456789"],
    "ig": ["https://www.instagram.com/p/ABC123/"]
  }'
```

## API Endpoints

### POST /ingest

Ingest content from multiple sources.

**Request Body:**
```json
{
  "videos": ["https://www.youtube.com/watch?v=VIDEO_ID"],
  "twitter": ["https://twitter.com/user/status/TWEET_ID"],
  "ig": ["https://www.instagram.com/p/POST_ID/"]
}
```

**Response:**
```json
{
  "status": "queued",
  "cmd": ["python", "-m", "src.worker.main", "--videos", "..."]
}
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/      # Unit tests
pytest tests/api/       # API tests
pytest tests/integration/  # Integration tests

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src
```

## Project Structure

```
├── src/
│   ├── api/
│   │   └── handler.py          # FastAPI application
│   ├── config/
│   │   ├── settings.py         # Environment configuration
│   │   └── local_config.py     # Local development config
│   ├── ingest/
│   │   ├── base.py            # Base ingestion classes
│   │   ├── youtube.py         # YouTube content ingestion
│   │   ├── twitter.py         # Twitter content ingestion
│   │   └── instagram.py       # Instagram content ingestion
│   ├── worker/
│   │   └── main.py            # Background worker
│   ├── kg/
│   │   ├── gremlin_client.py  # Graph database client
│   │   └── schema.py          # Graph schema
│   └── rag/
│       ├── retriever.py       # RAG retriever
│       └── vector_store.py    # Vector store
├── tests/
│   ├── unit/                  # Unit tests
│   ├── api/                   # API tests
│   ├── integration/           # Integration tests
│   └── test_end_to_end.py     # End-to-end tests
├── local.env                  # Environment variables template
├── requirements.txt           # Python dependencies
└── pytest.ini               # Test configuration
```

## Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **youtube-transcript-api**: YouTube transcript extraction
- **tweepy**: Twitter API client
- **yt-dlp**: YouTube video processing
- **langchain**: RAG framework
- **psycopg2**: PostgreSQL adapter

## Development

The application uses:
- **Hot reload**: Server automatically restarts on code changes
- **Background tasks**: Content processing runs asynchronously
- **Type hints**: Full type annotation support
- **Pytest**: Comprehensive testing framework
- **Mocking**: Tests use mocks to avoid external API calls
- **Environment configuration**: Uses `local.env` for development settings

## Next Steps

1. Configure database connections (PostgreSQL, Gremlin)
2. Set up API keys for external services
3. Implement content processing logic
4. Add authentication and rate limiting
5. Deploy to production environment
