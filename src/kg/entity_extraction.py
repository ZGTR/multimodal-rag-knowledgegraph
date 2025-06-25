import spacy
import logging
from typing import List
import time

logger = logging.getLogger(__name__)

class SpaCyEntityExtractor:
    def __init__(self):
        logger.info("Initializing SpaCyEntityExtractor")
        try:
            logger.info("Loading spaCy model: en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}")
            logger.info("Falling back to basic entity extraction")
            self.nlp = None

    def extract_entities(self, text: str) -> List[str]:
        if not self.nlp:
            logger.debug("SpaCy model not available, returning empty entity list")
            return []
        
        try:
            start_time = time.time()
            logger.debug(f"Extracting entities from text ({len(text)} chars)")
            
            doc = self.nlp(text)
            entities = [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT']]
            unique_entities = list(set(entities))
            
            extraction_time = time.time() - start_time
            logger.debug(f"Entity extraction completed in {extraction_time:.3f}s")
            logger.debug(f"Found {len(unique_entities)} unique entities: {unique_entities}")
            
            return unique_entities
        except Exception as e:
            logger.warning(f"Failed to extract entities: {e}")
            return []

class FallbackEntityExtractor:
    """Fallback entity extractor when spaCy is not available"""
    
    def __init__(self):
        logger.info("Using fallback entity extractor")
    
    def extract_entities(self, text: str) -> List[str]:
        """Simple fallback entity extraction using basic patterns"""
        logger.debug("Using basic fallback entity extraction")
        # This is a very basic fallback - in a real implementation you might use regex patterns
        # or other simple heuristics to extract entities
        logger.warning("Using basic fallback entity extraction")
        return [] 