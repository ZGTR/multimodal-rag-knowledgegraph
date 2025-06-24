from .base import ISource, ContentItem
from datetime import datetime, timezone
from typing import Iterable, List
import os
try:
    import tweepy
except ImportError:
    tweepy = None

class TwitterSource(ISource):
    def __init__(self, bearer_token: str | None = None):
        if tweepy is None:
            raise ImportError("Please install tweepy")
        self.client = tweepy.Client(bearer_token or os.getenv("TWITTER_BEARER_TOKEN"))

    def fetch(self, query: str | List[str], since: datetime | None = None) -> Iterable[ContentItem]:
        q = query if isinstance(query, str) else " OR ".join(query)
        params = {"query": q, "tweet_fields": "created_at,author_id"}
        if since:
            params["start_time"] = since.astimezone(timezone.utc).isoformat()
        resp = self.client.search_recent_tweets(**params)
        if not resp.data:
            return []
        for tweet in resp.data:
            yield ContentItem(
                id=str(tweet.id),
                source="twitter",
                url=f"https://twitter.com/i/web/status/{tweet.id}",
                author=str(tweet.author_id),
                published_at=tweet.created_at,
                text=tweet.text,
                raw=tweet.data
            )
