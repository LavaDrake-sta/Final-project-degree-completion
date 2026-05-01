"""
PII Detection System - Basic Detector
פרויקט גמר - זיהוי מידע אישי רגיש

מודול זיהוי בסיסי עם רגקסים ומילות מפתח.
תיקונים:
  - Span-based dedup (מניעת כפילויות לפי מיקום, לא רק טקסט)
  - Context keyword detection (מילת מפתח → ערך שאחריה)
  - אוצר מילים מורחב לישראלי
  - שמות קטגוריות בעברית
"""

import re
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

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

logger = get_logger("PII.BasicDetector")


# ─── רמות רגישות ───────────────────────────────────────────────────
class SensitivityLevel(Enum):
    """רמות רגישות למידע"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# ─── מבנה ממצא ─────────────────────────────────────────────────────
@dataclass
class PIIMatch:
    """ייצוג של מידע רגיש שנמצא"""
    text: str
    category: str
    start_pos: int
    end_pos: int
    confidence: float
    sensitivity: SensitivityLevel


# ─── מילון שמות עברי לקטגוריות ────────────────────────────────────
CATEGORY_HEBREW = {
    "israeli_id":            "תעודת זהות ישראלית",
    "phone_number":          "מספר טלפון",
    "email":                 "כתובת אימייל",
    "credit_card":           "כרטיס אשראי",
    "bank_account":          "חשבון בנק",
    "postal_code":           "מיקוד",
    "context_id":            "תעודת זהות (הקשר)",
    "context_phone":         "טלפון (הקשר)",
    "context_name":          "שם אדם (הקשר)",
    "context_birthdate":     "תאריך לידה (הקשר)",
    "context_address":       "כתובת (הקשר)",
    "context_bank":          "חשבון בנק (הקשר)",
    "context_personal_num":  "מספר אישי (הקשר)",
    "keyword_medical":       "מידע רפואי",
    "keyword_financial":     "מידע פיננסי",
    "keyword_personal":      "מידע אישי",
    "keyword_identification":"זיהוי",
}


def category_display_name(category: str) -> str:
    """מחזיר שם עברי לקטגוריה"""
    return CATEGORY_HEBREW.get(category, category)


# ─── עדיפות קטגוריות (לdedup) ──────────────────────────────────────
CATEGORY_PRIORITY = {
    "israeli_id":   10,
    "credit_card":  9,
    "context_id":   8,
    "context_phone":7,
    "phone_number": 7,
    "email":        7,
    "context_bank": 6,
    "bank_account": 5,
    "context_personal_num": 5,
    "context_name": 4,
    "context_birthdate": 4,
    "context_address": 4,
    "postal_code":  2,
    "keyword_identification": 3,
    "keyword_medical":   3,
    "keyword_financial": 3,
    "keyword_personal":  2,
}


def _priority(category: str) -> int:
    return CATEGORY_PRIORITY.get(category, 1)


class BasicPIIDetector:
    """
    מזהה מידע אישי בסיסי עם רגקסים + context keywords.
    """

    def __init__(self):
        """אתחול המזהה עם כל הדפוסים והחוקים"""
        logger.info("🔧 אתחול BasicPIIDetector...")

        # ─── תבניות Regex ─────────────────────────────────────────
        self.patterns = {
            'israeli_id': {
                'pattern': r'\b\d{9}\b',
                'sensitivity': SensitivityLevel.CRITICAL,
                'description': 'מספר תעודת זהות ישראלית'
            },
            'phone_number': {
                'pattern': r'\b0\d{1,2}-?\d{7,8}\b',
                'sensitivity': SensitivityLevel.HIGH,
                'description': 'מספר טלפון ישראלי'
            },
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
                'sensitivity': SensitivityLevel.HIGH,
                'description': 'כתובת דואר אלקטרוני'
            },
            'credit_card': {
                'pattern': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                'sensitivity': SensitivityLevel.CRITICAL,
                'description': 'מספר כרטיס אשראי'
            },
            'bank_account': {
                'pattern': r'\b\d{6,12}\b',
                'sensitivity': SensitivityLevel.HIGH,
                'description': 'מספר חשבון בנק (חשוד)'
            },
            'postal_code': {
                'pattern': r'\b\d{5,7}\b',
                'sensitivity': SensitivityLevel.MEDIUM,
                'description': 'מיקוד'
            },
        }

        # ─── מילות מפתח → זיהוי ערך שאחריהן ─────────────────────
        # פורמט: (keyword_pattern, entity_category, sensitivity, value_pattern)
        # value_pattern מוצא את הערך שבא מיד אחרי מילת המפתח
        self.context_keywords = [
            # זיהוי
            (r'(?:תעודת\s+זהות|ת\.?ז\.?|מספר\s+זהות|מס[\'"]?\s*זהות)',
             'context_id', SensitivityLevel.CRITICAL,
             r'[\s:״"]*(\d{7,9})'),
            # טלפון
            (r'(?:טל(?:פון)?\'?|נייד|פלאפון|סלולרי|טל\.)',
             'context_phone', SensitivityLevel.HIGH,
             r'[\s:]*(\d[\d\-\s]{7,12})'),
            # שם
            (r'(?:שם\s+(?:פרטי|משפחה|מלא|האב|אב|האם|אם)|שמו|שמה)',
             'context_name', SensitivityLevel.HIGH,
             r'[\s:״"]*([א-ת][א-ת\s]{1,30})'),
            # תאריך לידה
            (r'(?:תאריך\s+לידה|ת\.?\s*לידה|נולד(?:ה)?)',
             'context_birthdate', SensitivityLevel.CRITICAL,
             r'[\s:]*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})'),
            # כתובת
            (r'(?:כתובת(?:\s+מגורים)?|מגורים|רחוב|מרחוב)',
             'context_address', SensitivityLevel.MEDIUM,
             r'[\s:]*([א-ת][א-ת\s\d,״\'"]{3,50})'),
            # חשבון בנק
            (r'(?:חשבון\s+בנק|מספר\s+חשבון|ח[./]ב)',
             'context_bank', SensitivityLevel.CRITICAL,
             r'[\s:]*(\d{6,14})'),
            # מספר אישי
            (r'(?:מספר\s+אישי|מס[\'"]?\s*אישי|מ\.?א\.?)',
             'context_personal_num', SensitivityLevel.CRITICAL,
             r'[\s:]*(\d{5,9})'),
        ]

        # ─── מילות מפתח רגישות (הקשר בלבד, לא ערך ספציפי) ───────
        self.sensitive_keywords = {
            'medical': {
                'keywords': [
                    'רופא', 'בית חולים', 'מחלה', 'תרופה', 'אבחנה',
                    'ביטוח בריאות', 'חולה', 'טיפול רפואי', 'מרפאה',
                    'סרטן', 'סוכרת', 'דיכאון', 'חרדה', 'פסיכיאטר'
                ],
                'sensitivity': SensitivityLevel.HIGH
            },
            'financial': {
                'keywords': [
                    'משכורת', 'שכר חודשי', 'חוב', 'הלוואה', 'משכנתא',
                    'כרטיס אשראי', 'ממון', 'חיוב חשבון', 'זיכוי'
                ],
                'sensitivity': SensitivityLevel.HIGH
            },
            'personal': {
                'keywords': [
                    'גירושין', 'מזונות', 'טיפול פסיכולוגי',
                    'פרטי', 'סודי', 'אישי'
                ],
                'sensitivity': SensitivityLevel.MEDIUM
            },
            'identification': {
                'keywords': [
                    'דרכון', 'רישיון נהיגה', 'תעודה ממשלתית'
                ],
                'sensitivity': SensitivityLevel.CRITICAL
            },
        }

        logger.info("✅ BasicPIIDetector מוכן")

    # ─── זיהוי תבניות Regex ────────────────────────────────────────
    def detect_patterns(self, text: str) -> List[PIIMatch]:
        """זיהוי דפוסים באמצעות ביטויים רגולריים"""
        matches = []
        for category, pattern_info in self.patterns.items():
            try:
                for m in re.finditer(pattern_info['pattern'], text, re.IGNORECASE):
                    matches.append(PIIMatch(
                        text=m.group(),
                        category=category,
                        start_pos=m.start(),
                        end_pos=m.end(),
                        confidence=0.9,
                        sensitivity=pattern_info['sensitivity']
                    ))
            except Exception as e:
                logger.warning(f"שגיאה בזיהוי דפוס {category}: {e}")
        logger.debug(f"🔍 נמצאו {len(matches)} ממצאי Regex (לפני dedup)")
        return matches

    # ─── זיהוי Context Keywords ────────────────────────────────────
    def detect_context_keywords(self, text: str) -> List[PIIMatch]:
        """
        מחפש מילות מפתח כמו 'תעודת זהות:' ותופס את הערך שאחריהן.
        """
        matches = []
        for kw_pattern, category, sensitivity, val_pattern in self.context_keywords:
            full_pattern = kw_pattern + val_pattern
            try:
                for m in re.finditer(full_pattern, text, re.IGNORECASE | re.UNICODE):
                    # קבוצה 1 = הערך שנתפס
                    value = m.group(1).strip() if m.lastindex and m.group(1) else m.group().strip()
                    if not value:
                        continue
                    # מיקום הערך בטקסט
                    value_start = m.start(1) if m.lastindex else m.start()
                    value_end = m.end(1) if m.lastindex else m.end()
                    matches.append(PIIMatch(
                        text=value,
                        category=category,
                        start_pos=value_start,
                        end_pos=value_end,
                        confidence=0.95,
                        sensitivity=sensitivity
                    ))
            except Exception as e:
                logger.warning(f"שגיאה ב-context keyword {category}: {e}")
        logger.debug(f"🔑 נמצאו {len(matches)} ממצאי Context")
        return matches

    # ─── זיהוי מילות מפתח כלליות ──────────────────────────────────
    def detect_keywords(self, text: str) -> List[PIIMatch]:
        """זיהוי מילות מפתח רגישות (הקשר בלבד)"""
        matches = []
        text_lower = text.lower()
        for category, keyword_info in self.sensitive_keywords.items():
            for keyword in keyword_info['keywords']:
                pos = 0
                while True:
                    idx = text_lower.find(keyword.lower(), pos)
                    if idx == -1:
                        break
                    matches.append(PIIMatch(
                        text=text[idx: idx + len(keyword)],
                        category=f"keyword_{category}",
                        start_pos=idx,
                        end_pos=idx + len(keyword),
                        confidence=0.6,
                        sensitivity=keyword_info['sensitivity']
                    ))
                    pos = idx + 1
        return matches

    # ─── Span-based Dedup ──────────────────────────────────────────
    @staticmethod
    def _span_dedup(matches: List[PIIMatch]) -> List[PIIMatch]:
        """
        מסיר כפילויות לפי מיקום (start, end).
        אם שניים חופפים (overlap), שומר את זה עם העדיפות הגבוהה יותר.
        לוגיקה:
          1. ממיין לפי start.
          2. עבור כל ממצא — בודק אם הוא חופף עם ממצא שכבר בתוצאה.
          3. אם חופף: שומר את זה עם priority גבוה יותר.
        """
        if not matches:
            return []

        # מיון לפי start_pos, אח"כ לפי priority יורד
        sorted_matches = sorted(
            matches,
            key=lambda m: (m.start_pos, -_priority(m.category))
        )

        result: List[PIIMatch] = []
        for candidate in sorted_matches:
            overlaps_with = [
                i for i, existing in enumerate(result)
                if candidate.start_pos < existing.end_pos and candidate.end_pos > existing.start_pos
            ]
            if not overlaps_with:
                result.append(candidate)
            else:
                # החלף את כל החופפים אם ל-candidate יש עדיפות גבוהה יותר
                for idx in overlaps_with:
                    existing = result[idx]
                    if _priority(candidate.category) > _priority(existing.category):
                        result[idx] = candidate
                        break
        return result

    # ─── ניתוח ראשי ────────────────────────────────────────────────
    def analyze_text(self, text: str) -> Dict:
        """ניתוח טקסט מלא — פונקציה ראשית"""
        if not text or not text.strip():
            return {
                'matches': [],
                'total_matches': 0,
                'overall_sensitivity': SensitivityLevel.LOW,
                'summary': "לא הוזן טקסט לבדיקה"
            }

        logger.info(f"🔍 מתחיל ניתוח PII | {len(text)} תווים")
        try:
            pattern_matches  = self.detect_patterns(text)
            context_matches  = self.detect_context_keywords(text)
            keyword_matches  = self.detect_keywords(text)

            all_matches = pattern_matches + context_matches + keyword_matches

            # Span-based dedup
            unique_matches = self._span_dedup(all_matches)

            logger.info(
                f"✅ זיהוי הושלם | "
                f"Regex={len(pattern_matches)}, "
                f"Context={len(context_matches)}, "
                f"Keywords={len(keyword_matches)} → "
                f"ייחודי={len(unique_matches)}"
            )

            # רמת רגישות כללית
            overall_sensitivity = (
                SensitivityLevel(max(m.sensitivity.value for m in unique_matches))
                if unique_matches else SensitivityLevel.LOW
            )

            summary = self._generate_summary(unique_matches)
            return {
                'matches': unique_matches,
                'total_matches': len(unique_matches),
                'overall_sensitivity': overall_sensitivity,
                'summary': summary,
                'text_length': len(text),
                'words_count': len(text.split())
            }

        except Exception as e:
            logger.error(f"❌ שגיאה בניתוח הטקסט: {e}", exc_info=True)
            return {
                'matches': [],
                'total_matches': 0,
                'overall_sensitivity': SensitivityLevel.LOW,
                'summary': f"שגיאה בניתוח הטקסט: {str(e)}",
                'error': str(e)
            }

    def _generate_summary(self, matches: List[PIIMatch]) -> str:
        """יצירת סיכום הממצאים"""
        if not matches:
            return "✅ לא נמצא מידע רגיש בטקסט"
        critical = sum(1 for m in matches if m.sensitivity == SensitivityLevel.CRITICAL)
        high     = sum(1 for m in matches if m.sensitivity == SensitivityLevel.HIGH)
        summary  = f"⚠️ נמצאו {len(matches)} פריטי מידע רגיש"
        if critical:
            summary += f" (כולל {critical} קריטיים)"
        elif high:
            summary += f" (כולל {high} ברמה גבוהה)"
        return summary

    def get_statistics(self, matches: List[PIIMatch]) -> Dict:
        """סטטיסטיקות מפורטות על הממצאים"""
        if not matches:
            return {}
        stats = {'by_sensitivity': {}, 'by_category': {}, 'confidence_avg': 0}
        for m in matches:
            stats['by_sensitivity'][m.sensitivity.name] = \
                stats['by_sensitivity'].get(m.sensitivity.name, 0) + 1
            label = category_display_name(m.category)
            stats['by_category'][label] = stats['by_category'].get(label, 0) + 1
        stats['confidence_avg'] = sum(m.confidence for m in matches) / len(matches)
        return stats


# ─── בדיקה עצמאית ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔍 בדיקת BasicPIIDetector")
    print("=" * 50)
    detector = BasicPIIDetector()

    tests = [
        "שלום, שם פרטי: יוסי כהן, תעודת זהות: 123456789",
        "טלפון: 052-1234567 | אימייל: yossi@example.com",
        "תאריך לידה: 15/03/1990 | כתובת: רחוב הרצל 12 תל אביב",
        "מספר חשבון: 123456789 סניף 001 בנק לאומי",
        "מספר אישי: 1234567 של העובד",
        "כרטיס אשראי: 4580-1234-5678-9012",
    ]
    for i, t in enumerate(tests, 1):
        print(f"\n{i}. {t}")
        res = detector.analyze_text(t)
        print(f"   → {res['summary']}")
        for m in res['matches']:
            print(f"      📌 '{m.text}' | {category_display_name(m.category)} | {m.sensitivity.name} | {m.confidence:.0%}")
    print("\n✅ הבדיקה הושלמה!")