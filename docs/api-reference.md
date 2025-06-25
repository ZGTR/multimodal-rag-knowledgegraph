# API Reference Documentation

This document provides comprehensive examples of expected outputs for all API endpoints in the Multimodal RAG Knowledge Graph system.

## Table of Contents

1. [Ingest Endpoint (`POST /ingest`)](#ingest-endpoint)
2. [Entities Endpoint (`GET /entities`)](#entities-endpoint)
3. [Graph Endpoint (`GET /graph`)](#graph-endpoint)
4. [Search Endpoint (`GET /search`)](#search-endpoint)
5. [Error Responses](#error-responses)
6. [Running Tests](#running-tests)

---

## Ingest Endpoint

**Endpoint:** `POST /ingest`  
**Purpose:** Queue data ingestion from various sources (YouTube, Twitter, Instagram)

### Request Format

```json
{
  "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
  "twitter": ["https://twitter.com/elonmusk/status/123456789"],
  "ig": ["https://www.instagram.com/p/ABC123/"]
}
```

### Expected Success Response

```json
{
  "status": "queued",
  "cmd": [
    "python",
    "-m",
    "src.worker.ingest_worker",
    "--videos",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "--twitter",
    "https://twitter.com/elonmusk/status/123456789",
    "--ig",
    "https://www.instagram.com/p/ABC123/"
  ]
}
```

### Test Cases

#### 1. YouTube Only
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]}'
```

**Expected Output:**
```json
{
  "status": "queued",
  "cmd": [
    "python",
    "-m",
    "src.worker.ingest_worker",
    "--videos",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  ]
}
```

#### 2. Empty Request
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Output:**
```json
{
  "status": "queued",
  "cmd": [
    "python",
    "-m",
    "src.worker.ingest_worker"
  ]
}
```

---

## Entities Endpoint

**Endpoint:** `GET /entities`  
**Purpose:** Retrieve all entities (nodes) from the knowledge graph

### Expected Success Response

```json
{
  "status": "success",
  "count": 12,
  "entities": [
    {
      "id": "youtube:dQw4w9WgXcQ",
      "label": null,
      "properties": {
        "node_type": "Content",
        "title": "Rick Astley - Never Gonna Give You Up",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "content": "We're no strangers to love...",
        "source": "youtube"
      }
    },
    {
      "id": "entity:rick_astley",
      "label": null,
      "properties": {
        "node_type": "Entity",
        "name": "Rick Astley",
        "type": "extracted"
      }
    },
    {
      "id": "entity:never_gonna_give_you_up",
      "label": null,
      "properties": {
        "node_type": "Entity",
        "name": "Never Gonna Give You Up",
        "type": "extracted"
      }
    }
  ]
}
```

### Empty Knowledge Graph Response

```json
{
  "status": "success",
  "count": 0,
  "entities": []
}
```

### Test Command

```bash
curl -s "http://localhost:8000/entities" | jq '.'
```

---

## Graph Endpoint

**Endpoint:** `GET /graph`  
**Purpose:** Retrieve the complete knowledge graph with nodes and edges

### Expected Success Response

```json
{
  "status": "success",
  "graph": {
    "nodes": [
      {
        "id": "youtube:dQw4w9WgXcQ",
        "label": null,
        "properties": {
          "node_type": "Content",
          "title": "Rick Astley - Never Gonna Give You Up",
          "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
      },
      {
        "id": "entity:rick_astley",
        "label": null,
        "properties": {
          "node_type": "Entity",
          "name": "Rick Astley",
          "type": "extracted"
        }
      },
      {
        "id": "entity:never_gonna_give_you_up",
        "label": null,
        "properties": {
          "node_type": "Entity",
          "name": "Never Gonna Give You Up",
          "type": "extracted"
        }
      }
    ],
    "edges": [
      {
        "id": "edge:youtube:dQw4w9WgXcQ:entity:rick_astley:contains_entity",
        "source": "youtube:dQw4w9WgXcQ",
        "target": "entity:rick_astley",
        "label": "contains_entity"
      },
      {
        "id": "edge:youtube:dQw4w9WgXcQ:entity:never_gonna_give_you_up:contains_entity",
        "source": "youtube:dQw4w9WgXcQ",
        "target": "entity:never_gonna_give_you_up",
        "label": "contains_entity"
      }
    ],
    "total_nodes": 3,
    "total_edges": 2
  }
}
```

### Empty Knowledge Graph Response

```json
{
  "status": "success",
  "graph": {
    "nodes": [],
    "edges": [],
    "total_nodes": 0,
    "total_edges": 0
  }
}
```

### Test Command

```bash
curl -s "http://localhost:8000/graph" | jq '.'
```

---

## Search Endpoint

**Endpoint:** `GET /search?query=<search_term>&k=<limit>`  
**Purpose:** Search for similar documents in the vector store

### Parameters

- `query` (required): Search term
- `k` (optional): Number of results to return (default: 5)

### Expected Success Response

```json
{
  "status": "success",
  "query": "AI machine learning",
  "count": 2,
  "results": [
    {
      "content": "This video discusses artificial intelligence and machine learning concepts in detail. We cover neural networks, deep learning, and practical applications.",
      "metadata": {
        "source": "youtube:dQw4w9WgXcQ",
        "title": "AI Tutorial - Machine Learning Basics",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "timestamp": "2024-01-15T10:30:00Z"
      }
    },
    {
      "content": "Another comprehensive guide to artificial intelligence and its applications in modern technology.",
      "metadata": {
        "source": "youtube:test123",
        "title": "Understanding AI",
        "url": "https://www.youtube.com/watch?v=test123",
        "timestamp": "2024-01-14T15:45:00Z"
      }
    }
  ]
}
```

### No Results Response

```json
{
  "status": "success",
  "query": "nonexistent term",
  "count": 0,
  "results": []
}
```

### Test Commands

#### Basic Search
```bash
curl -s "http://localhost:8000/search?query=AI&k=5" | jq '.'
```

#### Search with Custom Limit
```bash
curl -s "http://localhost:8000/search?query=machine%20learning&k=10" | jq '.'
```

#### Search with Default Parameters
```bash
curl -s "http://localhost:8000/search?query=test" | jq '.'
```

---

## Error Responses

### Validation Error (422)

**When:** Invalid request parameters

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "query"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### Server Error (500)

**When:** Internal server error

```json
{
  "status": "error",
  "message": "Connection failed",
  "entities": []
}
```

### Vector Store Unavailable

```json
{
  "status": "error",
  "message": "Vector store not available",
  "results": []
}
```

---

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/api/test_handler.py -v

# Run specific test class
pytest tests/api/test_handler.py::TestEntitiesEndpoint -v

# Run specific test method
pytest tests/api/test_handler.py::TestEntitiesEndpoint::test_get_entities_success -v
```

### Integration Tests

```bash
# Run integration tests (requires API server running)
python tests/test_api_integration.py

# Or with pytest
pytest tests/test_api_integration.py -v
```

### Manual API Testing

```bash
# Start the API server
python -m uvicorn src.api.handler:app --reload --host 0.0.0.0 --port 8000

# Test all endpoints
curl -s "http://localhost:8000/entities" | jq '.'
curl -s "http://localhost:8000/graph" | jq '.'
curl -s "http://localhost:8000/search?query=test&k=5" | jq '.'

# Test ingest
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]}' | jq '.'
```

---

## Test Coverage

The test suite covers:

### Unit Tests
- ✅ All API endpoints
- ✅ Success scenarios
- ✅ Error scenarios
- ✅ Edge cases
- ✅ Parameter validation
- ✅ Mock dependencies

### Integration Tests
- ✅ Real API server interaction
- ✅ End-to-end workflows
- ✅ Data persistence verification
- ✅ Actual response validation
- ✅ Performance testing

### Expected Test Results

When running the full test suite, you should see:

```
🚀 Starting API Integration Tests
==================================================
✅ API server is running and accessible

📥 Ingest Request:
   URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   Response: {
     "status": "queued",
     "cmd": ["python", "-m", "src.worker.ingest_worker", "--videos", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
   }
✅ Ingest request successful
⏳ Waiting for ingestion to complete...

📊 Entities Response:
   Status Code: 200
   Response: {
     "status": "success",
     "count": 12,
     "entities": [...]
   }
✅ Found 12 entities

🕸️  Graph Response:
   Status Code: 200
   Response: {
     "status": "success",
     "graph": {
       "nodes": [...],
       "edges": [...],
       "total_nodes": 12,
       "total_edges": 11
     }
   }
✅ Graph contains 12 nodes and 11 edges

🔍 Search Response (query='test', k=5):
   Status Code: 200
   Response: {
     "status": "success",
     "query": "test",
     "count": 1,
     "results": [...]
   }
✅ Found 1 results for query 'test'

==================================================
✅ All integration tests completed successfully!
```

This comprehensive test suite ensures that all API endpoints work correctly and return the expected outputs in all scenarios. 