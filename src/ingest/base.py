from abc import ABC, abstractmethod
from typing import Iterable
from pydantic import BaseModel, HttpUrl
from datetime import datetime

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
