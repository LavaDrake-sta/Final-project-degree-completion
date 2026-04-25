from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from typing import List, Dict, Any
import re

class PIIDetector:
    """
    Core AI Layer using Microsoft Presidio for PII Detection locally.
    Includes custom recognizers for Israeli/Hebrew data.
    """
    
    def __init__(self):
        # Explicitly tell Presidio which spaCy model to use.
        # This prevents it from trying to auto-download en_core_web_lg.
        # We use en_core_web_lg (already downloaded) for best accuracy.
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()

        # Registry - only English
        self.registry = RecognizerRegistry()
        self.registry.load_predefined_recognizers(languages=["en"])

        # Add custom Israeli recognizers (regex-based, no spaCy needed)
        self._add_israeli_recognizers()

        # Analyzer - use the explicitly created NLP engine
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=self.registry,
            supported_languages=["en"]
        )
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
        
        # 3. כתובת בעברית
        address_pattern = Pattern(name="heb_address_pattern", regex=r'\b(?:רחוב|שדרות|שד\'|דרך|סמטת)\s+[א-ת]+\s+\d+\b', score=0.6)
        address_recognizer = PatternRecognizer(
            supported_entity="HEB_ADDRESS",
            patterns=[address_pattern],
            context=["כתובת", "מגורים", "מיקוד"]
        )
        self.registry.add_recognizer(address_recognizer)

        # 4. מספר אישי (מספר עובד / מספר צבאי) - בד"כ 6-8 ספרות
        personal_num_pattern = Pattern(
            name="il_personal_number",
            regex=r'\b\d{6,8}\b',
            score=0.65
        )
        personal_num_recognizer = PatternRecognizer(
            supported_entity="IL_PERSONAL_NUMBER",
            patterns=[personal_num_pattern],
            context=["מספר אישי", "מס' אישי", "מ.א.", "מספר עובד",
                     "מספר חייל", "personal number", "employee id"]
        )
        self.registry.add_recognizer(personal_num_recognizer)

        # 5. תפקיד - keyword רשימת תפקידים נפוצים
        job_title_pattern = Pattern(
            name="job_title_pattern",
            regex=(
                r'\b('
                r'מנהל|מנהלת|מנכ"ל|מנכ"לית|סמנכ"ל|סמנכ"לית|'
                r'מהנדס|מהנדסת|ארכיטקט|אדריכל|'
                r'רופא|רופאה|ד"ר|פרופסור|'
                r'עורך דין|עורכת דין|עו"ד|'
                r'חשב|חשבת|רואה חשבון|'
                r'מנתח מערכות|מתכנת|מתכנתת|אנליסט|'
                r'מורה|מורה|מנהל בית ספר|'
                r'שוטר|קצין|טייס|'
                r'CEO|CTO|CFO|COO|VP|Director|Manager'
                r')\b'
            ),
            score=0.7
        )
        job_title_recognizer = PatternRecognizer(
            supported_entity="JOB_TITLE",
            patterns=[job_title_pattern],
            context=["תפקיד", "עובד", "position", "title", "role",
                     "עיסוק", "שם", "פרטים"]
        )
        self.registry.add_recognizer(job_title_recognizer)

        # 6. מקצוע - מילות מקצוע כלליות יותר
        profession_pattern = Pattern(
            name="profession_pattern",
            regex=(
                r'\b('
                r'רפואה|משפטים|הנדסה|אדריכלות|חינוך|חשבונאות|'
                r'כלכלה|פסיכולוגיה|סיעוד|פיזיותרפיה|'
                r'תכנות|סייבר|מחשבים|'
                r'medicine|law|engineering|education|accounting|'
                r'psychology|nursing|software|finance'
                r')\b'
            ),
            score=0.6
        )
        profession_recognizer = PatternRecognizer(
            supported_entity="PROFESSION",
            patterns=[profession_pattern],
            context=["מקצוע", "לימד", "למד", "עוסק", "עוסקת",
                     "profession", "occupation", "field"]
        )
        self.registry.add_recognizer(profession_recognizer)

        # 7. מספר סניף בנק ישראלי - 3 ספרות עם הקשר של "סניף"/"בנק"
        bank_branch_pattern = Pattern(
            name="il_bank_branch_pattern",
            regex=r'\b\d{3}\b',
            score=0.75
        )
        bank_branch_recognizer = PatternRecognizer(
            supported_entity="IL_BANK_BRANCH",
            patterns=[bank_branch_pattern],
            context=["סניף", "מספר סניף", "branch", "סניף בנק",
                     "bank branch", "בנק", "חשבון בנק", "העברה"]
        )
        self.registry.add_recognizer(bank_branch_recognizer)

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
