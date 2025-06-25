from fastapi import APIRouter, HTTPException
from src.kg.gremlin_client import GremlinKG
from src.bootstrap.logger import get_logger
from typing import Dict, Any

router = APIRouter(prefix="/graph", tags=["graph"])
logger = get_logger("api.graph")

@router.get("")
def get_graph():
    try:
        kg = GremlinKG()
        graph = kg.get_whole_graph()
        return graph
    except Exception as e:
        logger.error(f"Failed to get graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get graph: {e}")

@router.get("/debug")
def debug_graph():
    """Return the number of nodes and a sample of nodes for debugging."""
    try:
        kg = GremlinKG()
        graph = kg.get_whole_graph()
        nodes = graph.get("nodes", [])
        return {
            "node_count": len(nodes),
            "sample_nodes": nodes[:5],
            "total_edges": graph.get("total_edges", 0)
        }
    except Exception as e:
        logger.error(f"Failed to debug graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to debug graph: {e}")

@router.get("/graph")
def get_graph_old() -> Dict[str, Any]:
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