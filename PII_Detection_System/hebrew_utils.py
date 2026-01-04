"""
Hebrew Text Utils - כלי עזר לטקסט עברי
פרויקט גמר - זיהוי מידע אישי רגיש

תיקון בעיות עם הצגת טקסט עברי ב-Python
"""

import re
from typing import List, Dict


class HebrewTextFixer:
    """מחלקה לתיקון בעיות טקסט עברי"""

    def __init__(self):
        # טבלת המרה לתווים עבריים שטסטקט מבלבל
        self.common_mistakes = {
            # תיקונים נפוצים של OCR
            'י': ['|', 'l', '1'],
            'ו': ['1', 'l', '|'],
            'ר': ['ר', 'p'],
            'ד': ['ד', '6'],
            'ה': ['ה', 'n'],
            'ח': ['ח', 'n'],
            'מ': ['מ', 'o'],
            'ף': ['ף', 'P'],
            'ץ': ['ץ', 'v'],
            'ק': ['ק', 'p'],
        }

    def fix_rtl_display(self, text: str) -> str:
        """
        תיקון הצגת טקסט עברי (RTL)
        """
        try:
            # ניסיון עם bidi אם זמין
            from bidi.algorithm import get_display
            return get_display(text)
        except ImportError:
            # אם אין bidi, נשתמש בפתרון פשוט יותר
            return self._simple_rtl_fix(text)

    def _simple_rtl_fix(self, text: str) -> str:
        """תיקון RTL פשוט ללא ספריות חיצוניות"""

        lines = text.split('\n')
        fixed_lines = []

        for line in lines:
            # בדיקה אם השורה מכילה עברית
            if self._contains_hebrew(line):
                # הפוך את השורה אם היא קצרה ומכילה רק עברית
                words = line.strip().split()
                if len(words) <= 3 and all(self._is_mostly_hebrew(word) for word in words):
                    fixed_line = ' '.join(reversed(words))
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _contains_hebrew(self, text: str) -> bool:
        """בדיקה אם הטקסט מכיל עברית"""
        hebrew_chars = re.findall(r'[\u0590-\u05FF]', text)
        return len(hebrew_chars) > 0

    def _is_mostly_hebrew(self, word: str) -> bool:
        """בדיקה אם המילה היא בעיקר עברית"""
        if not word:
            return False

        hebrew_chars = len(re.findall(r'[\u0590-\u05FF]', word))
        total_chars = len(re.findall(r'[a-zA-Z\u0590-\u05FF]', word))

        if total_chars == 0:
            return False

        return hebrew_chars / total_chars > 0.5

    def improve_ocr_text(self, text: str) -> str:
        """שיפור טקסט שהתקבל מOCR"""

        # תיקון תווים שגויים נפוצים
        improved_text = text

        # תיקונים ספציפיים לעברית מOCR
        ocr_fixes = {
            'רח\'': 'רח׳',
            'ת.ז': 'ת.ז.',
            'ד"ר': 'ד״ר',
            'בע"מ': 'בע״מ',
            'שח"ר': 'ש״ח',
            'נ"ע': 'נ״ע',
        }

        for wrong, correct in ocr_fixes.items():
            improved_text = improved_text.replace(wrong, correct)

        # ניקוי רווחים מיותרים
        improved_text = re.sub(r'\s+', ' ', improved_text)
        improved_text = improved_text.strip()

        return improved_text


# פונקציות עזר גלובליות
def fix_hebrew_text(text: str) -> str:
    """פונקציה מהירה לתיקון טקסט עברי"""
    fixer = HebrewTextFixer()
    fixed = fixer.fix_rtl_display(text)
    return fixer.improve_ocr_text(fixed)


def prepare_text_for_display(text: str) -> str:
    """הכנת טקסט לתצוגה נכונה"""
    if not text:
        return text

    # תיקון כיוון
    fixed_text = fix_hebrew_text(text)

    # תיקון עיצוב לStreamlit
    # Streamlit עובד טוב יותר עם HTML לעברית
    lines = fixed_text.split('\n')
    formatted_lines = []

    for line in lines:
        if line.strip():
            # אם השורה מכילה עברית, נוסיף כיוון RTL
            if re.search(r'[\u0590-\u05FF]', line):
                formatted_lines.append(f'<div dir="rtl">{line}</div>')
            else:
                formatted_lines.append(line)
        else:
            formatted_lines.append('<br>')

    return '\n'.join(formatted_lines)


# בדיקה מהירה
if __name__ == "__main__":
    print("🔤 בדיקת תיקון טקסט עברי")
    print("=" * 30)

    # דוגמאות טקסט בעייתי
    test_texts = [
        "שלום יוסי כהן",
        "תעודת זהות: 123456789",
        "רח' הרצל 25 תל אביב",
        "טלפון: 052-1234567"
    ]

    fixer = HebrewTextFixer()

    for text in test_texts:
        fixed = fixer.fix_rtl_display(text)
        print(f"מקורי: {text}")
        print(f"מתוקן: {fixed}")
        print("---")

    print("✅ בדיקת תיקון הושלמה")