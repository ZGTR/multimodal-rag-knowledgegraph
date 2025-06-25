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
    def extract_entities(self, text: str) -> List[str]:
        import re
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(words[:10])) 