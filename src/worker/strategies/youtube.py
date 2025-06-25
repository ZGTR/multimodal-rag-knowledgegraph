from .base import BaseIngestStrategy
from src.ingest.youtube import YouTubeSource
from src.ingest.base import ContentItem
from datetime import datetime
import re
from src.bootstrap.logger import get_logger

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

class YouTubeIngestStrategy(BaseIngestStrategy):
    def ingest(self, items: list[str]):
        video_ids = self.extract_video_ids(items)
        logger.info(f"Extracted video IDs: {video_ids}")
        yt_items = self.fetch_content(video_ids)
        for item in yt_items:
            self.process_item(item)

    def extract_video_ids(self, items: list[str]) -> list[str]:
        return [extract_youtube_id(vid) for vid in items]

    def fetch_content(self, video_ids: list[str]) -> list[ContentItem]:
        yt_source = YouTubeSource()
        return yt_source.fetch(video_ids)

    def process_item(self, item: ContentItem):
        doc_id = f"youtube:{item.id}"
        logger.info(f"[YT] Processing item: {doc_id}")
        
        if self.vectordb:
            self.store_in_vector_store(doc_id, item)
        
        if self.kg:
            self.store_in_kg(doc_id, item)
        
        logger.info(f"[YT] Finished item: {doc_id}")

    def store_in_vector_store(self, doc_id: str, item: ContentItem):
        metadata = {
            "source": item.source,
            "id": item.id,
            "title": str(getattr(item, 'title', '')),
            "url": str(getattr(item, 'url', '')),
            "timestamp": str(getattr(item, 'timestamp', datetime.now().isoformat()))
        }
        self.vectordb.store_document(doc_id, item.text, metadata)

    def store_in_kg(self, doc_id: str, item: ContentItem):
        metadata = {
            "source": item.source,
            "title": str(getattr(item, 'title', '')),
            "url": str(getattr(item, 'url', '')),
            "timestamp": str(getattr(item, 'timestamp', datetime.now().isoformat()))
        }
        self.kg.store_content_with_entities(doc_id, item.text, metadata)
        logger.info(f"[YT] Stored in KG: {doc_id}") 