# Multimodal RAG Knowledge Graph

A comprehensive system for ingesting data from YouTube, Twitter, and Instagram, storing embeddings in a vector database, and building a knowledge graph using Gremlin-compatible databases.

## Features

- **Multi-source Data Ingestion**: YouTube, Twitter, and Instagram
- **Vector Storage**: PostgreSQL with pgvector extension (with in-memory fallback)
- **Knowledge Graph**: Gremlin-compatible databases (AWS Neptune or local TinkerPop)
- **Entity Extraction**: Automatic extraction of named entities
- **RESTful API**: FastAPI-based endpoints
- **Background Processing**: Asynchronous data processing
- **Clean Architecture**: OOP strategies with proper separation of concerns

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Vector Store  │    │ Knowledge Graph │
│                 │    │                 │    │                 │
│ • YouTube       │───▶│ • PostgreSQL    │    │ • Gremlin       │
│ • Twitter       │    │ • pgvector      │    │ • TinkerPop     │
│ • Instagram     │    │ • Embeddings    │    │ • Entities      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI API   │
                    │                 │
                    │ • /ingest       │
                    │ • /search       │
                    │ • /entities     │
                    │ • /graph        │
                    └─────────────────┘
```

## Quick Start (Development)

### 1. Prerequisites

- Python 3.8+
- Docker (for local Gremlin server)
- API keys for data sources (optional for testing)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd multimodal-rag-knowledgegraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm
```

### 3. Start Local Gremlin Server

```bash
# Start TinkerPop Gremlin Server (recommended for development)
docker run -d --name gremlin-server -p 8182:8182 tinkerpop/gremlin-server:latest

# Verify it's running
docker ps | grep gremlin-server
```

### 4. Environment Configuration

Create `local.env` file (optional for development):

```env
# App Configuration
APP_ENV=dev

# Vector Database (optional - will use in-memory fallback)
VECTORDB_URI=postgresql://username:password@localhost:5432/vectordb

# Knowledge Graph (Local TinkerPop)
KG_URI=ws://localhost:8182/gremlin

# Data Source APIs (optional for testing)
YOUTUBE_API_KEY=your-youtube-api-key
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
INSTAGRAM_ACCESS_TOKEN=your-instagram-access-token
```

### 5. Run the Application

```bash
# Start the FastAPI server
source venv/bin/activate
python -m uvicorn src.api.handler:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test the System

```bash
# Test YouTube ingestion
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]}'

# Check entities
curl http://localhost:8000/entities

# Check graph
curl http://localhost:8000/graph

# Search documents
curl "http://localhost:8000/search?query=test&k=5"

# View API documentation
open http://localhost:8000/docs
```

### 7. Test Knowledge Graph Connection

```bash
# Test Gremlin connection
python test_neptune.py
```

## Production Setup

### AWS Neptune Setup

#### Option A: Automated Setup (Recommended)

```bash
# Run the Neptune setup script
./setup_neptune.sh

# Follow the prompts to create your Neptune cluster
# The script will output configuration for your local.env file
```

#### Option B: Manual Setup

1. **Create Neptune Cluster**:
   - Go to AWS Console → Neptune
   - Click "Create database"
   - Choose "Standard create"
   - Engine: Neptune, Version: Latest
   - Instance: db.r5.large (development)
   - VPC: Default or custom
   - Security Group: Allow port 8182 from your IP

2. **Configure Security**:
   - Create security group with inbound rule: TCP 8182 from 0.0.0.0/0
   - Attach to Neptune cluster

3. **Get Endpoint**:
   - Note the cluster endpoint from AWS Console
   - Format: `your-cluster.cluster-xxxxx.region.neptune.amazonaws.com`

### PostgreSQL with pgvector

```bash
# Install PostgreSQL and pgvector
# On macOS with Homebrew:
brew install postgresql
brew install pgvector

# Create database
createdb vectordb

# Enable pgvector extension
psql vectordb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Production Environment

Update `local.env` for production:

```env
# App Configuration
APP_ENV=prod

# Vector Database
VECTORDB_URI=postgresql://username:password@localhost:5432/vectordb

# Knowledge Graph (Neptune)
NEPTUNE_CLUSTER_ENDPOINT=your-cluster.cluster-xxxxx.region.neptune.amazonaws.com
NEPTUNE_PORT=8182
NEPTUNE_REGION=us-east-1
NEPTUNE_USE_SSL=true
NEPTUNE_VERIFY_SSL=true

# Data Source APIs
YOUTUBE_API_KEY=your-youtube-api-key
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
INSTAGRAM_ACCESS_TOKEN=your-instagram-access-token
```

## API Endpoints

### POST /ingest
Ingest data from specified sources.

**Request Body:**
```json
{
  "videos": ["https://www.youtube.com/watch?v=VIDEO_ID"],
  "twitter": ["USERNAME"],
  "ig": ["USERNAME"]
}
```

**Response:**
```json
{
  "status": "queued",
  "cmd": ["python", "-m", "src.worker.ingest_worker", "--videos", "VIDEO_ID"]
}
```

### GET /search
Search the vector store.

**Query Parameters:**
- `query`: Search query
- `k`: Number of results (default: 5)

**Response:**
```json
{
  "status": "success",
  "query": "search term",
  "count": 1,
  "results": [
    {
      "content": "document content",
      "metadata": {"source": "youtube", "id": "video_id"}
    }
  ]
}
```

### GET /entities
Retrieve all entities from the knowledge graph.

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "entities": ["entity1", "entity2", ...]
}
```

### GET /graph
Retrieve the complete knowledge graph (nodes and edges).

**Response:**
```json
{
  "status": "success",
  "graph": {
    "nodes": [...],
    "edges": [...],
    "total_nodes": 10,
    "total_edges": 15
  }
}
```

## Architecture Details

### Data Ingestion Strategy

The system uses a strategy pattern for data ingestion:

```python
# Base strategy interface
class BaseIngestStrategy(ABC):
    def __init__(self, vectordb=None, kg=None):
        self.vectordb = vectordb
        self.kg = kg

    @abstractmethod
    def ingest(self, items: Optional[List[str]] = None):
        """Ingest data from the source, process, and store."""
        pass

# YouTube strategy implementation
class YouTubeIngestStrategy(BaseIngestStrategy):
    def ingest(self, items: List[str]):
        video_ids = self.extract_video_ids(items)
        yt_items = self.fetch_content(video_ids)
        for item in yt_items:
            self.process_item(item)
```

### Knowledge Graph Schema

**Nodes:**
- `Content`: Video, tweet, or post content
- `Entity`: Named entities (people, places, topics)
- `User`: Content creators
- `Topic`: Themes and subjects

**Edges:**
- `contains_entity`: Content → Entity
- `created_by`: Content → User
- `related_to`: Entity → Entity
- `discusses`: Content → Topic

### Vector Store Schema

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),  -- OpenAI embedding dimension
    source_type VARCHAR(50),
    source_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Development

### Project Structure

```
src/
├── api/                    # FastAPI endpoints
├── bootstrap/              # Configuration and settings
├── config/                 # App configuration
├── ingest/                 # Data ingestion modules
├── kg/                     # Knowledge graph client
├── rag/                    # Vector store and retrieval
└── worker/                 # Background processing
    └── strategies/         # Ingestion strategies
```

### Adding New Data Sources

1. Create a new strategy class:
```python
class NewSourceStrategy(BaseIngestStrategy):
    def ingest(self, items: List[str]):
        # Implement data fetching and processing
        pass
```

2. Add to the worker:
```python
# In ingest_worker.py
STRATEGY_REGISTRY = {
    'youtube': YouTubeIngestStrategy,
    'newsource': NewSourceStrategy,
    # ...
}
```

### Testing

```bash
# Test knowledge graph connection
python test_neptune.py

# Test ingestion directly
python -m src.worker.ingest_worker --videos "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## Development Commands

```bash
# Start Gremlin Server
docker run -d --name gremlin-server -p 8182:8182 tinkerpop/gremlin-server:latest

# Start FastAPI App
source venv/bin/activate
python -m uvicorn src.api.handler:app --reload --host 0.0.0.0 --port 8000

# Test ingestion directly
python -m src.worker.ingest_worker --videos "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Test knowledge graph
python test_neptune.py

# View running containers
docker ps

# Stop Gremlin Server
docker stop gremlin-server
docker rm gremlin-server
```

## Deployment

### Production Considerations

1. **Neptune Configuration**:
   - Use Multi-AZ deployment
   - Enable encryption at rest
   - Configure proper IAM roles
   - Set up CloudWatch monitoring

2. **Vector Database**:
   - Use managed PostgreSQL service
   - Configure connection pooling
   - Set up automated backups

3. **API Security**:
   - Add authentication/authorization
   - Rate limiting
   - Input validation
   - CORS configuration

## Cleanup

When you're done with development/testing:

```bash
# Stop and remove Gremlin server
docker stop gremlin-server
docker rm gremlin-server

# Delete Neptune cluster and resources (if using AWS)
./cleanup_neptune.sh
```

## Troubleshooting

### Common Issues

1. **Gremlin Connection Failed**:
   - Check if Docker is running
   - Verify Gremlin server is started: `docker ps | grep gremlin-server`
   - Test connection: `python test_neptune.py`

2. **Vector Store Connection Failed**:
   - Verify PostgreSQL is running (if using)
   - Check pgvector extension is installed
   - System will fall back to in-memory store

3. **API Key Issues**:
   - Verify API keys are valid
   - Check rate limits
   - Ensure proper permissions

4. **Import Errors**:
   - Ensure virtual environment is activated
   - Check all dependencies are installed: `pip install -r requirements.txt`

### Logs

Check application logs for detailed error information:

```bash
# View Docker logs
docker logs gremlin-server

# View application logs in terminal
# (logs are displayed in the terminal where you started the FastAPI server)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 