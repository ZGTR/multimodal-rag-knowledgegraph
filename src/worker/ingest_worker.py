import argparse
import re
from datetime import datetime, timezone, timedelta
from typing import Iterable, List, Optional
from src.ingest.twitter import TwitterSource
from src.ingest.youtube import YouTubeSource
from src.ingest.instagram import InstagramSource
from src.rag.vector_store import get_vectorstore
from src.bootstrap.settings import settings
from src.kg.gremlin_client import GremlinKG, Node
from src.ingest.base import ContentItem
from src.bootstrap.logger import get_logger

logger = get_logger("ingest_worker")

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

class SourceStrategy:
    def fetch(self, *args, **kwargs) -> Iterable[ContentItem]:
        raise NotImplementedError

class TwitterStrategy(SourceStrategy):
    def fetch(self, query, since):
        return TwitterSource().fetch(query, since=since)

class YouTubeStrategy(SourceStrategy):
    def fetch(self, video_ids):
        video_ids_clean = [extract_youtube_id(vid) for vid in video_ids]
        logger.info(f"Extracted video IDs: {video_ids_clean}")
        return YouTubeSource().fetch(video_ids_clean)

class InstagramStrategy(SourceStrategy):
    def fetch(self, ig_urls):
        return InstagramSource().fetch(ig_urls)

class IngestWorker:
    def __init__(self, videos: Optional[List[str]] = None, twitter: Optional[List[str]] = None, ig: Optional[List[str]] = None):
        self.videos = videos
        self.twitter = twitter
        self.ig = ig
        self.vectordb = get_vectorstore()
        self.kg = self._init_kg()
        self.strategies = {
            'twitter': TwitterStrategy(),
            'youtube': YouTubeStrategy(),
            'instagram': InstagramStrategy(),
        }

    def _init_kg(self):
        try:
            kg = GremlinKG()
            logger.info("Knowledge graph initialized successfully")
            return kg
        except Exception as e:
            logger.warning(f"Failed to initialize knowledge graph: {e}")
            return None

    def process_items(self, items: Iterable[ContentItem], source: str):
        for item in items:
            try:
                doc_id = f"{item.source}:{item.id}"
                logger.info(f"[TASK] Start processing item: {doc_id}")
                if self.vectordb is not None:
                    try:
                        logger.info(f"[TASK] Would store text in vector store: {item.text[:100]}...")
                    except Exception as e:
                        logger.error(f"[TASK][ABORT] Failed to store in vector store: {e}")
                if self.kg is not None:
                    try:
                        self.kg.upsert(nodes=[Node(id=doc_id, label=item.source, properties=item.model_dump())], edges=[])
                        logger.info(f"[TASK] Stored in knowledge graph: {doc_id}")
                    except Exception as e:
                        logger.error(f"[TASK][ABORT] Failed to store in knowledge graph: {e}")
                logger.info(f"[TASK] Finished processing item: {doc_id}")
            except Exception as e:
                logger.error(f"[TASK][ABORT] Failed to process item {getattr(item, 'id', 'unknown')}: {e}")

    def run(self):
        logger.info("[JOB] IngestWorker started with params: videos=%s, twitter=%s, ig=%s", self.videos, self.twitter, self.ig)
        since = datetime.now(timezone.utc) - timedelta(days=7)
        job_success = True
        if self.twitter:
            logger.info("[TASK] Twitter ingestion started")
            try:
                items = self.strategies['twitter'].fetch(self.twitter, since=since)
                self.process_items(items, source="twitter")
                logger.info("[TASK] Twitter ingestion finished")
            except Exception as e:
                logger.error(f"[TASK][ABORT] Twitter ingestion failed: {e}")
                job_success = False
        if self.videos:
            logger.info("[TASK] YouTube ingestion started")
            try:
                items = self.strategies['youtube'].fetch(self.videos)
                self.process_items(items, source="youtube")
                logger.info("[TASK] YouTube ingestion finished")
            except Exception as e:
                logger.error(f"[TASK][ABORT] YouTube ingestion failed: {e}")
                job_success = False
        if self.ig:
            logger.info("[TASK] Instagram ingestion started")
            try:
                items = self.strategies['instagram'].fetch(self.ig)
                self.process_items(items, source="instagram")
                logger.info("[TASK] Instagram ingestion finished")
            except Exception as e:
                logger.error(f"[TASK][ABORT] Instagram ingestion failed: {e}")
                job_success = False
        if job_success:
            logger.info("[JOB] IngestWorker finished successfully")
        else:
            logger.error("[JOB][ABORT] IngestWorker finished with errors")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--videos", nargs="*", help="YouTube video IDs or URLs")
    parser.add_argument("--twitter", nargs="+", help="Twitter query terms")
    parser.add_argument("--ig", nargs="*", help="Instagram post URLs")
    args = parser.parse_args()
    worker = IngestWorker(videos=args.videos, twitter=args.twitter, ig=args.ig)
    worker.run()
