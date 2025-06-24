import re
from src.ingest.youtube import YouTubeSource
from src.bootstrap.logger import get_logger
from .base import SourceStrategy

logger = get_logger("youtube_strategy")

def extract_youtube_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url

class YouTubeStrategy(SourceStrategy):
    """Strategy for fetching YouTube content."""
    
    def fetch(self, video_ids):
        """Fetch YouTube content for the given video IDs or URLs."""
        video_ids_clean = [extract_youtube_id(vid) for vid in video_ids]
        logger.info(f"Extracted video IDs: {video_ids_clean}")
        return YouTubeSource().fetch(video_ids_clean) 