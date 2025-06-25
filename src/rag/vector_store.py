from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain.schema import Document
from src.bootstrap.settings import settings
from src.bootstrap.logger import get_logger
from typing import List, Optional
import json
import os
import numpy as np

logger = get_logger("vector_store")

class MockEmbeddings:
    """Simple mock embeddings for testing when OpenAI API is not available."""
    
    def __init__(self):
        self.dimension = 1536  # Same as OpenAI embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings."""
        embeddings = []
        for text in texts:
            # Generate a deterministic embedding based on text content
            np.random.seed(hash(text) % 2**32)
            embedding = np.random.rand(self.dimension).tolist()
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Generate mock embedding for a query."""
        np.random.seed(hash(text) % 2**32)
        return np.random.rand(self.dimension).tolist()

class VectorStore:
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        """Initialize vector store with embeddings."""
        if settings.vectordb_uri is None:
            logger.error("VECTORDB_URI not configured. Vector store not available.")
            return
        
        try:
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model_name,
                openai_api_key=settings.openai_api_key
            )
            
            # Initialize PGVector
            self.vectorstore = PGVector(
                connection_string=settings.vectordb_uri,
                embedding_function=self.embeddings,
                collection_name="multimodal_rag"
            )
            
            logger.info("Vector store initialized successfully with PostgreSQL")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.vectorstore = None
    
    def store_document(self, doc_id: str, text: str, metadata: dict = None) -> bool:
        """Store a document in the vector store."""
        if self.vectorstore is None:
            logger.error("Vector store not available")
            return False
            
        try:
            doc_metadata = metadata or {}
            doc_metadata["doc_id"] = doc_id
            
            document = Document(
                page_content=text,
                metadata=doc_metadata
            )
            
            self.vectorstore.add_documents([document])
            logger.info(f"Stored document {doc_id} in vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document {doc_id}: {e}")
            return False
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        if self.vectorstore is None:
            logger.error("Vector store not available")
            return []
            
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return results
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return []

def get_vectorstore() -> Optional[VectorStore]:
    """Get vector store instance."""
    try:
        vectorstore = VectorStore()
        if vectorstore.vectorstore is None:
            logger.error("Vector store not properly initialized")
            return None
        return vectorstore
    except Exception as e:
        logger.error(f"Failed to create vector store: {e}")
        return None
