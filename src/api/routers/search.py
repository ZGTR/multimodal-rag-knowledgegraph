from fastapi import APIRouter
from src.rag.vector_store import get_vectorstore
from src.bootstrap.logger import get_logger
from typing import Dict, Any

router = APIRouter()
logger = get_logger("api.search")

@router.get("/search")
def search_documents(query: str, k: int = 5) -> Dict[str, Any]:
    try:
        vectordb = get_vectorstore()
        if vectordb is None:
            return {
                "status": "error",
                "message": "Vector store not available",
                "results": []
            }
        results = vectordb.search(query, k=k)
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        return {
            "status": "success",
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Failed to search documents: {e}")
        return {
            "status": "error",
            "message": str(e),
            "results": []
        } 