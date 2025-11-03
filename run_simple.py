"""
Simple PII Detection Script - No AI Dependencies Required
Works on Windows without heavy libraries
"""

import sys
import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

# Israeli ID validation
def validate_israeli_id(id_num: str) -> bool:
    """Validate Israeli ID using Luhn algorithm"""
    if len(id_num) != 9 or not id_num.isdigit():
        return False

    total = 0
    for i, digit in enumerate(id_num):
        num = int(digit)
        if i % 2 == 0:
            num *= 1
        else:
            num *= 2
            if num > 9:
                num = num // 10 + num % 10
        total += num

    return total % 10 == 0


@dataclass
class PIIItem:
    text: str
    type: str
    sensitivity: str  # "standard" or "special"


class SimplePIIDetector:
    """Simple PII detector using only regex - no AI dependencies"""

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns"""
        # Israeli ID
        self.id_pattern = re.compile(r'\b\d{9}\b')

        # Phone
        self.phone_pattern = re.compile(
            r'(?:\+972|972|0)[-\s]?(?:5[0-9]|[2-4]|[8-9])[-\s]?\d{3}[-\s]?\d{4}'
        )

        # Email
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )

        # Date of birth
        self.dob_pattern = re.compile(
            r'\b(?:0[1-9]|[12][0-9]|3[01])[\./-](?:0[1-9]|1[0-2])[\./-](?:19|20)\d{2}\b'
        )

        # Bank account
        self.bank_pattern = re.compile(r'\b\d{2,3}[-/]\d{3,6}[-/]\d{1,2}\b')

        # Keywords for sensitive detection
        self.medical_keywords = ['רפואי', 'מטופל', 'חולים', 'רופא', 'טיפול', 'מחלה', 'קופת חולים']
        self.financial_keywords = ['משכורת', 'שכר', 'הכנסה', 'חשבון בנק']
        self.political_keywords = ['מפלגה', 'פוליטי', 'השתייכות פוליטית']
        self.religious_keywords = ['דתי', 'אמונה דתית', 'יהודי', 'נוצרי', 'מוסלמי']

    def detect(self, text: str) -> Dict[str, List[PIIItem]]:
        """Detect PII in text"""
        results = {
            'standard': [],
            'special': []
        }

        # ID numbers
        for match in self.id_pattern.finditer(text):
            if validate_israeli_id(match.group()):
                results['standard'].append(PIIItem(
                    text=match.group(),
                    type='תעודת זהות',
                    sensitivity='standard'
                ))

        # Phone numbers
        for match in self.phone_pattern.finditer(text):
            results['standard'].append(PIIItem(
                text=match.group(),
                type='טלפון',
                sensitivity='standard'
            ))

        # Emails
        for match in self.email_pattern.finditer(text):
            results['standard'].append(PIIItem(
                text=match.group(),
                type='אימייל',
                sensitivity='standard'
            ))

        # Dates
        for match in self.dob_pattern.finditer(text):
            results['standard'].append(PIIItem(
                text=match.group(),
                type='תאריך',
                sensitivity='standard'
            ))

        # Bank accounts (special sensitivity)
        for match in self.bank_pattern.finditer(text):
            results['special'].append(PIIItem(
                text=match.group(),
                type='חשבון בנק',
                sensitivity='special'
            ))

        # Context-based detection for sensitive info
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()

            # Medical info
            if any(kw in line for kw in self.medical_keywords):
                results['special'].append(PIIItem(
                    text=line.strip(),
                    type='מידע רפואי',
                    sensitivity='special'
                ))

            # Financial info
            elif any(kw in line for kw in self.financial_keywords):
                results['special'].append(PIIItem(
                    text=line.strip(),
                    type='מידע כלכלי',
                    sensitivity='special'
                ))

            # Political info
            elif any(kw in line for kw in self.political_keywords):
                results['special'].append(PIIItem(
                    text=line.strip(),
                    type='דעה פוליטית',
                    sensitivity='special'
                ))

            # Religious info
            elif any(kw in line for kw in self.religious_keywords):
                results['special'].append(PIIItem(
                    text=line.strip(),
                    type='אמונה דתית',
                    sensitivity='special'
                ))

        return results


def main():
    print("=" * 80)
    print("🔍 זיהוי פרטים אישיים - גרסה פשוטה (ללא תלות ב-AI)")
    print("⚖️  תואם לתיקון 13 לחוק הגנת הפרטיות")
    print("=" * 80)
    print()

    # Check for input file
    input_file = "data/input/test_document.txt"

    if not os.path.exists(input_file):
        print(f"❌ קובץ לא נמצא: {input_file}")
        print("\nהזן טקסט לבדיקה (Enter פעמיים לסיום):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        text = '\n'.join(lines)
    else:
        print(f"✓ קורא קובץ: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()

    if not text.strip():
        print("❌ אין טקסט לבדיקה")
        return

    print()
    print("🔍 מזהה פרטים אישיים...")
    print()

    detector = SimplePIIDetector()
    results = detector.detect(text)

    standard_count = len(results['standard'])
    special_count = len(results['special'])
    total = standard_count + special_count

    print("-" * 80)
    print("📊 תוצאות:")
    print("-" * 80)
    print()

    if standard_count > 0:
        print(f"✅ פרטים אישיים רגילים ({standard_count}):")
        seen = set()
        for item in results['standard']:
            key = f"{item.type}:{item.text}"
            if key not in seen:
                print(f"   • {item.type}: {item.text}")
                seen.add(key)
        print()

    if special_count > 0:
        print(f"⚠️  מידע בעל רגישות מיוחדת - תיקון 13 ({special_count}):")
        seen = set()
        for item in results['special']:
            key = f"{item.type}:{item.text[:50]}"
            if key not in seen:
                preview = item.text[:60] + "..." if len(item.text) > 60 else item.text
                print(f"   • {item.type}: {preview}")
                seen.add(key)
        print()

    print("-" * 80)
    print(f"סה\"כ: {total} פרטים אישיים ({standard_count} רגילים + {special_count} רגישים)")
    print("-" * 80)
    print()

    if total > 0:
        print("💡 המלצה: נמצאו פרטים אישיים בקובץ.")
        if special_count > 0:
            print(f"⚠️  שים לב: {special_count} פריטים דורשים הגנה מוגברת לפי תיקון 13!")
    else:
        print("✓ לא נמצאו פרטים אישיים")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
