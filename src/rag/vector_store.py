from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain.schema import Document
from src.bootstrap.settings import settings
from src.bootstrap.logger import get_logger
from typing import List, Optional
import json
import os

logger = get_logger("vector_store")

class InMemoryVectorStore:
    """Simple in-memory vector store for testing when PostgreSQL is not available."""
    
    def __init__(self):
        self.documents = []
        self.embeddings = None
        self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize embeddings."""
        try:
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model_name,
                openai_api_key=settings.openai_api_key
            )
            logger.info("In-memory vector store initialized with embeddings")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            self.embeddings = None
    
    def store_document(self, doc_id: str, text: str, metadata: dict = None) -> bool:
        """Store a document in memory."""
        try:
            doc_metadata = metadata or {}
            doc_metadata["doc_id"] = doc_id
            
            document = {
                "id": doc_id,
                "content": text,
                "metadata": doc_metadata
            }
            
            self.documents.append(document)
            logger.info(f"Stored document {doc_id} in memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document {doc_id}: {e}")
            return False
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """Simple search - returns all documents for now."""
        try:
            results = []
            for doc in self.documents[:k]:
                results.append(Document(
                    page_content=doc["content"],
                    metadata=doc["metadata"]
                ))
            return results
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return []

class VectorStore:
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.in_memory_store = None
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        """Initialize vector store with embeddings."""
        if settings.vectordb_uri is None:
            logger.warning("VECTORDB_URI not configured, using in-memory store")
            self.in_memory_store = InMemoryVectorStore()
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
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            logger.info("Falling back to in-memory store")
            self.vectorstore = None
            self.in_memory_store = InMemoryVectorStore()
    
    def store_document(self, doc_id: str, text: str, metadata: dict = None) -> bool:
        """Store a document in the vector store."""
        if self.vectorstore is not None:
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
        elif self.in_memory_store is not None:
            return self.in_memory_store.store_document(doc_id, text, metadata)
        else:
            logger.warning("No vector store available")
            return False
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        if self.vectorstore is not None:
            try:
                results = self.vectorstore.similarity_search(query, k=k)
                return results
            except Exception as e:
                logger.error(f"Failed to search vector store: {e}")
                return []
        elif self.in_memory_store is not None:
            return self.in_memory_store.search(query, k)
        else:
            logger.warning("No vector store available")
            return []

def get_vectorstore() -> Optional[VectorStore]:
    """Get vector store instance."""
    try:
        return VectorStore()
    except Exception as e:
        logger.error(f"Failed to create vector store: {e}")
        return None
