from fastapi import APIRouter, HTTPException
from src.kg.gremlin_client import GremlinKG
from src.bootstrap.logger import get_logger
from typing import Dict, Any
import time

router = APIRouter()
logger = get_logger("api.entities")

@router.get("/entities")
def get_entities() -> Dict[str, Any]:
    start_time = time.time()
    try:
        logger.info("Retrieving entities from knowledge graph...")
        kg = GremlinKG()
        
        # Add timeout protection
        timeout = 10  # 10 seconds timeout
        if time.time() - start_time > timeout:
            logger.warning("Entities retrieval timed out")
            return {
                "status": "timeout",
                "message": "Entities retrieval timed out",
                "entities": []
            }
        
        entities = kg.get_all_entities()
        processing_time = time.time() - start_time
        
        logger.info(f"Retrieved {len(entities)} entities in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "count": len(entities),
            "processing_time": f"{processing_time:.2f}s",
            "entities": entities
        }
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Failed to retrieve entities after {processing_time:.2f}s: {e}")
        return {
            "status": "error",
            "message": str(e),
            "processing_time": f"{processing_time:.2f}s",
            "entities": []
        } 