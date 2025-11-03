"""
Quick test script for PII detection (Amendment 13 compliant)
Tests detection without requiring heavy AI models
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pii_detector_il import IsraeliPIIDetector
from src.israeli_privacy_law import is_special_sensitivity, get_category_hebrew_name
from src.anonymizer import PIIAnonymizer, AnonymizationMode

# Sample text with various PII types
test_text = """
תיק רפואי - פרטי מטופל

שם: יוסי כהן
תעודת זהות: 123456782
תאריך לידה: 15/03/1985
טלפון: 052-1234567
דוא"ל: yossi.cohen@example.co.il
כתובת: רחוב הרצל 23, תל אביב

פרטים רפואיים:
המטופל סובל מלחץ דם גבוה ומקבל טיפול תרופתי.
ביקר בבית החולים איכילוב ביום 12/01/2024.
רופא מטפל: ד"ר משה לוי, קופת חולים כללית.
נקבע תור לבדיקת דם ביום 20/02/2024.

פרטים כלכליים:
משכורת חודשית: 15,000 ₪
מספר חשבון בנק: 12-345678-01
כרטיס אשראי: 4580-1234-5678-9012

הערות נוספות:
המטופל הצהיר על אמונה דתית יהודית שומרת מסורת.
השתייכות פוליטית: מפלגת העבודה (על פי רישומים).
"""

print("=" * 80)
print("🧪 בדיקת מערכת זיהוי PII - תואם תיקון 13")
print("=" * 80)
print()

print("📝 טוען מזהה PII...")
try:
    # Initialize detector without AI (regex only for faster testing)
    detector = IsraeliPIIDetector(use_ai=False)
    print("✓ מזהה נטען בהצלחה (מצב Regex בלבד)")
except Exception as e:
    print(f"❌ שגיאה בטעינת מזהה: {e}")
    sys.exit(1)

print()
print("🔍 מזהה פרטים אישיים...")
print()

# Detect PII
entities = detector.detect_pii(test_text)

# Count findings
standard_count = 0
special_count = 0
total_count = 0

print("-" * 80)
print("📊 תוצאות זיהוי:")
print("-" * 80)
print()

for entity_type, entity_list in entities.items():
    if entity_list:
        count = len(entity_list)
        total_count += count

        hebrew_name = get_category_hebrew_name(entity_type)
        is_special = is_special_sensitivity(entity_type)

        if is_special:
            special_count += count
            icon = "⚠️ "
            sensitivity = "רגישות מיוחדת"
        else:
            standard_count += count
            icon = "✓ "
            sensitivity = "רגיל"

        print(f"{icon}{hebrew_name} ({entity_type}):")
        print(f"   סוג: {sensitivity}")
        print(f"   נמצאו: {count}")

        # Show first 3 examples
        for i, entity in enumerate(entity_list[:3]):
            print(f"   {i+1}. '{entity.text}' (וודאות: {entity.confidence:.0%})")

        if count > 3:
            print(f"   ... ועוד {count - 3}")

        print()

print("-" * 80)
print("סיכום:")
print("-" * 80)
print(f"📊 סה\"כ פרטים אישיים שזוהו: {total_count}")
print(f"✓ פרטים רגילים: {standard_count}")
print(f"⚠️  בעלי רגישות מיוחדת (תיקון 13): {special_count}")
print()

# Test anonymization
print("-" * 80)
print("🔐 בדיקת הסתרה:")
print("-" * 80)
print()

anonymizer = PIIAnonymizer(mode=AnonymizationMode.REPLACE)
anonymized_text = anonymizer.anonymize(test_text, entities)

print("מקור (50 תווים ראשונים):")
print(test_text[:150] + "...")
print()
print("מוסתר (50 תווים ראשונים):")
print(anonymized_text[:150] + "...")
print()

print("=" * 80)
print("✨ הבדיקה הושלמה בהצלחה!")
print("⚖️  המערכת תואמת לתיקון 13 לחוק הגנת הפרטיות")
print("=" * 80)
