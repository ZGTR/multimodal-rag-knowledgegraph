from typing import Iterable
from src.ingest.base import ContentItem
from abc import ABC, abstractmethod
from typing import List, Optional

class SourceStrategy:
    """Base class for content source strategies."""
    
    def fetch(self, *args, **kwargs) -> Iterable[ContentItem]:
        """Fetch content from the source."""
        raise NotImplementedError 

class BaseIngestStrategy(ABC):
    def __init__(self, vectordb=None, kg=None):
        self.vectordb = vectordb
        self.kg = kg

    @abstractmethod
    def ingest(self, items: Optional[List[str]] = None):
        """Ingest data from the source, process, and store."""
        pass 