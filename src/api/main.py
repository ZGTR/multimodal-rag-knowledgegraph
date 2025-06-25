from fastapi import FastAPI
from src.api.routers.ingest import router as ingest_router
from src.api.routers.entities import router as entities_router
from src.api.routers.graph import router as graph_router
from src.api.routers.search import router as search_router

app = FastAPI()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Multimodal RAG Knowledge Graph API is running"}

app.include_router(ingest_router)
app.include_router(entities_router)
app.include_router(graph_router)
app.include_router(search_router) 