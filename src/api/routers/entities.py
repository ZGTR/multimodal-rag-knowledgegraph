from fastapi import APIRouter
from src.kg.gremlin_client import GremlinKG
from src.bootstrap.logger import get_logger
from typing import Dict, Any

router = APIRouter()
logger = get_logger("api.entities")

@router.get("/entities")
def get_entities() -> Dict[str, Any]:
    try:
        kg = GremlinKG()
        entities = kg.get_all_entities()
        return {
            "status": "success",
            "count": len(entities),
            "entities": entities
        }
    except Exception as e:
        logger.error(f"Failed to retrieve entities: {e}")
        return {
            "status": "error",
            "message": str(e),
            "entities": []
        } 