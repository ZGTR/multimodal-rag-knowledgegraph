from typing import Iterable
from src.ingest.base import ContentItem

class SourceStrategy:
    """Base class for content source strategies."""
    
    def fetch(self, *args, **kwargs) -> Iterable[ContentItem]:
        """Fetch content from the source."""
        raise NotImplementedError 