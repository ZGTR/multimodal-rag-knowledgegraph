from .base import BaseIngestStrategy
from src.ingest.youtube import YouTubeVideoSource, YouTubeSource
from src.ingest.base import ContentItem, VideoContentItem
from datetime import datetime
import re
from src.bootstrap.logger import get_logger
import time

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
        logger.info(f"Starting YouTube ingestion for {len(items)} items")
        start_time = time.time()
        
        video_ids = self.extract_video_ids(items)
        logger.info(f"Extracted video IDs: {video_ids}")
        
        # Use new temporal video processing
        logger.info("Processing videos with temporal video processing...")
        video_items = self.fetch_video_content(video_ids)
        for i, item in enumerate(video_items, 1):
            logger.info(f"[{i}/{len(video_ids)}] Processing video item: {item.id}")
            self.process_video_item(item)
        
        # Also process with legacy method for backward compatibility
        logger.info("Processing videos with legacy method for backward compatibility...")
        legacy_items = self.fetch_legacy_content(video_ids)
        for i, item in enumerate(legacy_items, 1):
            logger.info(f"[{i}/{len(video_ids)}] Processing legacy item: {item.id}")
            self.process_legacy_item(item)
        
        total_time = time.time() - start_time
        logger.info(f"YouTube ingestion completed in {total_time:.2f}s")

    def extract_video_ids(self, items: list[str]) -> list[str]:
        logger.info(f"Extracting video IDs from {len(items)} items")
        video_ids = [extract_youtube_id(vid) for vid in items]
        logger.info(f"Extracted {len(video_ids)} video IDs: {video_ids}")
        return video_ids

    def fetch_video_content(self, video_ids: list[str]) -> list[VideoContentItem]:
        """Fetch video content with temporal segments"""
        logger.info(f"Fetching video content for {len(video_ids)} videos")
        yt_source = YouTubeVideoSource()
        video_items = list(yt_source.fetch_video(video_ids))
        logger.info(f"Fetched {len(video_items)} video items")
        return video_items

    def fetch_legacy_content(self, video_ids: list[str]) -> list[ContentItem]:
        """Fetch content using legacy method for backward compatibility"""
        logger.info(f"Fetching legacy content for {len(video_ids)} videos")
        yt_source = YouTubeSource()
        legacy_items = list(yt_source.fetch(video_ids))
        logger.info(f"Fetched {len(legacy_items)} legacy items")
        return legacy_items

    def process_video_item(self, item: VideoContentItem):
        """Process video item with temporal segments"""
        doc_id = f"youtube:{item.id}"
        logger.info(f"[{doc_id}] Processing video item with {len(item.segments)} segments")
        start_time = time.time()
        
        # Store video metadata
        if self.vectordb:
            logger.info(f"[{doc_id}] Storing video metadata in vector store...")
            self.store_video_metadata(doc_id, item)
        
        if self.kg:
            logger.info(f"[{doc_id}] Storing video in knowledge graph...")
            self.store_video_in_kg(doc_id, item)
        
        # Process each segment
        logger.info(f"[{doc_id}] Processing {len(item.segments)} segments...")
        for i, segment in enumerate(item.segments, 1):
            segment_id = f"{doc_id}:segment:{i}"
            logger.debug(f"[{doc_id}] Processing segment {i}/{len(item.segments)}: {segment.start_time:.1f}s - {segment.end_time:.1f}s")
            self.process_video_segment(segment_id, item, segment)
        
        processing_time = time.time() - start_time
        logger.info(f"[{doc_id}] Video item processing completed in {processing_time:.2f}s")

    def process_video_segment(self, segment_id: str, video_item: VideoContentItem, segment):
        """Process individual video segment"""
        logger.debug(f"[{segment_id}] Processing segment ({segment.start_time:.1f}s - {segment.end_time:.1f}s)")
        
        if self.vectordb:
            logger.debug(f"[{segment_id}] Storing segment in vector store...")
            self.store_segment_in_vector_store(segment_id, video_item, segment)
        
        if self.kg:
            logger.debug(f"[{segment_id}] Storing segment in knowledge graph...")
            self.store_segment_in_kg(segment_id, video_item, segment)

    def store_video_metadata(self, doc_id: str, item: VideoContentItem):
        """Store video-level metadata"""
        logger.debug(f"[{doc_id}] Storing video metadata...")
        metadata = {
            "source": item.source,
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "url": str(item.url),
            "author": item.author,
            "duration": item.duration,
            "thumbnail_url": item.thumbnail_url,
            "published_at": item.published_at.isoformat(),
            "content_type": "video",
            "segment_count": len(item.segments)
        }
        
        try:
            self.vectordb.store_document(doc_id, item.title + " " + item.description, metadata)
            logger.debug(f"[{doc_id}] Video metadata stored successfully")
        except Exception as e:
            logger.error(f"[{doc_id}] Failed to store video metadata: {e}")

    def store_segment_in_vector_store(self, segment_id: str, video_item: VideoContentItem, segment):
        """Store video segment in vector store"""
        logger.debug(f"[{segment_id}] Storing segment in vector store...")
        metadata = {
            "source": video_item.source,
            "video_id": video_item.id,
            "video_title": video_item.title,
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "entities": segment.entities,
            "topics": segment.topics,
            "visual_entities": segment.visual_entities,
            "confidence": segment.confidence,
            "segment_type": "video_segment",
            "url": str(video_item.url),
            "author": video_item.author,
            "published_at": video_item.published_at.isoformat()
        }
        
        try:
            self.vectordb.store_document(segment_id, segment.text, metadata)
            logger.debug(f"[{segment_id}] Segment stored in vector store successfully")
        except Exception as e:
            logger.error(f"[{segment_id}] Failed to store segment in vector store: {e}")

    def store_video_in_kg(self, doc_id: str, item: VideoContentItem):
        """Store video in knowledge graph"""
        logger.debug(f"[{doc_id}] Storing video in knowledge graph...")
        metadata = {
            "source": item.source,
            "title": item.title,
            "description": item.description,
            "url": str(item.url),
            "author": item.author,
            "duration": item.duration,
            "published_at": item.published_at.isoformat(),
            "content_type": "video"
        }
        # Store video-level content
        full_text = item.title + " " + item.description + " " + " ".join([seg.text for seg in item.segments])
        
        try:
            self.kg.store_content_with_entities(doc_id, full_text, metadata)
            logger.debug(f"[{doc_id}] Video stored in knowledge graph successfully")
        except Exception as e:
            logger.error(f"[{doc_id}] Failed to store video in knowledge graph: {e}")

    def store_segment_in_kg(self, segment_id: str, video_item: VideoContentItem, segment):
        """Store video segment in knowledge graph"""
        logger.debug(f"[{segment_id}] Storing segment in knowledge graph...")
        metadata = {
            "source": video_item.source,
            "video_id": video_item.id,
            "video_title": video_item.title,
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "entities": segment.entities,
            "topics": segment.topics,
            "confidence": segment.confidence,
            "segment_type": "video_segment",
            "url": str(video_item.url),
            "author": video_item.author,
            "published_at": video_item.published_at.isoformat()
        }
        
        try:
            self.kg.store_content_with_entities(segment_id, segment.text, metadata)
            logger.debug(f"[{segment_id}] Segment stored in knowledge graph successfully")
        except Exception as e:
            logger.error(f"[{segment_id}] Failed to store segment in knowledge graph: {e}")

    def process_legacy_item(self, item: ContentItem):
        """Process item using legacy method for backward compatibility"""
        doc_id = f"youtube:legacy:{item.id}"
        logger.info(f"[{doc_id}] Processing legacy item")
        
        if self.vectordb:
            logger.debug(f"[{doc_id}] Storing legacy item in vector store...")
            self.store_in_vector_store(doc_id, item)
        
        if self.kg:
            logger.debug(f"[{doc_id}] Storing legacy item in knowledge graph...")
            self.store_in_kg(doc_id, item)
        
        logger.info(f"[{doc_id}] Legacy item processing completed")

    def store_in_vector_store(self, doc_id: str, item: ContentItem):
        metadata = {
            "source": item.source,
            "id": item.id,
            "title": str(getattr(item, 'title', '')),
            "url": str(getattr(item, 'url', '')),
            "timestamp": str(getattr(item, 'timestamp', datetime.now().isoformat())),
            "content_type": "legacy"
        }
        
        try:
            self.vectordb.store_document(doc_id, item.text, metadata)
            logger.debug(f"[{doc_id}] Legacy item stored in vector store successfully")
        except Exception as e:
            logger.error(f"[{doc_id}] Failed to store legacy item in vector store: {e}")

    def store_in_kg(self, doc_id: str, item: ContentItem):
        metadata = {
            "source": item.source,
            "title": str(getattr(item, 'title', '')),
            "url": str(getattr(item, 'url', '')),
            "timestamp": str(getattr(item, 'timestamp', datetime.now().isoformat())),
            "content_type": "legacy"
        }
        
        try:
            self.kg.store_content_with_entities(doc_id, item.text, metadata)
            logger.debug(f"[{doc_id}] Legacy item stored in knowledge graph successfully")
        except Exception as e:
            logger.error(f"[{doc_id}] Failed to store legacy item in knowledge graph: {e}") 