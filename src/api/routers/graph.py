from fastapi import APIRouter, HTTPException
from src.kg.gremlin_client import GremlinKG
from src.bootstrap.logger import get_logger
from typing import Dict, Any
import time

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

@router.delete("")
def delete_all_graph_data() -> Dict[str, Any]:
    """Delete all nodes and edges from the knowledge graph."""
    start_time = time.time()
    try:
        logger.info("Deleting all nodes and edges from knowledge graph...")
        kg = GremlinKG()
        
        # Get counts before deletion
        before_node_count = kg.get_node_count()
        before_edge_count = kg.get_edge_count()
        
        # Delete all data
        success = kg.delete_all()
        
        processing_time = time.time() - start_time
        
        if success:
            logger.info(f"All data deleted from knowledge graph in {processing_time:.2f}s")
            return {
                "status": "success",
                "message": f"Successfully deleted {before_node_count} nodes and {before_edge_count} edges from knowledge graph",
                "deleted_nodes": before_node_count,
                "deleted_edges": before_edge_count,
                "processing_time": f"{processing_time:.2f}s"
            }
        else:
            logger.error(f"Failed to delete data from knowledge graph after {processing_time:.2f}s")
            return {
                "status": "error",
                "message": "Failed to delete data from knowledge graph",
                "deleted_nodes": 0,
                "deleted_edges": 0,
                "processing_time": f"{processing_time:.2f}s"
            }
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Delete operation failed after {processing_time:.2f}s: {e}")
        return {
            "status": "error",
            "message": str(e),
            "deleted_nodes": 0,
            "deleted_edges": 0,
            "processing_time": f"{processing_time:.2f}s"
        }

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