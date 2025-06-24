from pydantic import BaseModel
from datetime import datetime
from typing import List

class Node(BaseModel):
    id: str
    label: str
    properties: dict

class Edge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    properties: dict = {}
    timestamp: datetime | None = None

class KnowledgeGraphPacket(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
