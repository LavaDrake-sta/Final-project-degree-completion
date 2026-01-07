"""
הגדרת נתיב Tesseract עבור Windows
"""

import pytesseract
import os

# הגדרת נתיב Tesseract (עדכן את הנתיב לפי ההתקנה שלך)
TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Tesseract-OCR\tesseract.exe',
    r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME'))
]


def setup_tesseract():
    """מציאה והגדרה של Tesseract"""

    print("🔍 מחפש Tesseract...")

    # נסה למצוא את Tesseract
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"✅ Tesseract נמצא ב: {path}")

            # בדיקה שזה עובד
            try:
                version = pytesseract.get_tesseract_version()
                print(f"✅ Tesseract גרסה: {version}")
                return True
            except Exception as e:
                print(f"❌ Tesseract לא עובד: {e}")
                continue

    # אם לא נמצא, נסה לחפש במקומות אחרים
    print("⚠️ Tesseract לא נמצא בנתיבים הרגילים")

    # חיפוש אוטומטי
    for drive in ['C:', 'D:']:
        for root, dirs, files in os.walk(drive + '\\'):
            if 'tesseract.exe' in files:
                potential_path = os.path.join(root, 'tesseract.exe')
                print(f"💡 נמצא Tesseract ב: {potential_path}")

                # נסה להגדיר
                try:
                    pytesseract.pytesseract.tesseract_cmd = potential_path
                    version = pytesseract.get_tesseract_version()
                    print(f"✅ Tesseract עובד! גרסה: {version}")
                    return True
                except:
                    continue

            # אל תחפש יותר מדי עמוק
            if len(root.split('\\')) > 3:
                dirs.clear()

    print("❌ Tesseract לא נמצא במערכת")
    return False


def test_tesseract_manual():
    """בדיקה ידנית - הזן נתיב בעצמך"""

    print("\n🔧 בדיקה ידנית")
    print("אם אתה יודע איפה התקנת את Tesseract, הזן את הנתיב:")
    print("דוגמה: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")

    manual_path = input("נתיב ל-tesseract.exe (או Enter לדלג): ").strip()

    if manual_path and os.path.exists(manual_path):
        try:
            pytesseract.pytesseract.tesseract_cmd = manual_path
            version = pytesseract.get_tesseract_version()
            print(f"✅ הצלחה! Tesseract גרסה: {version}")

            # שמירת הנתיב לשימוש עתידי
            with open('tesseract_path.txt', 'w') as f:
                f.write(manual_path)
            print(f"💾 הנתיב נשמר ב-tesseract_path.txt")
            return True

        except Exception as e:
            print(f"❌ הנתיב לא עובד: {e}")

    return False


if __name__ == "__main__":
    print("⚙️ הגדרת Tesseract עבור Windows")
    print("=" * 35)

    # נסה הגדרה אוטומטית
    if setup_tesseract():
        print("\n🎉 Tesseract מוכן לשימוש!")
        print("עכשיו נסה שוב: python debug_ocr.py")
    else:
        # אם לא הצליח, נסה הגדרה ידנית
        if test_tesseract_manual():
            print("\n🎉 Tesseract מוכן לשימוש!")
        else:
            print("\n❌ Tesseract עדיין לא מוגדר")
            print("💡 וודא שהתקנת את Tesseract מ:")
            print("   https://github.com/UB-Mannheim/tesseract/wiki")
            print("   ואחר כך הפעל שוב את הסקריפט הזה")