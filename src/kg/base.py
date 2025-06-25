from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseEntityExtractor(ABC):
    @abstractmethod
    def extract_entities(self, text: str) -> List[str]:
        pass

class BaseKnowledgeGraph(ABC):
    @abstractmethod
    def upsert(self, nodes: List[Any], edges: List[Any]):
        pass

    @abstractmethod
    def store_content_with_entities(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        pass

    @abstractmethod
    def get_all_entities(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_whole_graph(self) -> Dict[str, Any]:
        pass 