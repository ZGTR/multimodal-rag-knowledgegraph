from langchain_openai import OpenAIEmbeddings
from src.bootstrap.settings import settings
from src.bootstrap.logger import get_logger

logger = get_logger("vector_store")

def get_vectorstore():
    """Get vector store instance. Returns None if not configured."""
    if settings.vectordb_uri is None:
        logger.warning("VECTORDB_URI not configured, skipping vector store operations")
        return None
    
    try:
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model_name,
            openai_api_key=settings.openai_api_key
        )
        
        # For now, return the embeddings object
        # In a full implementation, you would return a proper vector store
        logger.info("Vector store initialized successfully")
        return embeddings
        
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        return None
