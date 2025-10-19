"""
בדיקת OCR - מה בדיוק קורה?
"""

import pytesseract
from PIL import Image
import sys
import os

# הגדרת נתיב Tesseract (חשוב!)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_simple_ocr():
    """בדיקה פשוטה של OCR"""

    print("🔍 בדיקת OCR על התמונה")
    print("=" * 30)

    image_path = "data/test_images/numbers_only.png"

    if not os.path.exists(image_path):
        print(f"❌ התמונה לא נמצאת: {image_path}")
        return

    try:
        # טעינת התמונה
        img = Image.open(image_path)
        print(f"✅ תמונה נטענה: {img.size}")

        # בדיקת Tesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")

        # OCR עם הגדרות שונות
        configs = [
            ('Default', ''),
            ('English only', '--oem 3 --psm 6 -l eng'),
            ('Numbers focus', '--oem 3 --psm 8 -l eng'),
            ('Single block', '--oem 3 --psm 6'),
            ('Sparse text', '--oem 3 --psm 11 -l eng')
        ]

        for name, config in configs:
            try:
                print(f"\n--- {name} ---")
                text = pytesseract.image_to_string(img, config=config)
                print(f"Text: '{text.strip()}'")
                print(f"Length: {len(text.strip())}")

                # קבלת ציון ודאות
                try:
                    data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    if confidences:
                        avg_conf = sum(confidences) / len(confidences)
                        print(f"Confidence: {avg_conf:.1f}%")
                    else:
                        print("Confidence: No valid data")
                except Exception as e:
                    print(f"Confidence error: {e}")

            except Exception as e:
                print(f"❌ Config failed: {e}")

        # בדיקה עם הטקסט הטוב ביותר
        print(f"\n--- Final Test ---")
        best_text = pytesseract.image_to_string(img, config='--oem 3 --psm 6 -l eng')
        print(f"Best text: '{best_text}'")

        if best_text.strip():
            # בדיקת זיהוי PII
            print(f"\n--- PII Detection Test ---")

            # ייבוא הזיהוי שלנו
            sys.path.append('src')
            from detectors.basic_detector import BasicPIIDetector

            detector = BasicPIIDetector()
            results = detector.analyze_text(best_text)

            print(f"PII Results: {results['summary']}")
            print(f"Matches found: {len(results['matches'])}")

            for match in results['matches']:
                print(f"  - {match.text} ({match.category})")

    except Exception as e:
        print(f"❌ שגיאה כללית: {e}")

def test_tesseract_installation():
    """בדיקת התקנת Tesseract"""

    print("🔧 בדיקת התקנת Tesseract")
    print("=" * 25)

    try:
        # בדיקת גרסה
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract מותקן: {version}")

        # בדיקת שפות זמינות
        try:
            langs = pytesseract.get_languages()
            print(f"✅ שפות זמינות: {langs}")

            if 'eng' in langs:
                print("✅ אנגלית זמינה")
            else:
                print("❌ אנגלית לא זמינה")

            if 'heb' in langs:
                print("✅ עברית זמינה")
            else:
                print("⚠️ עברית לא זמינה")

        except Exception as e:
            print(f"⚠️ לא ניתן לקבל רשימת שפות: {e}")

    except Exception as e:
        print(f"❌ Tesseract לא מותקן או לא נמצא: {e}")
        print("💡 הוראות התקנה:")
        print("   Windows: הורד מ- https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Ubuntu: sudo apt install tesseract-ocr")
        print("   MacOS: brew install tesseract")

if __name__ == "__main__":
    test_tesseract_installation()
    print("\n" + "="*50 + "\n")
    test_simple_ocr()