"""
PII Detector — AI Pipeline Layer (Presidio)
פרויקט גמר - זיהוי מידע אישי רגיש

שיפורים:
  - Overlap-based dedup (לא רק exact-span)
  - Context recognizers ישראליים מורחבים
  - ContextualKeywordRecognizer: keyword → value
  - לוגים לכל שלב
"""

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from typing import List, Dict, Any
import re

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

logger = get_logger("PII.Pipeline.Detector")


class PIIDetector:
    """
    Core AI Layer using Microsoft Presidio for PII Detection locally.
    Includes custom recognizers for Israeli/Hebrew data.
    """

    def __init__(self):
        logger.info("PIIDetector init (Presidio)...")

        # Try spaCy models in order: lg -> sm -> simple fallback
        nlp_engine = None
        for model_name in ["en_core_web_lg", "en_core_web_sm", "en_core_web_md"]:
            try:
                import spacy
                spacy.load(model_name)  # verify it's installed before telling Presidio
                nlp_configuration = {
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": model_name}],
                }
                nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
                logger.info(f"spaCy model loaded: {model_name}")
                break
            except Exception:
                logger.warning(f"spaCy model not available: {model_name}")

        if nlp_engine is None:
            # Final fallback — use Presidio's built-in simple NLP (no spaCy)
            try:
                from presidio_analyzer.nlp_engine import SpacyNlpEngine
                nlp_engine = SpacyNlpEngine()
                logger.warning("Using simple NLP engine (no spaCy model) - reduced accuracy")
            except Exception as e:
                logger.error(f"Could not create any NLP engine: {e}")
                raise RuntimeError("No NLP engine available for Presidio") from e

        self.registry = RecognizerRegistry()
        self.registry.load_predefined_recognizers(languages=["en"])

        self._add_israeli_recognizers()

        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=self.registry,
            supported_languages=["en"]
        )
        self.anonymizer = AnonymizerEngine()
        logger.info("PIIDetector ready")

        # Context keywords לשימוש ב-post-processing
        # (keyword_regex, entity_type, score, value_regex)
        self.context_kw_patterns = [
            (r'(?:תעודת\s+זהות|ת\.?ז\.?|מספר\s+זהות|מס[\'"]?\s*זהות)',
             'IL_ID', 0.95, r'[\s:״"]*(\d{7,9})'),
            (r'(?:שם\s+(?:פרטי|משפחה|מלא|האב|אב|האם|אם)|שמו|שמה)',
             'HEB_NAME', 0.9, r'[\s:״"]*([א-ת][א-ת\s]{1,30})'),
            (r'(?:תאריך\s+לידה|ת\.?\s*לידה|נולד(?:ה)?)',
             'DATE_OF_BIRTH', 0.95, r'[\s:]*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})'),
            (r'(?:כתובת(?:\s+מגורים)?|מגורים|מרחוב)',
             'HEB_ADDRESS', 0.85, r'[\s:]*([א-ת][א-ת\s\d,״\'"]{3,50})'),
            (r'(?:חשבון\s+בנק|מספר\s+חשבון|ח[./]ב)',
             'IL_BANK_ACCOUNT', 0.95, r'[\s:]*(\d{6,14})'),
            (r'(?:מספר\s+אישי|מס[\'"]?\s*אישי|מ\.?א\.?)',
             'IL_PERSONAL_NUMBER', 0.95, r'[\s:]*(\d{5,9})'),
            (r'(?:טל(?:פון)?\'?|נייד|פלאפון|סלולרי|טל\.)',
             'IL_PHONE', 0.9, r'[\s:]*(\d[\d\-\s]{7,12})'),
            (r'(?:סיסמה|סיסמא|קוד\s+סודי|password|pwd)',
             'PASSWORD', 0.95, r'[\s:״"=-]*([A-Za-z0-9@#$%^&+=*]{4,20})'),
            (r'(?:קופת\s+חולים|קופ"ח|מכבי|כללית|מאוחדת|לאומית)',
             'HEALTH_FUND', 0.85, r'[\s:]*([א-ת\d\-\s]{3,20})'),
            (r'(?:ח\.פ|ח\.צ|עוסק\s+מורשה|תיק\s+ניכויים)',
             'IL_COMPANY_ID', 0.9, r'[\s:״"=-]*(\d{9})'),
            (r'(?:תיק\s+רפואי|מספר\s+מטופל|קוד\s+מטופל|מזהה\s+רפואי)',
             'MEDICAL_RECORD', 0.95, r'[\s:״"=-]*([A-Za-z0-9\.\-]{3,15})'),
            (r'(?:סוג\s+דם|blood\s+type)',
             'BLOOD_TYPE', 0.9, r'[\s:״"=-]*([ABO][+-]|AB[+-])'),
            (r'(?:פרופיל\s+רפואי|פרופיל\s+צבאי|פרופיל)',
             'MILITARY_PROFILE', 0.9, r'[\s:״"=-]*(\d{2})'),
            (r'(?:CVV|CVC|קוד\s+אבטחה|בגב\s+הכרטיס)',
             'CVV', 0.95, r'[\s:״"=-]*(\d{3,4})'),
            (r'(?:קוד\s+אימות|קוד\s+גישה|PIN|OTP|קוד\s+סודי)',
             'AUTH_CODE', 0.95, r'[\s:״"=-]*([a-zA-Z0-9]{4,10})'),
            (r'(?:שם\s+משתמש|username|user)',
             'USERNAME', 0.85, r'[\s:״"=-]*([a-zA-Z0-9_\.\-]{3,20})'),
            (r'(?:מספר\s+דרכון|דרכון|passport)',
             'PASSPORT', 0.95, r'[\s:״"=-]*([A-Za-z0-9]{5,15})'),
            (r'(?:רישיון\s+נהיגה|מספר\s+רישיון|driver\s+license)',
             'DRIVER_LICENSE', 0.9, r'[\s:״"=-]*(\d{5,10})'),
            (r'(?:לוחית\s+רישוי|מספר\s+רכב|רכב\s+מספר)',
             'LICENSE_PLATE', 0.85, r'[\s:״"=-]*(\d{2,3}[-\s]?\d{2,3}[-\s]?\d{2,3})'),
            (r'(?:כתובת\s+MAC|MAC\s+address)',
             'MAC_ADDRESS', 0.85, r'[\s:״"=-]*([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'),
            (r'(?:מיקוד|zip\s+code|zipcode)',
             'ZIPCODE', 0.85, r'[\s:״"=-]*(\d{5,7})'),
        ]

        logger.info("✅ PIIDetector מוכן")

    # ─── Custom Recognizers ────────────────────────────────────────
    def _add_israeli_recognizers(self):
        """הוספת recognizers ישראליים מותאמים אישית"""

        # 1. תעודת זהות ישראלית
        il_id_recognizer = PatternRecognizer(
            supported_entity="IL_ID",
            patterns=[Pattern(name="israeli_id", regex=r'\b\d{9}\b', score=0.85)],
            context=["תעודת זהות", "ת.ז", "ת\"ז", "תז", "זהות", "מספר זהות",
                     "id", "identity", "מזהה"]
        )
        self.registry.add_recognizer(il_id_recognizer)

        # 2. טלפון ישראלי
        il_phone_recognizer = PatternRecognizer(
            supported_entity="IL_PHONE",
            patterns=[Pattern(name="israeli_phone",
                              regex=r'\b0[57]\d{1}-?\d{7}\b|\b0[23489]-?\d{7}\b', score=0.8)],
            context=["טלפון", "נייד", "סלולרי", "פלאפון", "טל'", "טל.", "phone", "mobile",
                     "מספר טלפון", "ליצור קשר"]
        )
        self.registry.add_recognizer(il_phone_recognizer)

        # 3. כתובת בעברית
        address_recognizer = PatternRecognizer(
            supported_entity="HEB_ADDRESS",
            patterns=[Pattern(name="heb_address",
                              regex=r'\b(?:רחוב|שדרות|שד\'|דרך|סמטת)\s+[א-ת]+\s+\d+\b', score=0.6)],
            context=["כתובת", "מגורים", "מיקוד", "עיר", "ישוב", "שכונה"]
        )
        self.registry.add_recognizer(address_recognizer)

        # 4. מספר אישי
        personal_num_recognizer = PatternRecognizer(
            supported_entity="IL_PERSONAL_NUMBER",
            patterns=[Pattern(name="il_personal_number", regex=r'\b\d{6,8}\b', score=0.65)],
            context=["מספר אישי", "מס' אישי", "מ.א.", "מספר עובד",
                     "מספר חייל", "personal number", "employee id",
                     "מספר מזהה", "מזהה עובד"]
        )
        self.registry.add_recognizer(personal_num_recognizer)

        # 5. חשבון בנק ישראלי
        bank_account_recognizer = PatternRecognizer(
            supported_entity="IL_BANK_ACCOUNT",
            patterns=[Pattern(name="il_bank_account", regex=r'\b\d{6,14}\b', score=0.75)],
            context=["חשבון בנק", "מספר חשבון", "ח/ב", "ח.ב", "העברה", "bank account",
                     "account number", "בנק", "הפקדה", "משיכה"]
        )
        self.registry.add_recognizer(bank_account_recognizer)

        # 6. שם בעברית (בהקשר)
        heb_name_recognizer = PatternRecognizer(
            supported_entity="HEB_NAME",
            patterns=[Pattern(name="heb_name",
                              regex=r'\b[א-ת]{2,12}\s+[א-ת]{2,12}(?:\s+[א-ת]{2,12})?\b', score=0.55)],
            context=["שם", "שם פרטי", "שם משפחה", "שם מלא", "שם האב", "שם האם",
                     "לכבוד", "מאת", "חתום", "name", "full name"]
        )
        self.registry.add_recognizer(heb_name_recognizer)

        # 7. תאריך לידה
        dob_recognizer = PatternRecognizer(
            supported_entity="DATE_OF_BIRTH",
            patterns=[Pattern(name="date_of_birth",
                              regex=r'\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b', score=0.7)],
            context=["תאריך לידה", "ת. לידה", "ת.לידה", "נולד", "נולדה",
                     "date of birth", "dob", "birthday", "birth date"]
        )
        self.registry.add_recognizer(dob_recognizer)

        # 8. מספר סניף בנק
        bank_branch_recognizer = PatternRecognizer(
            supported_entity="IL_BANK_BRANCH",
            patterns=[Pattern(name="il_bank_branch", regex=r'\b\d{3}\b', score=0.75)],
            context=["סניף", "מספר סניף", "branch", "בנק", "סניף בנק", "bank branch"]
        )
        self.registry.add_recognizer(bank_branch_recognizer)

        # 9. תפקיד
        job_title_recognizer = PatternRecognizer(
            supported_entity="JOB_TITLE",
            patterns=[Pattern(name="job_title", regex=(
                r'\b('
                r'מנהל|מנהלת|מנכ"ל|מנכ"לית|סמנכ"ל|סמנכ"לית|'
                r'מהנדס|מהנדסת|ארכיטקט|אדריכל|'
                r'רופא|רופאה|ד"ר|פרופסור|'
                r'עורך דין|עורכת דין|עו"ד|'
                r'חשב|חשבת|רואה חשבון|'
                r'מנתח מערכות|מתכנת|מתכנתת|אנליסט|'
                r'שוטר|קצין|טייס|'
                r'CEO|CTO|CFO|COO|VP|Director|Manager'
                r')\b'
            ), score=0.7)],
            context=["תפקיד", "עובד", "position", "title", "role", "עיסוק"]
        )
        self.registry.add_recognizer(job_title_recognizer)

        logger.info("✅ הוספו 9 recognizers ישראליים מותאמים")

    # ─── Context Keyword Post-Processing ───────────────────────────
    def detect_context_keywords(self, text: str) -> List[Dict[str, Any]]:
        """
        זיהוי ערכים שבאים אחרי מילות מפתח (post-processing).
        מחזיר רשימת dicts תואמות לפורמט Presidio.
        """
        results = []
        for kw_pattern, entity_type, score, val_pattern in self.context_kw_patterns:
            full_pattern = kw_pattern + val_pattern
            try:
                for m in re.finditer(full_pattern, text, re.IGNORECASE | re.UNICODE):
                    if m.lastindex:
                        value = m.group(1).strip()
                        value_start = m.start(1)
                        value_end = m.end(1)
                    else:
                        value = m.group().strip()
                        value_start = m.start()
                        value_end = m.end()
                    if value:
                        results.append({
                            "entity_type": entity_type,
                            "start": value_start,
                            "end": value_end,
                            "score": score,
                            "text": value,
                            "source": "context_keyword"
                        })
            except Exception as e:
                logger.warning(f"שגיאה ב-context keyword {entity_type}: {e}")
        logger.debug(f"🔑 Context keywords: {len(results)} ממצאים")
        return results

    # ─── Overlap Dedup ─────────────────────────────────────────────
    @staticmethod
    def _overlap_dedup(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        מסיר כפילויות לפי חפיפת span.
        אם span A כולל את span B, שומר רק את A (הארוך/עם הציון הגבוה יותר).
        """
        if not entities:
            return []

        # מיון לפי start, ואז score יורד
        sorted_e = sorted(entities, key=lambda e: (e["start"], -e["score"]))
        result = []

        for candidate in sorted_e:
            cstart, cend = candidate["start"], candidate["end"]
            overlapping = [
                i for i, ex in enumerate(result)
                if cstart < ex["end"] and cend > ex["start"]
            ]
            if not overlapping:
                result.append(candidate)
            else:
                # שמור את זה עם ה-score הגבוה / ה-span הארוך יותר
                for idx in overlapping:
                    ex = result[idx]
                    span_len_candidate = cend - cstart
                    span_len_existing  = ex["end"] - ex["start"]
                    if (candidate["score"] > ex["score"] or
                            span_len_candidate > span_len_existing):
                        result[idx] = candidate
                        break

        return sorted(result, key=lambda e: e["start"])

    # ─── ניתוח ראשי ────────────────────────────────────────────────
    def analyze(self, text: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        ניתוח טקסט + context keywords + overlap dedup.
        """
        if not text.strip():
            return []

        logger.info(f"🤖 Presidio מנתח | {len(text)} תווים")

        # Presidio
        presidio_results = self.analyzer.analyze(text=text, entities=[], language="en")
        presidio_entities = [{
            "entity_type": r.entity_type,
            "start": r.start,
            "end": r.end,
            "score": r.score,
            "text": text[r.start:r.end],
            "source": "presidio"
        } for r in presidio_results]

        logger.debug(f"  Presidio raw: {len(presidio_entities)}")

        # Context keywords
        context_entities = self.detect_context_keywords(text)

        # איחוד + dedup
        all_entities = presidio_entities + context_entities
        deduped = self._overlap_dedup(all_entities)

        logger.info(
            f"✅ Presidio={len(presidio_entities)}, "
            f"Context={len(context_entities)} → "
            f"ייחודי={len(deduped)}"
        )
        return deduped

    def anonymize(self, text: str, analyzer_results) -> str:
        """אנונימיזציה לפי תוצאות Presidio"""
        if not text.strip() or not analyzer_results:
            return text
        anonymized = self.anonymizer.anonymize(text=text, analyzer_results=analyzer_results)
        return anonymized.text

    def future_nlp_hook(self, text: str):
        """Hook לשילוב מודל NLP עתידי (AlephBERT)"""
        return []
