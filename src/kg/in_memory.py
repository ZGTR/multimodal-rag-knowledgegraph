from .base import BaseKnowledgeGraph
from .entity_extraction import SpaCyEntityExtractor, FallbackEntityExtractor
from .schema import Node, Edge
from typing import List, Dict, Any

class InMemoryKG(BaseKnowledgeGraph):
    def __init__(self):
        self.nodes = []
        self.edges = []
        try:
            self.entity_extractor = SpaCyEntityExtractor()
        except Exception:
            self.entity_extractor = FallbackEntityExtractor()
        print("In-memory knowledge graph initialized")

    def extract_entities(self, text: str) -> List[str]:
        entities = self.entity_extractor.extract_entities(text)
        if not entities:
            entities = FallbackEntityExtractor().extract_entities(text)
        return entities

    def upsert(self, nodes: List[Node], edges: List[Edge]):
        for node in nodes:
            existing_node = next((n for n in self.nodes if n.id == node.id), None)
            if existing_node:
                existing_node.properties.update(node.properties)
            else:
                self.nodes.append(node)
        for edge in edges:
            existing_edge = next((e for e in self.edges if e.get("source") == edge["source"] and e.get("target") == edge["target"]), None)
            if not existing_edge:
                self.edges.append(edge)
        print(f"Stored {len(nodes)} nodes and {len(edges)} edges in memory")

    def store_content_with_entities(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        content_node = Node(
            id=doc_id,
            label="Content",
            properties={
                "text": content[:500] + "..." if len(content) > 500 else content,
                **metadata
            }
        )
        entities = self.extract_entities(content)
        entity_nodes = []
        edges = []
        for entity in entities[:10]:
            entity_id = f"entity:{entity.lower().replace(' ', '_')}"
            entity_node = Node(
                id=entity_id,
                label="Entity",
                properties={
                    "name": entity,
                    "type": "extracted"
                }
            )
            entity_nodes.append(entity_node)
            edge = Edge(
                id=f"edge:{doc_id}:{entity_id}:contains_entity",
                source=doc_id,
                target=entity_id,
                label="contains_entity"
            )
            edges.append(edge)
        all_nodes = [content_node] + entity_nodes
        self.upsert(all_nodes, edges)
        print(f"Stored content {doc_id} with {len(entities)} entities")

    def get_all_entities(self) -> List[Dict[str, Any]]:
        entities = []
        for node in self.nodes:
            entity = {
                "id": node.id,
                "label": node.label,
                "properties": node.properties
            }
            entities.append(entity)
        return entities

    def get_whole_graph(self) -> Dict[str, Any]:
        nodes = []
        for node in self.nodes:
            nodes.append({
                "id": node.id,
                "label": node.label,
                "properties": node.properties
            })
        edges = []
        for edge in self.edges:
            edges.append({
                "id": f"edge_{len(edges)}",
                "label": edge.get("label", "related"),
                "outV": edge.get("source"),
                "inV": edge.get("target"),
                "properties": {}
            })
        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        } 