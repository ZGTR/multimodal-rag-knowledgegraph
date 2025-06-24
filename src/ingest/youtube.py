from .base import ISource, ContentItem
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from datetime import datetime, timezone
from typing import Iterable, List

class YouTubeSource(ISource):
    def fetch(self, video_ids: List[str], since: datetime | None = None) -> Iterable[ContentItem]:
        for vid in video_ids:
            ydl = yt_dlp.YoutubeDL({'quiet': True})
            info = ydl.extract_info(f"https://youtu.be/{vid}", download=False)
            upload_dt = datetime.strptime(info['upload_date'], "%Y%m%d").replace(tzinfo=timezone.utc)
            if since and upload_dt < since:
                continue
            transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en'])
            text = " ".join([t['text'] for t in transcript])
            yield ContentItem(
                id=vid,
                source="youtube",
                url=f"https://youtu.be/{vid}",
                author=info.get('uploader'),
                published_at=upload_dt,
                text=text,
                raw=info
            )
