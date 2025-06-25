from .base import ISource, ContentItem, IVideoSource, VideoContentItem, VideoSegment
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from datetime import datetime, timezone
from typing import Iterable, List, Optional
from src.kg.entity_extraction import SpaCyEntityExtractor
from src.rag.vector_store import get_vectorstore
import logging
import time

logger = logging.getLogger(__name__)

class YouTubeVideoSource(IVideoSource):
    def __init__(self):
        logger.info("Initializing YouTubeVideoSource")
        self.entity_extractor = SpaCyEntityExtractor()
        self.vectorstore = get_vectorstore()
        logger.info("YouTubeVideoSource initialized successfully")
        
    def fetch_video(self, video_ids: List[str], since: datetime | None = None) -> Iterable[VideoContentItem]:
        logger.info(f"Starting video processing for {len(video_ids)} videos")
        
        for i, vid in enumerate(video_ids, 1):
            logger.info(f"[{i}/{len(video_ids)}] Processing video: {vid}")
            start_time = time.time()
            
            try:
                # Extract video metadata
                logger.info(f"[{vid}] Step 1/5: Extracting video metadata...")
                video_info = self._extract_video_info(vid)
                if since and video_info['upload_date'] < since:
                    logger.info(f"[{vid}] Skipping video - uploaded before {since}")
                    continue
                
                # Get transcript with timestamps
                logger.info(f"[{vid}] Step 2/5: Retrieving transcript...")
                transcript = self._get_transcript_with_timestamps(vid)
                
                # Process into temporal segments
                logger.info(f"[{vid}] Step 3/5: Processing temporal segments...")
                segments = self._process_segments(transcript, vid)
                
                # Create video content item
                logger.info(f"[{vid}] Step 4/5: Creating video content item...")
                video_item = VideoContentItem(
                    id=vid,
                    source="youtube",
                    url=f"https://youtu.be/{vid}",
                    author=video_info.get('uploader'),
                    published_at=video_info['upload_date'],
                    title=video_info.get('title', ''),
                    description=video_info.get('description', ''),
                    duration=video_info.get('duration', 0),
                    segments=segments,
                    thumbnail_url=video_info.get('thumbnail'),
                    raw=video_info
                )
                
                processing_time = time.time() - start_time
                logger.info(f"[{vid}] Step 5/5: Video processing completed in {processing_time:.2f}s")
                logger.info(f"[{vid}] Summary: {len(segments)} segments, {video_info.get('duration', 0):.1f}s duration")
                
                yield video_item
                
            except Exception as e:
                logger.error(f"[{vid}] Failed to process video: {e}")
                continue
    
    def _extract_video_info(self, video_id: str) -> dict:
        """Extract comprehensive video metadata"""
        logger.info(f"[{video_id}] Extracting metadata using yt-dlp...")
        
        try:
            ydl = yt_dlp.YoutubeDL({'quiet': True})
            info = ydl.extract_info(f"https://youtu.be/{video_id}", download=False)
            
            # Convert upload date to datetime
            upload_dt = datetime.strptime(info['upload_date'], "%Y%m%d").replace(tzinfo=timezone.utc)
            info['upload_date'] = upload_dt
            
            logger.info(f"[{video_id}] Metadata extracted: '{info.get('title', 'Unknown')}' by {info.get('uploader', 'Unknown')}")
            logger.info(f"[{video_id}] Duration: {info.get('duration', 0):.1f}s, Upload date: {upload_dt.strftime('%Y-%m-%d')}")
            
            return info
            
        except Exception as e:
            logger.error(f"[{video_id}] Failed to extract video metadata: {e}")
            raise
    
    def _get_transcript_with_timestamps(self, video_id: str) -> List[dict]:
        """Get transcript with precise timestamps"""
        logger.info(f"[{video_id}] Retrieving transcript from YouTube...")
        
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            logger.info(f"[{video_id}] Transcript retrieved: {len(transcript)} entries")
            
            # Log transcript statistics
            if transcript:
                total_duration = transcript[-1]['start'] + transcript[-1]['duration']
                avg_entry_length = sum(len(entry['text'].split()) for entry in transcript) / len(transcript)
                logger.info(f"[{video_id}] Transcript stats: {total_duration:.1f}s total, {avg_entry_length:.1f} words per entry")
            
            return transcript
            
        except Exception as e:
            logger.error(f"[{video_id}] Failed to get transcript: {e}")
            logger.warning(f"[{video_id}] Continuing without transcript")
            return []
    
    def _process_segments(self, transcript: List[dict], video_id: str) -> List[VideoSegment]:
        """Process transcript into temporal segments with entity extraction"""
        logger.info(f"[{video_id}] Processing {len(transcript)} transcript entries into segments...")
        
        segments = []
        
        # Group transcript entries into segments (e.g., 30-second chunks)
        segment_duration = 30.0  # seconds
        current_segment_start = 0.0
        current_segment_text = ""
        current_segment_entries = []
        
        logger.info(f"[{video_id}] Using {segment_duration}s segment duration")
        
        for i, entry in enumerate(transcript):
            start_time = entry['start']
            text = entry['text']
            
            # If this entry starts a new segment
            if start_time >= current_segment_start + segment_duration:
                # Save previous segment
                if current_segment_text:
                    logger.debug(f"[{video_id}] Creating segment {len(segments)+1}: {current_segment_start:.1f}s - {start_time:.1f}s")
                    segment = self._create_segment(
                        current_segment_start,
                        start_time,
                        current_segment_text,
                        video_id
                    )
                    segments.append(segment)
                
                # Start new segment
                current_segment_start = start_time
                current_segment_text = text
                current_segment_entries = [entry]
            else:
                # Add to current segment
                current_segment_text += " " + text
                current_segment_entries.append(entry)
        
        # Add final segment
        if current_segment_text:
            final_end_time = transcript[-1]['start'] + transcript[-1]['duration'] if transcript else current_segment_start + segment_duration
            logger.debug(f"[{video_id}] Creating final segment {len(segments)+1}: {current_segment_start:.1f}s - {final_end_time:.1f}s")
            segment = self._create_segment(
                current_segment_start,
                final_end_time,
                current_segment_text,
                video_id
            )
            segments.append(segment)
        
        logger.info(f"[{video_id}] Created {len(segments)} temporal segments")
        return segments
    
    def _create_segment(self, start_time: float, end_time: float, text: str, video_id: str) -> VideoSegment:
        """Create a video segment with entity extraction and embedding"""
        logger.debug(f"[{video_id}] Processing segment {start_time:.1f}s - {end_time:.1f}s ({len(text)} chars)")
        
        # Extract entities from text
        logger.debug(f"[{video_id}] Extracting entities from segment...")
        entities = self.entity_extractor.extract_entities(text)
        if entities:
            logger.debug(f"[{video_id}] Found entities: {', '.join(entities)}")
        
        # Generate embedding for the segment
        embedding = None
        if self.vectorstore and self.vectorstore.embeddings:
            try:
                logger.debug(f"[{video_id}] Generating embedding for segment...")
                embedding = self.vectorstore.embeddings.embed_query(text)
                logger.debug(f"[{video_id}] Embedding generated successfully")
            except Exception as e:
                logger.warning(f"[{video_id}] Failed to generate embedding for segment: {e}")
        
        # Store segment in vector store for search
        if self.vectorstore:
            try:
                metadata = {
                    "video_id": video_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "entities": entities,
                    "segment_type": "video_segment"
                }
                segment_id = f"{video_id}_{start_time}_{end_time}"
                logger.debug(f"[{video_id}] Storing segment in vector store: {segment_id}")
                self.vectorstore.store_document(segment_id, text, metadata)
                logger.debug(f"[{video_id}] Segment stored successfully")
            except Exception as e:
                logger.warning(f"[{video_id}] Failed to store segment in vector store: {e}")
        
        return VideoSegment(
            start_time=start_time,
            end_time=end_time,
            text=text,
            confidence=1.0,  # Could be enhanced with actual confidence scores
            entities=entities,
            topics=[],  # Could be enhanced with topic modeling
            visual_entities=[],  # Could be enhanced with computer vision
            embedding=embedding
        )

# Keep the original YouTubeSource for backward compatibility
class YouTubeSource(ISource):
    def fetch(self, video_ids: List[str], since: datetime | None = None) -> Iterable[ContentItem]:
        logger.info("Using legacy YouTubeSource for backward compatibility")
        video_source = YouTubeVideoSource()
        for video_item in video_source.fetch_video(video_ids, since):
            # Convert to legacy ContentItem format
            yield ContentItem(
                id=video_item.id,
                source=video_item.source,
                url=video_item.url,
                author=video_item.author,
                published_at=video_item.published_at,
                text=" ".join([seg.text for seg in video_item.segments]),
                raw=video_item.raw
            )
