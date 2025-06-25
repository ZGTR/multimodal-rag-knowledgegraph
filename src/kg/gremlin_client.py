from .schema import Node, Edge
from typing import List, Dict, Any, Optional
import os
import spacy
import logging
try:
    from gremlin_python.driver import client, serializer
    from gremlin_python.structure.graph import Graph
    from gremlin_python.process.graph_traversal import __
    from gremlin_python.process.traversal import T, P
    from gremlin_python.process.strategies import SubgraphStrategy
    import ssl
    import certifi
except ImportError:
    client = None

from ..bootstrap.settings import get_settings

logger = logging.getLogger(__name__)

class InMemoryKG:
    """Simple in-memory knowledge graph for testing when Gremlin server is not available."""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.nlp = self._load_nlp()
        print("In-memory knowledge graph initialized")
    
    def _load_nlp(self):
        """Load spaCy model for entity extraction."""
        try:
            return spacy.load("en_core_web_sm")
        except Exception as e:
            print(f"Failed to load spaCy model: {e}")
            return None
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            entities = [ent.text for ent in doc.ents]
            for chunk in doc.noun_chunks:
                if chunk.text not in entities:
                    entities.append(chunk.text)
            return list(set(entities))
        except Exception as e:
            print(f"Failed to extract entities: {e}")
            return []
    
    def upsert(self, nodes: List[Node], edges: List[Edge]):
        """Store nodes and edges in memory."""
        for node in nodes:
            # Check if node already exists
            existing_node = next((n for n in self.nodes if n.id == node.id), None)
            if existing_node:
                existing_node.properties.update(node.properties)
            else:
                self.nodes.append(node)
        
        for edge in edges:
            # Check if edge already exists
            existing_edge = next((e for e in self.edges if e.get("source") == edge["source"] and e.get("target") == edge["target"]), None)
            if not existing_edge:
                self.edges.append(edge)
        
        print(f"Stored {len(nodes)} nodes and {len(edges)} edges in memory")
    
    def store_content_with_entities(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Store content and extract entities, creating nodes and edges automatically."""
        # Create content node
        content_node = Node(
            id=doc_id,
            label="Content",
            properties={
                "text": content[:500] + "..." if len(content) > 500 else content,
                **metadata
            }
        )
        
        # Extract entities
        entities = self.extract_entities(content)
        entity_nodes = []
        edges = []
        
        for entity in entities[:10]:  # Limit to 10 entities per document
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
            
            # Create edge between content and entity
            edge = {
                "source": doc_id,
                "target": entity_id,
                "label": "contains_entity"
            }
            edges.append(edge)
        
        # Store all nodes and edges
        all_nodes = [content_node] + entity_nodes
        self.upsert(all_nodes, edges)
        print(f"Stored content {doc_id} with {len(entities)} entities")
    
    def get_all_entities(self) -> List[Dict[str, Any]]:
        """Retrieve all entities (nodes) from memory."""
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
        """Retrieve the complete knowledge graph from memory."""
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

class GremlinClient:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.graph = Graph()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gremlin client with Neptune-specific configuration"""
        try:
            # Use Neptune endpoint if configured, otherwise fallback to local
            if self.settings.NEPTUNE_CLUSTER_ENDPOINT and not self.settings.NEPTUNE_CLUSTER_ENDPOINT.startswith('test-'):
                endpoint = self.settings.NEPTUNE_CLUSTER_ENDPOINT
                port = self.settings.NEPTUNE_PORT
                use_ssl = self.settings.NEPTUNE_USE_SSL
                verify_ssl = self.settings.NEPTUNE_VERIFY_SSL
                
                # Neptune-specific SSL configuration
                if use_ssl:
                    ssl_context = ssl.create_default_context(cafile=certifi.where())
                    if not verify_ssl:
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE
                    
                    connection_string = f"wss://{endpoint}:{port}/gremlin"
                    self.client = client.Client(
                        connection_string,
                        'g',
                        ssl_context=ssl_context
                    )
                else:
                    connection_string = f"ws://{endpoint}:{port}/gremlin"
                    self.client = client.Client(connection_string, 'g')
                
                logger.info(f"Initialized Neptune client: {endpoint}:{port}")
            else:
                # Fallback to local Gremlin server
                connection_string = self.settings.kg_uri or "ws://localhost:8182/gremlin"
                self.client = client.Client(connection_string, 'g')
                logger.info(f"Initialized local Gremlin client: {connection_string}")
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            logger.error(f"Failed to initialize Gremlin client: {e}")
            self.client = None
    
    def _test_connection(self):
        """Test the connection to the graph database"""
        try:
            if self.client:
                # Simple query to test connection
                result = self.client.submit("g.V().limit(1)")
                result.all().result()  # This will raise an exception if connection fails
                logger.info("Gremlin client connection test successful")
        except Exception as e:
            logger.error(f"Gremlin client connection test failed: {e}")
            raise
    
    def _execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Gremlin query and return results"""
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

class GremlinKG:
    def __init__(self, endpoint: str | None = None):
        if client is None:
            raise ImportError("Install gremlinpython")
        try:
            self.gremlin_client = GremlinClient()
            if self.gremlin_client.client is None:
                raise Exception("GremlinClient failed to initialize (no connection to Neptune)")
            self.in_memory = False
            logger.info("GremlinKG initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Gremlin server: {e}")
            raise  # Do not fallback to in-memory KG

    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        if self.in_memory:
            return self.memory_kg.extract_entities(text)
        # For real Gremlin server, you might want to use a different approach
        # or call an external NLP service
        return []
    
    def store_content_with_entities(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Store content and extract entities, creating nodes and edges automatically."""
        if self.in_memory:
            self.memory_kg.store_content_with_entities(doc_id, content, metadata)
        else:
            # For real Gremlin server, implement similar logic
            pass

    def upsert(self, nodes: List[Node], edges: List[Edge]):
        if self.in_memory:
            self.memory_kg.upsert(nodes, edges)
        else:
            try:
                for n in nodes:
                    query = """
                    g.V().has('id', id).fold().coalesce(
                        unfold(), 
                        addV(label).property('id', id).property('type', type)
                    )
                    """
                    self.gremlin_client._execute_query(query, {"id": n.id, "label": n.label, "type": n.label})
                
                for e in edges:
                    query = """
                    g.V().has('id', source).as('s')
                    .V().has('id', target).as('t')
                    .coalesce(
                        inE(label).where(outV().hasId(source)),
                        addE(label).from('s').to('t')
                    )
                    """
                    self.gremlin_client._execute_query(query, {"source": e.source, "target": e.target, "label": e.label})
                
                logger.info(f"Upserted {len(nodes)} nodes and {len(edges)} edges")
            except Exception as e:
                logger.error(f"Failed to upsert to graph: {e}")
                raise

    def get_all_entities(self) -> List[Dict[str, Any]]:
        """Retrieve all entities (nodes) from the knowledge graph."""
        if self.in_memory:
            return self.memory_kg.get_all_entities()
        
        try:
            query = "g.V().valueMap(true).toList()"
            result = self.gremlin_client._execute_query(query)
            entities = []
            for item in result:
                entity = {
                    "id": item.get("id", [None])[0] if item.get("id") else None,
                    "label": item.get("label", [None])[0] if item.get("label") else None,
                    "properties": {k: v[0] if v else None for k, v in item.items() if k not in ["id", "label"]}
                }
                entities.append(entity)
            return entities
        except Exception as e:
            logger.error(f"Error retrieving entities: {e}")
            return []

    def get_whole_graph(self) -> Dict[str, Any]:
        """Retrieve the complete knowledge graph (nodes and edges)."""
        if self.in_memory:
            return self.memory_kg.get_whole_graph()
        
        try:
            # Get all nodes
            nodes_query = "g.V().valueMap(true).toList()"
            nodes_result = self.gremlin_client._execute_query(nodes_query)
            nodes = []
            for item in nodes_result:
                node = {
                    "id": item.get("id", [None])[0] if item.get("id") else None,
                    "label": item.get("label", [None])[0] if item.get("label") else None,
                    "properties": {k: v[0] if v else None for k, v in item.items() if k not in ["id", "label"]}
                }
                nodes.append(node)
            
            # Get all edges
            edges_query = "g.E().valueMap(true).toList()"
            edges_result = self.gremlin_client._execute_query(edges_query)
            edges = []
            for item in edges_result:
                edge = {
                    "id": item.get("id", [None])[0] if item.get("id") else None,
                    "label": item.get("label", [None])[0] if item.get("label") else None,
                    "outV": item.get("outV", [None])[0] if item.get("outV") else None,
                    "inV": item.get("inV", [None])[0] if item.get("inV") else None,
                    "properties": {k: v[0] if v else None for k, v in item.items() if k not in ["id", "label", "outV", "inV"]}
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
            return {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}
