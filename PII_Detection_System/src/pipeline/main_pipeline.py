"""
Main Pipeline — PII Detection System
אורכסטרטור ראשי לזיהוי PII עם AI.

שיפורים:
  - Overlap dedup (בנוסף ל-exact-span)
  - Context keyword post-processing
  - לוגים לכל שלב
"""

import json
from typing import Dict, Any

from .file_handler import FileHandler
from .pii_detector import PIIDetector
from .decision_engine import DecisionEngine

try:
    from src.logger_config import get_logger
except ImportError:
    try:
        from logger_config import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger(name)

logger = get_logger("PII.Pipeline.Main")


class PIIPipeline:
    """
    אורכסטרטור ראשי לזיהוי PII מבוסס AI.
    """

    def __init__(self):
        logger.info("🚀 אתחול PIIPipeline...")
        self.file_handler   = FileHandler()
        self.detector       = PIIDetector()
        self.decision_engine = DecisionEngine()
        logger.info("✅ PIIPipeline מוכן")

    def process_file(
        self,
        file_path: str = None,
        file_bytes: bytes = None,
        filename: str = None
    ) -> Dict[str, Any]:
        """
        עיבוד קובץ: חילוץ טקסט → זיהוי PII → הערכת סיכון → אנונימיזציה.
        """
        logger.info(f"📂 מתחיל עיבוד קובץ: {filename or file_path or 'bytes'}")

        # ── 1. חילוץ טקסט ─────────────────────────────────────────
        extraction_result = self.file_handler.process_file(
            file_path=file_path, file_bytes=file_bytes, filename=filename
        )
        if not extraction_result["success"]:
            error_msg = extraction_result.get("error", "Failed to extract text.")
            logger.error(f"❌ חילוץ טקסט נכשל: {error_msg}")
            return {"success": False, "error": error_msg}

        original_text = extraction_result["text"]
        file_type     = extraction_result.get("file_type", "unknown")
        logger.info(f"📄 טקסט חולץ | {len(original_text)} תווים | סוג: {file_type}")

        # ── 2. זיהוי PII (Presidio + Context) ────────────────────
        MIN_CONFIDENCE = 0.4

        # Presidio analyzer results (לאנונימיזציה)
        presidio_results = self.detector.analyzer.analyze(
            text=original_text, entities=[], language="en"
        )

        # Format Presidio
        presidio_entities = [{
            "entity_type": r.entity_type,
            "start": r.start,
            "end": r.end,
            "score": r.score,
            "text": original_text[r.start:r.end],
            "source": "presidio"
        } for r in presidio_results if r.score >= MIN_CONFIDENCE]

        # Context keywords
        context_entities = self.detector.detect_context_keywords(original_text)
        context_entities = [e for e in context_entities if e["score"] >= MIN_CONFIDENCE]

        logger.info(
            f"🔍 Presidio raw: {len(presidio_entities)} | "
            f"Context: {len(context_entities)}"
        )

        # ── 3. Overlap Dedup ──────────────────────────────────────
        all_entities = presidio_entities + context_entities
        extracted_entities = PIIDetector._overlap_dedup(all_entities)

        logger.info(f"✅ לאחר dedup: {len(extracted_entities)} ישויות ייחודיות")

        # ── 4. שמור רק Presidio results תואמים לאנונימיזציה ───────
        keep_spans = {(e["start"], e["end"]) for e in extracted_entities if e.get("source") == "presidio"}
        analyzer_results_filtered = [
            r for r in presidio_results
            if (r.start, r.end) in keep_spans and r.score >= MIN_CONFIDENCE
        ]

        # ── 5. הערכת סיכון ────────────────────────────────────────
        evaluation = self.decision_engine.evaluate(extracted_entities)
        logger.info(f"⚠️ הערכת סיכון: {evaluation['risk_level']} | {evaluation['summary']}")

        # ── 6. אנונימיזציה ────────────────────────────────────────
        anonymized_text = self.detector.anonymize(original_text, analyzer_results_filtered)
        logger.info(f"🔒 אנונימיזציה הושלמה | {len(anonymized_text)} תווים")

        # ── 7. דוח סופי ──────────────────────────────────────────
        report = {
            "success":              True,
            "file_type":            file_type,
            "original_text_length": len(original_text),
            "risk_evaluation":      evaluation,
            "entities":             extracted_entities,
            "anonymized_text":      anonymized_text,
        }
        return report

    def generate_report_json(self, report: Dict[str, Any]) -> str:
        """ייצוא דוח כ-JSON"""
        return json.dumps(report, indent=2, ensure_ascii=False)
