import spacy
import logging
from typing import List

logger = logging.getLogger(__name__)

class SpaCyEntityExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}")
            self.nlp = None

    def extract_entities(self, text: str) -> List[str]:
        if not self.nlp:
            return []
        try:
            doc = self.nlp(text)
            entities = [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT']]
            return list(set(entities))
        except Exception as e:
            logger.warning(f"Failed to extract entities: {e}")
            return []

class FallbackEntityExtractor:
    """Fallback entity extractor when spaCy is not available"""
    
    def __init__(self):
        logger.info("Using fallback entity extractor")
    
    def extract_entities(self, text: str) -> List[str]:
        """Simple fallback entity extraction using basic patterns"""
        # This is a very basic fallback - in a real implementation you might use regex patterns
        # or other simple heuristics to extract entities
        logger.warning("Using basic fallback entity extraction")
        return [] 