"""
PII Detection System - Basic Detector
פרויקט גמר - זיהוי מידע אישי רגיש

מודול זיהוי בסיסי עם רגקסים ומילות מפתח
מתוקן לעבודה ב-PyCharm
"""

import re
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class SensitivityLevel(Enum):
    """רמות רגישות למידע"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class PIIMatch:
    """ייצוג של מידע רגיש שנמצא"""
    text: str
    category: str
    start_pos: int
    end_pos: int
    confidence: float
    sensitivity: SensitivityLevel

class BasicPIIDetector:
    """
    מזהה מידע אישי בסיסי עם רגקסים
    גרסה פשוטה ויציבה
    """

    def __init__(self):
        """אתחול המזהה עם כל הדפוסים והחוקים"""

        # דפוסי רגקס לזיהוי מידע אישי בעברית
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
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'sensitivity': SensitivityLevel.HIGH,
                'description': 'כתובת דואר אלקטרוני'
            },
            'credit_card': {
                'pattern': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                'sensitivity': SensitivityLevel.CRITICAL,
                'description': 'מספר כרטיס אשראי (חשוד)'
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
            }
        }

        # מילות מפתח רגישות בעברית
        self.sensitive_keywords = {
            'medical': {
                'keywords': [
                    'רופא', 'בית חולים', 'מחלה', 'תרופה', 'אבחנה',
                    'ביטוח בריאות', 'חולה', 'טיפול', 'רפואי', 'מרפאה',
                    'סרטן', 'סוכרת', 'דיכאון', 'חרדה', 'פסיכיאטר'
                ],
                'sensitivity': SensitivityLevel.HIGH
            },
            'financial': {
                'keywords': [
                    'משכורת', 'שכר', 'חוב', 'הלוואה', 'משכנתא',
                    'חשבון בנק', 'אשראי', 'ממון', 'כסף', 'שקל',
                    'עלות', 'תשלום', 'חיוב', 'זיכוי'
                ],
                'sensitivity': SensitivityLevel.HIGH
            },
            'personal': {
                'keywords': [
                    'גירושין', 'מזונות', 'טיפול פסיכולוגי', 'יחסים',
                    'משפחה', 'ילדים', 'הורים', 'נשוי', 'רווק',
                    'פרטי', 'סודי', 'אישי'
                ],
                'sensitivity': SensitivityLevel.MEDIUM
            },
            'identification': {
                'keywords': [
                    'תעודת זהות', 'ת.ז', 'דרכון', 'רישיון נהיגה',
                    'מספר זהות', 'תז', 'זהות', 'תעודה'
                ],
                'sensitivity': SensitivityLevel.CRITICAL
            }
        }

    def detect_patterns(self, text: str) -> List[PIIMatch]:
        """זיהוי דפוסים באמצעות ביטויים רגולריים"""
        matches = []

        for category, pattern_info in self.patterns.items():
            pattern = pattern_info['pattern']

            try:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    pii_match = PIIMatch(
                        text=match.group(),
                        category=category,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.9,  # רמת ודאות גבוהה לרגקסים
                        sensitivity=pattern_info['sensitivity']
                    )
                    matches.append(pii_match)
            except Exception as e:
                print(f"שגיאה בזיהוי דפוס {category}: {e}")
                continue

        return matches

    def detect_keywords(self, text: str) -> List[PIIMatch]:
        """זיהוי מילות מפתח רגישות"""
        matches = []
        text_lower = text.lower()

        for category, keyword_info in self.sensitive_keywords.items():
            for keyword in keyword_info['keywords']:
                keyword_lower = keyword.lower()

                # חיפוש כל המופעים של המילה
                start_pos = 0
                while True:
                    pos = text_lower.find(keyword_lower, start_pos)
                    if pos == -1:
                        break

                    pii_match = PIIMatch(
                        text=keyword,
                        category=f"keyword_{category}",
                        start_pos=pos,
                        end_pos=pos + len(keyword),
                        confidence=0.6,  # רמת ודאות נמוכה יותר למילות מפתח
                        sensitivity=keyword_info['sensitivity']
                    )
                    matches.append(pii_match)
                    start_pos = pos + 1

        return matches

    def analyze_text(self, text: str) -> Dict:
        """ניתוח טקסט מלא - הפונקציה הראשית"""
        if not text or not text.strip():
            return {
                'matches': [],
                'total_matches': 0,
                'overall_sensitivity': SensitivityLevel.LOW,
                'summary': "לא הוזן טקסט לבדיקה"
            }

        try:
            # זיהוי דפוסים ומילות מפתח
            pattern_matches = self.detect_patterns(text)
            keyword_matches = self.detect_keywords(text)

            # איחוד כל הממצאים
            all_matches = pattern_matches + keyword_matches

            # הסרת כפילויות (אותו טקסט באותו מיקום)
            unique_matches = []
            seen = set()

            for match in all_matches:
                match_key = (match.text, match.start_pos, match.category)
                if match_key not in seen:
                    unique_matches.append(match)
                    seen.add(match_key)

            # חישוב רמת רגישות כללית
            if not unique_matches:
                overall_sensitivity = SensitivityLevel.LOW
            else:
                max_sensitivity = max(match.sensitivity.value for match in unique_matches)
                overall_sensitivity = SensitivityLevel(max_sensitivity)

            # יצירת סיכום
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

        # ספירה לפי קטגוריות
        categories = {}
        critical_count = 0
        high_count = 0

        for match in matches:
            category = match.category
            categories[category] = categories.get(category, 0) + 1

            if match.sensitivity == SensitivityLevel.CRITICAL:
                critical_count += 1
            elif match.sensitivity == SensitivityLevel.HIGH:
                high_count += 1

        # בניית הסיכום
        summary = f"⚠️ נמצאו {len(matches)} פריטי מידע רגיש"

        if critical_count > 0:
            summary += f" (כולל {critical_count} קריטיים)"
        elif high_count > 0:
            summary += f" (כולל {high_count} ברמה גבוהה)"

        return summary

    def get_statistics(self, matches: List[PIIMatch]) -> Dict:
        """סטטיסטיקות מפורטות על הממצאים"""
        if not matches:
            return {}

        stats = {
            'by_sensitivity': {},
            'by_category': {},
            'confidence_avg': 0
        }

        # ספירה לפי רמת רגישות
        for match in matches:
            sens_name = match.sensitivity.name
            stats['by_sensitivity'][sens_name] = stats['by_sensitivity'].get(sens_name, 0) + 1

            # ספירה לפי קטגוריה
            category = match.category.replace('_', ' ').title()
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

        # חישוב ממוצע רמת ודאות
        if matches:
            stats['confidence_avg'] = sum(match.confidence for match in matches) / len(matches)

        return stats

# דוגמה לשימוש ובדיקה
if __name__ == "__main__":
    print("🔍 בדיקת מודול זיהוי המידע הרגיש")
    print("=" * 40)

    # יצירת מזהה
    detector = BasicPIIDetector()

    # דוגמאות לבדיקה
    test_cases = [
        "שלום, אני יוסי כהן ומספר הזהות שלי הוא 123456789",
        "אפשר להתקשר אליי בטלפון 052-1234567 או לשלוח אימייל ל yossi@example.com",
        "אני עובד בחברת הייטק ומרוויח 15,000 שקל בחודש",
        "השבוע הלכתי לרופא בגלל מחלה כרונית",
        "מספר הכרטיס שלי הוא 4580-1234-5678-9012"
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. בדיקת טקסט: '{text}'")
        results = detector.analyze_text(text)
        print(f"   {results['summary']}")
        print(f"   רמת רגישות: {results['overall_sensitivity'].name}")

        if results['matches']:
            for match in results['matches']:
                print(f"   🔍 '{match.text}' → {match.category} (ודאות: {match.confidence:.0%})")

    print("\n✅ בדיקת המודול הושלמה בהצלחה!")