# Multimodal RAG with Knowledge Graph

A multimodal retrieval-augmented generation (RAG) system that ingests data from YouTube, Twitter, and Instagram, stores embeddings in a vector database, and builds a knowledge graph using Gremlin.

## Features

- **Multimodal Ingestion**: YouTube videos, Twitter posts, Instagram content
- **Vector Search**: Semantic search using PostgreSQL with pgvector
- **Knowledge Graph**: Entity extraction and relationship mapping using Gremlin/Neptune
- **RESTful API**: FastAPI-based endpoints for ingestion and search
- **Scalable Architecture**: Worker-based ingestion with strategy pattern

## Project Structure

```
multimodal-rag-knowledgegraph/
├── config/
│   └── env/                    # Environment configuration files
│       ├── example.env         # Template environment file
│       ├── local.env           # Local development configuration
│       └── README.md           # Environment configuration documentation
├── infra/                      # Infrastructure configuration
│   ├── aws/                    # AWS-specific configurations
│   └── docker/                 # Docker configurations
├── src/                        # Application source code
├── tests/                      # Test files
└── README.md                   # This file
```

## Local Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd multimodal-rag-knowledgegraph
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Start Knowledge Graph (Gremlin Server) - Required

```bash
# Start local Gremlin Server using Docker
docker run -d -p 8182:8182 tinkerpop/gremlin-server:latest

# Verify connection
python test_neptune.py
```

### Step 3: Start Vector Database (PostgreSQL with pgvector) - Required

```bash
# Start PostgreSQL with pgvector using Docker Compose
docker compose -f infra/postgres/docker-compose.yml up -d

# Verify the database is running
docker ps
```

**Both components are required** - the system needs both the knowledge graph for entity relationships and the vector database for semantic search.

### Step 4: Configure Environment

Create a `.env` file based on the template in `config/env/`:

```bash
cp config/env/example.env .env
```

Update the `.env` file with your configuration:

```env
# App Environment
APP_ENV=dev

# Knowledge Graph (Gremlin Server)
KG_URI=ws://localhost:8182/gremlin

# Vector Database (PostgreSQL with pgvector)
VECTORDB_URI=postgresql://postgres:postgres@localhost:5432/vectordb

# Embedding Model
EMBEDDING_MODEL_NAME=text-embedding-3-small

# OpenAI API (optional for local dev - mock embeddings will be used if not set)
OPENAI_API_KEY=your-openai-api-key
```

For more details about environment configuration, see [`config/env/README.md`](config/env/README.md).

### Step 5: Start the Application

```bash
# Start the FastAPI server
source venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Test the Setup

```bash
# Test the API
curl http://localhost:8000/health

# Ingest a YouTube video
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]}'

# Search for content
curl "http://localhost:8000/search?query=trump&k=5"
```

### Step 7: View Knowledge Graph (Optional)

```bash
# Access Gremlin Console to explore the knowledge graph
docker exec -it <gremlin-container-id> bin/gremlin.sh
```

## Production Setup

### Prerequisites

- AWS Account with appropriate permissions
- Terraform (for infrastructure as code)
- Docker and Docker Compose
- Python 3.11+

### Step 1: Infrastructure Setup

**Both Knowledge Graph and Vector Database are required for production:**

#### Knowledge Graph: AWS Neptune

1. **Create Neptune Cluster**:
   ```bash
   # Using AWS CLI
   aws neptune create-db-cluster \
     --db-cluster-identifier my-neptune-cluster \
     --engine neptune \
     --engine-version 1.3.0.0 \
     --db-cluster-parameter-group-name default.neptune1.3 \
     --vpc-security-group-ids sg-xxxxxxxxx \
     --db-subnet-group-name my-db-subnet-group
   ```

2. **Create Neptune Instance**:
   ```bash
   aws neptune create-db-instance \
     --db-instance-identifier my-neptune-instance \
     --db-cluster-identifier my-neptune-cluster \
     --engine neptune \
     --db-instance-class db.r5.large
   ```

#### Vector Database: Managed PostgreSQL with pgvector

1. **Using AWS RDS with pgvector extension**:
   ```bash
   # Create RDS instance with PostgreSQL 14+
   aws rds create-db-instance \
     --db-instance-identifier my-vectordb \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --engine-version 14.10 \
     --master-username postgres \
     --master-user-password <secure-password> \
     --allocated-storage 20
   ```

2. **Enable pgvector extension**:
   ```sql
   -- Connect to your RDS instance and run:
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

**Note**: Both Neptune (for knowledge graph) and PostgreSQL with pgvector (for vector search) are essential components. The system requires both to function properly.

### Step 2: Application Deployment

#### Option A: Docker Compose (Production)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=prod
      - KG_URI=${KG_URI}
      - VECTORDB_URI=${VECTORDB_URI}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - worker

  worker:
    build: .
    command: python -m src.worker.ingest_worker
    environment:
      - APP_ENV=prod
      - KG_URI=${KG_URI}
      - VECTORDB_URI=${VECTORDB_URI}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

#### Option B: Kubernetes Deployment

1. **Create Kubernetes manifests**:
   ```yaml
   # api-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: multimodal-rag-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: multimodal-rag-api
     template:
       metadata:
         labels:
           app: multimodal-rag-api
       spec:
         containers:
         - name: api
           image: your-registry/multimodal-rag:latest
           ports:
           - containerPort: 8000
           env:
           - name: APP_ENV
             value: "prod"
           - name: KG_URI
             valueFrom:
               secretKeyRef:
                 name: app-secrets
                 key: kg-uri
           - name: VECTORDB_URI
             valueFrom:
               secretKeyRef:
                 name: app-secrets
                 key: vectordb-uri
   ```

### Step 3: Environment Configuration

Set production environment variables (**both are required**):

```bash
# Production environment
export APP_ENV=prod

# Knowledge Graph (Required)
export KG_URI=wss://your-neptune-cluster.cluster-xxxxx.region.neptune.amazonaws.com:8182/gremlin

# Vector Database (Required) 
export VECTORDB_URI=postgresql://username:password@your-rds-endpoint:5432/vectordb

# OpenAI API (Required for production embeddings)
export OPENAI_API_KEY=your-production-openai-key
```

**Important**: Both `KG_URI` and `VECTORDB_URI` must be configured. The system will not function properly if either component is missing.

### Step 4: Security and Monitoring

1. **Set up monitoring**:
   ```bash
   # Add Prometheus metrics
   pip install prometheus-client

   # Set up logging
   export LOG_LEVEL=INFO
   ```

2. **Configure secrets management**:
   ```bash
   # Use AWS Secrets Manager or similar
   aws secretsmanager create-secret \
     --name multimodal-rag-secrets \
     --secret-string '{"openai-api-key":"your-key","db-password":"your-password"}'
   ```

### Step 5: Deployment

```bash
# Build and deploy
docker build -t multimodal-rag:latest .
docker push your-registry/multimodal-rag:latest

# Deploy with Docker Compose
docker compose -f docker-compose.prod.yml up -d

# Or deploy to Kubernetes
kubectl apply -f k8s/
```

### Step 6: Verification

```bash
# Test production endpoints
curl https://your-api-domain.com/health

# Test ingestion
curl -X POST "https://your-api-domain.com/ingest" \
  -H "Content-Type: application/json" \
  -d '{"videos": ["https://www.youtube.com/watch?v=example"]}'

# Test search
curl "https://your-api-domain.com/search?query=trump&k=5"
```

## API Endpoints

For detailed API documentation with request/response examples, see [docs/api-reference.md](docs/api-reference.md).

### Health Check
- `GET /health` - Check system health

### Ingestion
- `POST /ingest` - Ingest content from various sources
  ```json
  {
    "videos": ["https://youtube.com/watch?v=..."],
    "twitter": ["query1", "query2"],
    "ig": ["https://instagram.com/p/..."]
  }
  ```

### Search
- `GET /search?query=<search_term>&k=<num_results>` - Search for content

### Knowledge Graph
- `GET /graph/entities` - Get all entities
- `GET /graph/entities/{entity_id}` - Get specific entity
- `GET /graph/search?query=<entity_name>` - Search entities

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
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI App   │
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

**Knowledge Graph (Gremlin/Neptune)**
- Extracts and stores named entities (people, places, organizations)
- Maps relationships between entities
- Enables graph-based queries and entity exploration

**Both components are required** - they serve different but complementary purposes in the multimodal RAG system.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/api/
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 