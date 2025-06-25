from abc import ABC, abstractmethod
from typing import Iterable, List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class VideoSegment(BaseModel):
    """Represents a temporal segment of a video with associated content"""
    start_time: float  # seconds from start
    end_time: float    # seconds from start
    text: str          # transcript for this segment
    confidence: float  # confidence score for the transcript
    entities: List[str] = []  # entities mentioned in this segment
    topics: List[str] = []    # topics discussed in this segment
    visual_entities: List[str] = []  # entities visible in this segment
    embedding: Optional[List[float]] = None  # vector embedding for this segment

class VideoContentItem(BaseModel):
    """Extended ContentItem specifically for video content"""
    id: str
    source: str
    url: HttpUrl
    author: str | None = None
    published_at: datetime
    title: str
    description: str
    duration: float  # video duration in seconds
    segments: List[VideoSegment] = []
    thumbnail_url: Optional[str] = None
    raw: dict

class ContentItem(BaseModel):
    id: str
    source: str
    url: HttpUrl
    author: str | None = None
    published_at: datetime
    text: str
    raw: dict

class ISource(ABC):
    @abstractmethod
    def fetch(self, query: str | list[str], since: datetime | None = None) -> Iterable[ContentItem]:
        ...

class IVideoSource(ABC):
    @abstractmethod
    def fetch_video(self, video_ids: List[str], since: datetime | None = None) -> Iterable[VideoContentItem]:
        ...
