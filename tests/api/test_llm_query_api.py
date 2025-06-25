import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_llm_query_basic():
    # This test assumes the vector store and OpenAI API are properly configured.
    payload = {
        "question": "List all the video splits where B-2 bombers were discussed.",
        "k": 3
    }
    response = client.post("/llm/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "relevant_splits" in data
    assert isinstance(data["relevant_splits"], list)
    # The answer should be a string
    assert isinstance(data["answer"], str)
    # The relevant_splits should be a list of dicts (may be empty if no data)
    for split in data["relevant_splits"]:
        assert "content" in split
        assert "split_number" in split 