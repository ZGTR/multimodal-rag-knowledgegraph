# Multimodal RAG Knowledge Graph

A comprehensive system for ingesting data from YouTube, Twitter, and Instagram, storing embeddings in a vector database, and building a knowledge graph using AWS Neptune.

## Features

- **Multi-source Data Ingestion**: YouTube, Twitter, and Instagram
- **Vector Storage**: PostgreSQL with pgvector extension
- **Knowledge Graph**: AWS Neptune (Gremlin-compatible)
- **Entity Extraction**: Automatic extraction of named entities
- **RESTful API**: FastAPI-based endpoints
- **Background Processing**: Asynchronous data processing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Vector Store  │    │ Knowledge Graph │
│                 │    │                 │    │                 │
│ • YouTube       │───▶│ • PostgreSQL    │    │ • AWS Neptune   │
│ • Twitter       │    │ • pgvector      │    │ • Gremlin       │
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

## Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- AWS Neptune cluster (or local Gremlin server)
- API keys for data sources

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

### 3. AWS Neptune Setup

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

### 4. Environment Configuration

Create `local.env` file:

```env
# App Configuration
APP_ENV=dev

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

### 5. Database Setup

#### PostgreSQL with pgvector

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

### 6. Run the Application

```bash
# Start the FastAPI server
python -m uvicorn src.api.handler:app --reload --host 0.0.0.0 --port 8000
```

### 7. Test the API

```bash
# Ingest YouTube data
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
  }'

# Search vector store
curl "http://localhost:8000/search?query=love&k=3"

# Get all entities
curl "http://localhost:8000/entities"

# Get whole graph
curl "http://localhost:8000/graph"
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

### GET /search
Search the vector store.

**Query Parameters:**
- `query`: Search query
- `k`: Number of results (default: 5)

### GET /entities
Retrieve all entities from the knowledge graph.

### GET /graph
Retrieve the complete knowledge graph (nodes and edges).

## Architecture Details

### Data Ingestion Strategy

The system uses a strategy pattern for data ingestion:

```python
# Base strategy interface
class IngestStrategy(ABC):
    @abstractmethod
    def fetch_data(self, source_id: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def extract_content(self, data: Dict[str, Any]) -> str:
        pass

# YouTube strategy implementation
class YouTubeStrategy(IngestStrategy):
    def fetch_data(self, video_id: str) -> Dict[str, Any]:
        # Fetch video metadata and transcript
        pass
    
    def extract_content(self, data: Dict[str, Any]) -> str:
        # Extract transcript and metadata
        pass
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
class NewSourceStrategy(IngestStrategy):
    def fetch_data(self, source_id: str) -> Dict[str, Any]:
        # Implement data fetching
        pass
    
    def extract_content(self, data: Dict[str, Any]) -> str:
        # Implement content extraction
        pass
```

2. Add to the worker:
```python
# In ingest_worker.py
if new_source_data:
    strategy = NewSourceStrategy()
    # Process data...
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
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
# Delete Neptune cluster and resources
./cleanup_neptune.sh
```

## Troubleshooting

### Common Issues

1. **Neptune Connection Failed**:
   - Check security group allows port 8182
   - Verify cluster endpoint is correct
   - Ensure SSL configuration is proper

2. **Vector Store Connection Failed**:
   - Verify PostgreSQL is running
   - Check pgvector extension is installed
   - Confirm database credentials

3. **API Key Issues**:
   - Verify API keys are valid
   - Check rate limits
   - Ensure proper permissions

### Logs

Check application logs for detailed error information:

```bash
# View logs
tail -f logs/app.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 