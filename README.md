# Multimodal RAG with Knowledge Graph

A multimodal retrieval-augmented generation (RAG) system that ingests data from YouTube, Twitter, and Instagram, stores embeddings in a vector database, and builds a knowledge graph using Gremlin.

## Features

- **Multimodal Ingestion**: YouTube videos, Twitter posts, Instagram content
- **Vector Search**: Semantic search using PostgreSQL with pgvector
- **Knowledge Graph**: Entity extraction and relationship mapping using Gremlin/Neptune
- **RESTful API**: FastAPI-based endpoints for ingestion and search
- **Scalable Architecture**: Worker-based ingestion with strategy pattern
- **Infrastructure as Code**: Complete Terraform setup for AWS deployment
- **Multi-Environment Support**: Local, dev, staging, and production environments

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
│   │   ├── neptune_setup.sh    # Manual Neptune setup script
│   │   └── neptune_cleanup.sh  # Neptune cleanup script
│   ├── postgres/               # PostgreSQL Docker configuration
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
├── src/                        # Application source code
├── tests/                      # Test files
├── DEPLOYMENT_GUIDE.md         # Comprehensive deployment guide
└── README.md                   # This file
```

## 🚀 Quick Start

### Local Development (Recommended for Development)

```bash
# Clone and setup
git clone <repository-url>
cd multimodal-rag-knowledgegraph

# Setup local environment (Docker services)
./infra/terraform/scripts/deploy.sh local setup

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp config/env/example.env .env
# Edit .env with your configuration

# Start the application
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### AWS Deployment (Recommended for Production)

```bash
# Deploy to development environment
./infra/terraform/scripts/deploy.sh dev apply

# Deploy to production environment
./infra/terraform/scripts/deploy.sh prod apply
```

For detailed deployment instructions, see [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md).

## Prerequisites

### Local Development
- Python 3.11+
- Docker and Docker Compose
- Git

### AWS Deployment
- AWS Account with appropriate permissions
- Terraform (>= 1.0)
- AWS CLI configured

## Local Development Setup

### Step 1: Start Required Services

The system requires both a knowledge graph and vector database:

```bash
# Start local Gremlin Server (Knowledge Graph)
docker run -d -p 8182:8182 tinkerpop/gremlin-server:latest

# Start PostgreSQL with pgvector (Vector Database)
docker compose -f infra/postgres/docker-compose.yml up -d
```

### Step 2: Configure Environment

Create a `.env` file based on the template:

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

### Step 3: Test the Setup

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