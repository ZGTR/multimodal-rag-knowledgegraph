from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain.schema import Document
from src.bootstrap.settings import settings
from src.bootstrap.logger import get_logger
from typing import List, Optional
import json
import os
import numpy as np
import time

logger = get_logger("vector_store")

class MockEmbeddings:
    """Simple mock embeddings for testing when OpenAI API is not available."""
    
    def __init__(self):
        self.dimension = 1536  # Same as OpenAI embeddings
        logger.info("Initializing MockEmbeddings for testing")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings."""
        logger.debug(f"Generating mock embeddings for {len(texts)} documents")
        embeddings = []
        for text in texts:
            # Generate a deterministic embedding based on text content
            np.random.seed(hash(text) % 2**32)
            embedding = np.random.rand(self.dimension).tolist()
            embeddings.append(embedding)
        logger.debug(f"Generated {len(embeddings)} mock embeddings")
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Generate mock embedding for a query."""
        logger.debug(f"Generating mock embedding for query: '{text[:50]}...'")
        np.random.seed(hash(text) % 2**32)
        embedding = np.random.rand(self.dimension).tolist()
        logger.debug("Mock embedding generated successfully")
        return embedding

class VectorStore:
    def __init__(self):
        logger.info("Initializing VectorStore")
        self.embeddings = None
        self.vectorstore = None
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        """Initialize vector store with embeddings."""
        if settings.vectordb_uri is None:
            logger.error("VECTORDB_URI not configured. Vector store not available.")
            return
        
        try:
            logger.info("Setting up OpenAI embeddings")
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model_name,
                openai_api_key=settings.openai_api_key
            )
            
            # Initialize PGVector
            logger.info("Initializing PGVector connection")
            self.vectorstore = PGVector(
                connection_string=settings.vectordb_uri,
                embedding_function=self.embeddings,
                collection_name="multimodal_rag"
            )
            
            logger.info("Vector store initialized successfully with PostgreSQL")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            logger.info("Falling back to mock embeddings for testing")
            self.embeddings = MockEmbeddings()
            self.vectorstore = None
    
    def store_document(self, doc_id: str, text: str, metadata: dict = None) -> bool:
        """Store a document in the vector store."""
        if self.vectorstore is None:
            logger.error("Vector store not available")
            return False
            
        try:
            start_time = time.time()
            logger.debug(f"Storing document: {doc_id} ({len(text)} chars)")
            
            doc_metadata = metadata or {}
            doc_metadata["doc_id"] = doc_id
            
            document = Document(
                page_content=text,
                metadata=doc_metadata
            )
            
            self.vectorstore.add_documents([document])
            
            storage_time = time.time() - start_time
            logger.debug(f"Document {doc_id} stored successfully in {storage_time:.2f}s")
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
            start_time = time.time()
            logger.debug(f"Searching for: '{query}' (k={k})")
            
            results = self.vectorstore.similarity_search(query, k=k)
            
            search_time = time.time() - start_time
            logger.debug(f"Search completed in {search_time:.2f}s, found {len(results)} results")
            
            return results
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return []

def get_vectorstore() -> Optional[VectorStore]:
    """Get vector store instance."""
    try:
        logger.info("Creating vector store instance")
        vectorstore = VectorStore()
        if vectorstore.vectorstore is None:
            logger.error("Vector store not properly initialized")
            return None
        logger.info("Vector store instance created successfully")
        return vectorstore
    except Exception as e:
        logger.error(f"Failed to create vector store: {e}")
        return None
