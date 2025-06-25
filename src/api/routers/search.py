from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional, Tuple
from src.rag.temporal_search import get_temporal_search_service, TemporalSearchQuery, TemporalSearchResult
from src.bootstrap.logger import get_logger

router = APIRouter(prefix="/search", tags=["search"])
logger = get_logger("api.search")

class GeneralSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    include_temporal: bool = False

@router.get("/")
def search(query: str = Query(..., description="Search query"), 
           k: int = Query(5, description="Number of results")) -> List[dict]:
    """
    General search endpoint for backward compatibility
    
    This endpoint performs general search across all content types.
    For temporal video search, use the /temporal endpoints.
    """
    logger.info(f"General search request: {query}")
    
    service = get_temporal_search_service()
    if not service:
        return []
    
    # Convert to temporal search
    temporal_query = TemporalSearchQuery(query=query, max_results=k)
    results = service.search_entities(temporal_query)
    
    # Convert to legacy format
    legacy_results = []
    for result in results:
        legacy_results.append({
            "content": result.matched_text,
            "metadata": {
                "video_id": result.video_id,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "entities": result.entities,
                "topics": result.topics,
                "source": "temporal_search"
            }
        })
    
    return legacy_results

@router.post("/general")
def general_search(request: GeneralSearchRequest) -> List[dict]:
    """
    General search endpoint with enhanced options
    
    Performs search across all content types with optional temporal information.
    """
    logger.info(f"General search request: {request}")
    
    service = get_temporal_search_service()
    if not service:
        return []
    
    # Convert to temporal search
    temporal_query = TemporalSearchQuery(query=request.query, max_results=request.max_results)
    results = service.search_entities(temporal_query)
    
    # Convert to general format
    search_results = []
    for result in results:
        search_result = {
            "content": result.matched_text,
            "metadata": {
                "video_id": result.video_id,
                "entities": result.entities,
                "topics": result.topics,
                "source": "temporal_search"
            }
        }
        
        # Include temporal information if requested
        if request.include_temporal:
            search_result["metadata"]["temporal"] = {
                "start_time": result.start_time,
                "end_time": result.end_time,
                "video_url": result.video_url
            }
        
        search_results.append(search_result)
    
    return search_results

@router.get("/suggestions")
def get_search_suggestions(query: str = Query(..., description="Base query for suggestions"),
                          max_suggestions: int = Query(10, description="Maximum number of suggestions")):
    """
    Get search suggestions based on available content
    
    Returns suggested search terms based on entities and topics found in the system.
    """
    logger.info(f"Search suggestions request for: {query}")
    
    # This is a placeholder - in a real implementation, you would
    # query the vector store or knowledge graph for suggestions
    suggestions = [
        f"{query} artificial intelligence",
        f"{query} machine learning",
        f"{query} data science",
        f"{query} neural networks",
        f"{query} deep learning"
    ]
    
    return {
        "query": query,
        "suggestions": suggestions[:max_suggestions]
    }

@router.get("/stats")
def get_search_stats():
    """
    Get search statistics
    
    Returns metrics about search performance and usage.
    """
    logger.info("Search stats request")
    
    # This is a placeholder - in a real implementation, you would
    # query the database for actual statistics
    stats = {
        "total_searches": 0,
        "searches_today": 0,
        "most_popular_queries": [],
        "avg_results_per_query": 0,
        "search_success_rate": 0.0
    }
    
    return stats 