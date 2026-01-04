"""
Tesseract Setup - הגדרה גלובלית של Tesseract
פרויקט גמר - זיהוי מידע אישי רגיש

הגדרה מרכזית של Tesseract עבור כל המערכת
"""

import pytesseract
import os
import platform


def setup_tesseract():
    """הגדרת Tesseract לפי מערכת ההפעלה"""

    system = platform.system()

    if system == "Windows":
        # נתיבים אפשריים ב-Windows
        windows_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe'
        ]

        for path in windows_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True

    elif system == "Darwin":  # macOS
        # macOS עם Homebrew
        mac_paths = [
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract'
        ]

        for path in mac_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True

    # Linux ו-macOS בדרך כלל לא צריכים הגדרה מיוחדת

    return False


def verify_tesseract():
    """וידוא שTesseract עובד"""

    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract {version} מוכן")
        return True
    except Exception as e:
        print(f"❌ Tesseract לא זמין: {e}")
        return False


# הגדרה אוטומטית בעת ייבוא המודול
setup_tesseract()