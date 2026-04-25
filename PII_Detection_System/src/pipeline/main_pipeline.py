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
        MIN_CONFIDENCE = 0.4  # סף ביטחון מינימלי - מתחת לזה לא נציג

        analyzer_results = self.detector.analyzer.analyze(text=original_text, entities=[], language="en")

        # Format entities
        raw_entities = []
        for res in analyzer_results:
            raw_entities.append({
                "entity_type": res.entity_type,
                "start": res.start,
                "end": res.end,
                "score": res.score,
                "text": original_text[res.start:res.end]
            })

        # ── סינון ביטחון נמוך ────────────────────────────────────────
        raw_entities = [e for e in raw_entities if e["score"] >= MIN_CONFIDENCE]

        # ── dedup: אותו span → שמור רק הציון הגבוה ביותר ───────────
        span_best: dict = {}
        for e in raw_entities:
            key = (e["start"], e["end"])
            if key not in span_best or e["score"] > span_best[key]["score"]:
                span_best[key] = e
        extracted_entities = sorted(span_best.values(), key=lambda x: x["start"])

        # שמור רק את ה-analyzer_results התואמים (לאנונימיזציה)
        keep_spans = {(e["start"], e["end"]) for e in extracted_entities}
        analyzer_results_filtered = [
            r for r in analyzer_results
            if (r.start, r.end) in keep_spans and r.score >= MIN_CONFIDENCE
        ]
        
        # 3. Decision Engine
        evaluation = self.decision_engine.evaluate(extracted_entities)
        
        # 4. Anonymize (using only the filtered & deduped results)
        anonymized_text = self.detector.anonymize(original_text, analyzer_results_filtered)
        
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
