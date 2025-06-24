import pytest
from pydantic import ValidationError
from src.api.handler import IngestRequest

class TestIngestRequest:
    """Test cases for the IngestRequest model"""
    
    def test_valid_request_with_all_fields(self):
        """Test valid request with all fields populated"""
        data = {
            "videos": ["https://www.youtube.com/watch?v=test"],
            "twitter": ["https://twitter.com/test/status/123"],
            "ig": ["https://www.instagram.com/p/ABC123/"]
        }
        
        request = IngestRequest(**data)
        assert request.videos == data["videos"]
        assert request.twitter == data["twitter"]
        assert request.ig == data["ig"]
    
    def test_valid_request_with_partial_fields(self):
        """Test valid request with only some fields populated"""
        data = {
            "videos": ["https://www.youtube.com/watch?v=test"]
        }
        
        request = IngestRequest(**data)
        assert request.videos == data["videos"]
        assert request.twitter is None
        assert request.ig is None
    
    def test_valid_request_with_empty_lists(self):
        """Test valid request with empty lists"""
        data = {
            "videos": [],
            "twitter": [],
            "ig": []
        }
        
        request = IngestRequest(**data)
        assert request.videos == []
        assert request.twitter == []
        assert request.ig == []
    
    def test_valid_request_with_none_values(self):
        """Test valid request with None values"""
        data = {
            "videos": None,
            "twitter": None,
            "ig": None
        }
        
        request = IngestRequest(**data)
        assert request.videos is None
        assert request.twitter is None
        assert request.ig is None
    
    def test_valid_request_with_no_fields(self):
        """Test valid request with no fields (all defaults)"""
        request = IngestRequest()
        assert request.videos is None
        assert request.twitter is None
        assert request.ig is None
    
    def test_invalid_request_with_wrong_types(self):
        """Test invalid request with wrong data types"""
        data = {
            "videos": "not_a_list",
            "twitter": 123,
            "ig": {"not": "a_list"}
        }
        
        with pytest.raises(ValidationError):
            IngestRequest(**data)
    
    def test_invalid_request_with_wrong_list_types(self):
        """Test invalid request with lists containing wrong types"""
        data = {
            "videos": [123, "https://www.youtube.com/watch?v=test"],
            "twitter": ["https://twitter.com/test/status/123", 456],
            "ig": [True, "https://www.instagram.com/p/ABC123/"]
        }
        
        with pytest.raises(ValidationError):
            IngestRequest(**data)
    
    def test_request_with_mixed_valid_and_invalid_urls(self):
        """Test request with a mix of valid and invalid URL formats"""
        data = {
            "videos": ["https://www.youtube.com/watch?v=test", "invalid_url"],
            "twitter": ["https://twitter.com/test/status/123", "not_a_twitter_url"],
            "ig": ["https://www.instagram.com/p/ABC123/", "random_string"]
        }
        
        # This should be valid since we're not validating URL formats in the model
        request = IngestRequest(**data)
        assert request.videos == data["videos"]
        assert request.twitter == data["twitter"]
        assert request.ig == data["ig"]
    
    def test_request_serialization(self):
        """Test that the model can be serialized to dict"""
        data = {
            "videos": ["https://www.youtube.com/watch?v=test"],
            "twitter": ["https://twitter.com/test/status/123"],
            "ig": ["https://www.instagram.com/p/ABC123/"]
        }
        
        request = IngestRequest(**data)
        serialized = request.model_dump()
        
        assert serialized["videos"] == data["videos"]
        assert serialized["twitter"] == data["twitter"]
        assert serialized["ig"] == data["ig"]
    
    def test_request_json_serialization(self):
        """Test that the model can be serialized to JSON"""
        data = {
            "videos": ["https://www.youtube.com/watch?v=test"],
            "twitter": ["https://twitter.com/test/status/123"],
            "ig": ["https://www.instagram.com/p/ABC123/"]
        }
        
        request = IngestRequest(**data)
        json_str = request.model_dump_json()
        
        # Should be valid JSON
        import json
        parsed = json.loads(json_str)
        assert parsed["videos"] == data["videos"]
        assert parsed["twitter"] == data["twitter"]
        assert parsed["ig"] == data["ig"] 