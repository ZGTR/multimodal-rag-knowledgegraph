from fastapi import APIRouter
from src.kg.gremlin_client import GremlinKG
from src.bootstrap.logger import get_logger
from typing import Dict, Any

router = APIRouter()
logger = get_logger("api.graph")

@router.get("/graph")
def get_graph() -> Dict[str, Any]:
    try:
        kg = GremlinKG()
        graph = kg.get_whole_graph()
        return {
            "status": "success",
            "graph": graph
        }
    except Exception as e:
        logger.error(f"Failed to retrieve graph: {e}")
        return {
            "status": "error",
            "message": str(e),
            "graph": {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}
        } 