from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import subprocess, sys
from src.bootstrap.logger import get_logger
from src.bootstrap.settings import settings
from src.kg.gremlin_client import GremlinKG
from src.rag.vector_store import get_vectorstore
from typing import List, Dict, Any

app = FastAPI()
logger = get_logger("api")

class IngestRequest(BaseModel):
    videos: list[str] | None = None
    twitter: list[str] | None = None
    ig: list[str] | None = None

@app.post("/ingest")
def ingest(req: IngestRequest, bg: BackgroundTasks):
    logger.info(f"Received ingest request: {req}")
    cmd = [sys.executable, "-m", "src.worker.ingest_worker"]
    if req.videos:
        cmd += ["--videos"] + req.videos
    if req.twitter:
        cmd += ["--twitter"] + req.twitter
    if req.ig:
        cmd += ["--ig"] + req.ig
    logger.info(f"Queuing background task: {cmd}")
    bg.add_task(subprocess.run, cmd)
    return {"status": "queued", "cmd": cmd}

@app.get("/entities")
def get_entities() -> Dict[str, Any]:
    """Retrieve all entities from the knowledge graph."""
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

@app.get("/graph")
def get_graph() -> Dict[str, Any]:
    """Retrieve the complete knowledge graph."""
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

@app.get("/search")
def search_documents(query: str, k: int = 5) -> Dict[str, Any]:
    """Search for similar documents in the vector store."""
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
