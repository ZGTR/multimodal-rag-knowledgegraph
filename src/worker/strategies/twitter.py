from datetime import datetime
from src.ingest.twitter import TwitterSource
from .base import SourceStrategy

class TwitterStrategy(SourceStrategy):
    """Strategy for fetching Twitter content."""
    
    def fetch(self, query, since: datetime):
        """Fetch Twitter content for the given query."""
        return TwitterSource().fetch(query, since=since) 