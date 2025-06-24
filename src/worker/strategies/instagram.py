from src.ingest.instagram import InstagramSource
from .base import SourceStrategy

class InstagramStrategy(SourceStrategy):
    """Strategy for fetching Instagram content."""
    
    def fetch(self, ig_urls):
        """Fetch Instagram content for the given URLs."""
        return InstagramSource().fetch(ig_urls) 