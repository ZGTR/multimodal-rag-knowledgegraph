from .base import ISource, ContentItem
from typing import Iterable, List
from datetime import datetime, timezone

class InstagramSource(ISource):
    def fetch(self, urls: List[str], since: datetime | None = None) -> Iterable[ContentItem]:
        for u in urls:
            yield ContentItem(
                id=u.rstrip('/').split('/')[-1],
                source="instagram",
                url=u,
                author=None,
                published_at=datetime.now(timezone.utc),
                text="",
                raw={}
            )
