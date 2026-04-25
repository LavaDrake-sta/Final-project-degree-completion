from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from typing import List, Dict, Any
import re

class PIIDetector:
    """
    Core AI Layer using Microsoft Presidio for PII Detection locally.
    Includes custom recognizers for Israeli/Hebrew data.
    """
    
    def __init__(self):
        # Initialize Presidio registry and engine
        self.registry = RecognizerRegistry()
        self.registry.load_predefined_recognizers()
        
        # Add custom recognizers
        self._add_israeli_recognizers()
        
        # We use standard spacy model (en_core_web_sm is default in Presidio)
        # Note: For full Hebrew semantic support, a custom spacy model could be loaded here.
        # But for rule-based/regex, the default analyzer is sufficient.
        self.analyzer = AnalyzerEngine(registry=self.registry, supported_languages=["en", "he"])
        self.anonymizer = AnonymizerEngine()

    def _add_israeli_recognizers(self):
        """Add custom recognizers for Israeli PII."""
        # 1. Israeli ID Recognizer
        il_id_pattern = Pattern(name="israeli_id_pattern", regex=r'\b\d{9}\b', score=0.85)
        il_id_recognizer = PatternRecognizer(
            supported_entity="IL_ID", 
            patterns=[il_id_pattern], 
            context=["תעודת זהות", "ת.ז", "זהות", "id"]
        )
        self.registry.add_recognizer(il_id_recognizer)

        # 2. Israeli Phone Recognizer
        il_phone_pattern = Pattern(name="israeli_phone_pattern", regex=r'\b0[57]\d{1}-?\d{7}\b|\b0[23489]-?\d{7}\b', score=0.8)
        il_phone_recognizer = PatternRecognizer(
            supported_entity="IL_PHONE", 
            patterns=[il_phone_pattern],
            context=["טלפון", "נייד", "סלולרי", "phone", "mobile"]
        )
        self.registry.add_recognizer(il_phone_recognizer)
        
        # 3. Basic Hebrew Address Recognizer (Keywords based)
        address_pattern = Pattern(name="heb_address_pattern", regex=r'\b(?:רחוב|שדרות|שד\'|דרך|סמטת)\s+[א-ת]+\s+\d+\b', score=0.6)
        address_recognizer = PatternRecognizer(
            supported_entity="HEB_ADDRESS",
            patterns=[address_pattern],
            context=["כתובת", "מגורים", "מיקוד"]
        )
        self.registry.add_recognizer(address_recognizer)
        
        # 4. Hebrew Name Recognizer (Very basic heuristic)
        # This is a placeholder for a more advanced NLP model (e.g. AlephBERT).
        # We rely on existing heuristics for now.
        # name_pattern = Pattern(name="heb_name_pattern", regex=r'\b[א-ת]{2,}\s+[א-ת]{2,}\b', score=0.3)
        # name_recognizer = PatternRecognizer(supported_entity="HEB_NAME", patterns=[name_pattern])
        # self.registry.add_recognizer(name_recognizer)

    def analyze(self, text: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        Analyze text and return detected PII entities.
        Defaults to English but can process Hebrew if passed "he" (and if spacy model is installed).
        We will pass "en" by default because Presidio's default model is English, 
        but our custom regexes will still trigger.
        """
        if not text.strip():
            return []
            
        results = self.analyzer.analyze(text=text, entities=[], language="en")
        
        # Convert Presidio results to a list of dicts
        extracted_entities = []
        for res in results:
            extracted_entities.append({
                "entity_type": res.entity_type,
                "start": res.start,
                "end": res.end,
                "score": res.score,
                "text": text[res.start:res.end]
            })
            
        # Deduplicate and sort by start position
        extracted_entities = sorted(extracted_entities, key=lambda x: x["start"])
        return extracted_entities

    def anonymize(self, text: str, analyzer_results) -> str:
        """
        Anonymize text based on analyzer results.
        """
        if not text.strip() or not analyzer_results:
            return text
            
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results
        )
        return anonymized_result.text
    
    def future_nlp_hook(self, text: str):
        """
        Hook for future NLP model integration like AlephBERT.
        Currently returns an empty list.
        """
        return []
