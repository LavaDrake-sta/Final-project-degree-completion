import json
from typing import Dict, Any

from .file_handler import FileHandler
from .pii_detector import PIIDetector
from .decision_engine import DecisionEngine

class PIIPipeline:
    """
    Main orchestrator for the local AI-based PII detection pipeline.
    """
    def __init__(self):
        self.file_handler = FileHandler()
        self.detector = PIIDetector()
        self.decision_engine = DecisionEngine()

    def process_file(self, file_path: str = None, file_bytes: bytes = None, filename: str = None) -> Dict[str, Any]:
        """
        Processes a file, extracts text, detects PII, evaluates risk, and anonymizes.
        """
        # 1. Extract Text
        extraction_result = self.file_handler.process_file(file_path=file_path, file_bytes=file_bytes, filename=filename)
        
        if not extraction_result["success"]:
            return {
                "success": False,
                "error": extraction_result.get("error", "Failed to extract text.")
            }
            
        original_text = extraction_result["text"]
        file_type = extraction_result.get("file_type", "unknown")
        
        # 2. Analyze Text for PII
        # We need the raw Analyzer objects for the Anonymizer, so we call Presidio directly here too,
        # or we can modify pii_detector to return both. Let's do that cleanly.
        analyzer_results = self.detector.analyzer.analyze(text=original_text, entities=[], language="en")
        
        # Format entities for the report
        extracted_entities = []
        for res in analyzer_results:
            extracted_entities.append({
                "entity_type": res.entity_type,
                "start": res.start,
                "end": res.end,
                "score": res.score,
                "text": original_text[res.start:res.end]
            })
        extracted_entities = sorted(extracted_entities, key=lambda x: x["start"])
        
        # 3. Decision Engine
        evaluation = self.decision_engine.evaluate(extracted_entities)
        
        # 4. Anonymize
        anonymized_text = self.detector.anonymize(original_text, analyzer_results)
        
        # 5. Build Report
        report = {
            "success": True,
            "file_type": file_type,
            "original_text_length": len(original_text),
            "risk_evaluation": evaluation,
            "entities": extracted_entities,
            "anonymized_text": anonymized_text
        }
        
        return report

    def generate_report_json(self, report: Dict[str, Any]) -> str:
        """Helper to generate a formatted JSON report (excluding the large text blocks if needed)."""
        report_copy = dict(report)
        # Optional: remove full text from JSON report if it's too large
        # report_copy.pop("anonymized_text", None)
        return json.dumps(report_copy, indent=2, ensure_ascii=False)
