# Multimodal RAG with Knowledge Graph

This is a lightweight experimentation repo for multimodal retrieval-augmented generation (RAG) system that ingests data from YouTube, Twitter, and Instagram, stores embeddings in a vector database, and builds a knowledge graph using Gremlin.

This is not aimed to be prod-ready (though it can be). Albeit, we have to move the Neptune and Postgres deployments to other repos to correctly manage their IaC, add tests, follow DDD principles, etc. 

I may evolve this overtime. If you like to ask questions, please don't hesitate to send me an email: mohammadshakergtr@gmail.com

For everything deployment and local dev setup, please check [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md).

## Features

- **Multimodal Ingestion**: YouTube videos, Twitter posts, Instagram content
- **Vector Search**: Semantic search using PostgreSQL with pgvector
- **Knowledge Graph**: Entity extraction and relationship mapping using Gremlin/Neptune
- **RESTful API**: FastAPI-based endpoints for ingestion and search
- **Scalable Architecture**: Worker-based ingestion with strategy pattern
- **Infrastructure as Code**: Complete Terraform setup for AWS deployment
- **Multi-Environment Support**: Local, dev, staging, and production environments


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
│   └── local-dev.sh           # Local development setup script
├── src/                        # Application source code
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


## 🚀 Quick Start

### Local Development and Deployments
For detailed deployment instructions, see [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md).


### Test the Setup

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