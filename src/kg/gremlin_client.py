from .schema import Node, Edge
from .base import BaseKnowledgeGraph
from .entity_extraction import SpaCyEntityExtractor, FallbackEntityExtractor
from .utils import get_first
from typing import List, Dict, Any
import logging
try:
    from gremlin_python.driver import client, serializer
    from gremlin_python.structure.graph import Graph
except ImportError:
    client = None
from ..bootstrap.settings import get_settings

logger = logging.getLogger(__name__)

class GremlinClient:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            endpoint = self.settings.kg_uri or "ws://localhost:8182/gremlin"
            logger.info(f"Attempting to connect to Gremlin at: {endpoint}")
            self.client = client.Client(endpoint, 'g')
            self._test_connection()
            logger.info(f"Successfully initialized Gremlin client: {endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize Gremlin client: {e}")
            raise Exception(f"Gremlin client not initialized: {e}")
    
    def _test_connection(self):
        if self.client:
            try:
                result = self.client.submit("g.V().limit(1)")
                result.all().result()
            except Exception as e:
                logger.error(f"Gremlin connection test failed: {e}")
                raise Exception(f"Gremlin connection test failed: {e}")
    
    def _execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        if not self.client:
            raise Exception("Gremlin client not initialized")
        
        try:
            if parameters:
                result = self.client.submit(query, parameters)
            else:
                result = self.client.submit(query)
            return result.all().result()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

class GremlinKG(BaseKnowledgeGraph):
    def __init__(self):
        if client is None:
            raise ImportError("Install gremlinpython")
        
        self.gremlin_client = GremlinClient()
        self.entity_extractor = SpaCyEntityExtractor()
        logger.info("GremlinKG initialized successfully")

    def extract_entities(self, text: str) -> List[str]:
        entities = self.entity_extractor.extract_entities(text)
        if not entities:
            entities = FallbackEntityExtractor().extract_entities(text)
        return entities

    def upsert(self, nodes: List[Node], edges: List[Edge]):
        for n in nodes:
            query = """
            g.V().has('node_id', node_id).fold().coalesce(
                unfold(), 
                addV(node_label).property('node_id', node_id).property('node_type', node_type)
            )
            """
            self.gremlin_client._execute_query(query, {
                "node_id": n.id, 
                "node_label": n.label, 
                "node_type": n.label
            })
        
        for e in edges:
            query = """
            g.V().has('node_id', source_id).as('s')
            .V().has('node_id', target_id).as('t')
            .coalesce(
                inE(edge_label).where(outV().has('node_id', source_id)),
                addE(edge_label).from('s').to('t')
            )
            """
            self.gremlin_client._execute_query(query, {
                "source_id": e.source, 
                "target_id": e.target, 
                "edge_label": e.label
            })
        logger.info(f"Upserted {len(nodes)} nodes and {len(edges)} edges")

    def store_content_with_entities(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        content_node = Node(
            id=doc_id,
            label="Content",
            properties={
                "type": "youtube_video",
                "content": content[:500],
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
        logger.info(f"Stored content {doc_id} with {len(entities)} entities in Gremlin")

    def get_all_entities(self) -> List[Dict[str, Any]]:
        try:
            query = "g.V().valueMap(true).toList()"
            result = self.gremlin_client._execute_query(query)
            entities = []
            for item in result:
                entity = {
                    "id": get_first(item.get("node_id")),
                    "label": get_first(item.get("label")),
                    "properties": {k: get_first(v) for k, v in item.items() if k not in ["node_id", "label"]}
                }
                entities.append(entity)
            return entities
        except Exception as e:
            logger.error(f"Error retrieving entities: {e}")
            raise

    def get_whole_graph(self) -> Dict[str, Any]:
        try:
            nodes_query = "g.V().valueMap(true).toList()"
            nodes_result = self.gremlin_client._execute_query(nodes_query)
            nodes = []
            for item in nodes_result:
                node = {
                    "id": get_first(item.get("node_id")),
                    "label": get_first(item.get("label")),
                    "properties": {k: get_first(v) for k, v in item.items() if k not in ["node_id", "label"]}
                }
                nodes.append(node)
            
            edges_query = "g.E().valueMap(true).toList()"
            edges_result = self.gremlin_client._execute_query(edges_query)
            edges = []
            for item in edges_result:
                edge = {
                    "id": get_first(item.get("id")),
                    "label": get_first(item.get("label")),
                    "outV": get_first(item.get("outV")),
                    "inV": get_first(item.get("inV")),
                    "properties": {k: get_first(v) for k, v in item.items() if k not in ["id", "label", "outV", "inV"]}
                }
                edges.append(edge)
            
            return {
                "nodes": nodes,
                "edges": edges,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        except Exception as e:
            logger.error(f"Error retrieving whole graph: {e}")
            raise

    def get_facts_for_entity(self, entity_name: str) -> list[str]:
        """Return a list of fact strings about the entity from the KG."""
        facts = []
        try:
            # Find the entity node by name
            entity_id = f"entity:{entity_name.lower().replace(' ', '_')}"
            query = "g.V().has('node_id', entity_id).valueMap(true).toList()"
            result = self.gremlin_client._execute_query(query, {"entity_id": entity_id})
            if result:
                entity = result[0]
                label = entity.get("label", ["Entity"])[0]
                name = entity.get("name", [entity_name])[0]
                # Add properties as facts
                for k, v in entity.items():
                    if k not in ["node_id", "label", "name"]:
                        facts.append(f"{name} ({label}) has {k}: {v[0] if isinstance(v, list) else v}")
                facts.append(f"{name} is a {label} node in the knowledge graph.")
            # Find outgoing edges (relationships)
            edge_query = """
            g.V().has('node_id', entity_id).bothE().as('e').otherV().as('v').select('e','v').toList()
            """
            edge_results = self.gremlin_client._execute_query(edge_query, {"entity_id": entity_id})
            for edge in edge_results:
                e = edge.get("e", {})
                v = edge.get("v", {})
                edge_label = e.get("label", ["related"])[0] if isinstance(e.get("label"), list) else e.get("label", "related")
                target_label = v.get("label", ["Node"])[0] if isinstance(v.get("label"), list) else v.get("label", "Node")
                target_name = v.get("name", [v.get("node_id", ["unknown"])[0]])[0] if isinstance(v.get("name"), list) else v.get("name", v.get("node_id", "unknown"))
                facts.append(f"{entity_name} {edge_label} {target_label}: {target_name}")
        except Exception as e:
            logger.warning(f"Could not get facts for entity '{entity_name}': {e}")
        return facts
