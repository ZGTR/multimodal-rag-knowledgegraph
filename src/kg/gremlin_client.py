from .schema import Node, Edge
from typing import List
import os
try:
    from gremlin_python.driver import client, serializer
except ImportError:
    client = None

class GremlinKG:
    def __init__(self, endpoint: str | None = None):
        if client is None:
            raise ImportError("Install gremlinpython")
        endpoint = endpoint or os.getenv("KG_URI")
        self.client = client.Client(
            f"{endpoint}/gremlin", 'g', message_serializer=serializer.GraphSONSerializersV3d0())

    def upsert(self, nodes: List[Node], edges: List[Edge]):
        for n in nodes:
            self.client.submit(
                "g.V(id).fold().coalesce(unfold(), addV(label).property('id', id))",
                {"id": n.id, "label": n.label}
            )
        for e in edges:
            self.client.submit(
                "g.V(source).as('s').V(target).coalesce(inE(label).where(outV().hasId(source)), addE(label).from('s'))",
                {"source": e.source, "target": e.target, "label": e.label}
            )
