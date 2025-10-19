"""
Image Processor - עיבוד תמונות עם OCR
פרויקט גמר - זיהוי מידע אישי רגיש

מודול לקריאת טקסט מתמונות באמצעות OCR - גרסה מתוקנת
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import io
import os
from typing import Dict, Tuple, Optional
import logging

# הגדרת Tesseract לWindows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ImageProcessor:
    """
    מעבד תמונות עם יכולות OCR מתקדמות
    """

    def __init__(self):
        """אתחול המעבד"""
        self.setup_logging()

        # הגדרות OCR פשוטות ויעילות
        self.tesseract_configs = [
            r'--oem 3 --psm 6 -l eng',         # אנגלית בלבד - הכי אמין
            r'--oem 3 --psm 3 -l eng',         # אנגלית אוטומטי
            r'--oem 3 --psm 6',                # ברירת מחדל
            r'--oem 3 --psm 11 -l eng',        # אנגלית טקסט דליל
        ]

        # בדיקה שTesseract מותקן
        try:
            pytesseract.get_tesseract_version()
            self.logger.info("✅ Tesseract מותקן ופועל")
        except Exception as e:
            self.logger.error(f"❌ בעיה עם Tesseract: {e}")

    def setup_logging(self):
        """הגדרת לוגים"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """עיבוד מקדים פשוט של התמונה"""
        try:
            # המרה לגווני אפור
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # הגדלת התמונה אם צריך
            height, width = gray.shape
            if width < 800:
                scale_factor = 800 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # שיפור ניגודיות
            gray = cv2.equalizeHist(gray)

            # הסרת רעש
            gray = cv2.medianBlur(gray, 3)

            # בינאריזציה
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return binary

        except Exception as e:
            self.logger.error(f"❌ שגיאה בעיבוד מקדים: {e}")
            return image

    def extract_text_from_image(self, image_data, filename: str = "") -> Dict:
        """חילוץ טקסט מתמונה"""
        try:
            # קריאת התמונה
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            elif isinstance(image_data, str):
                cv_image = cv2.imread(image_data)
                if cv_image is None:
                    raise ValueError(f"לא ניתן לקרוא תמונה: {image_data}")
            else:
                cv_image = image_data

            # עיבוד מקדים
            processed_image = self.preprocess_image(cv_image)

            # OCR עם הגדרות שונות
            self.logger.info("🔍 מתחיל OCR...")

            best_text = ""
            best_confidence = 0

            for config in self.tesseract_configs:
                try:
                    # חילוץ טקסט
                    text = pytesseract.image_to_string(processed_image, config=config)

                    # קבלת ציון ודאות
                    try:
                        data = pytesseract.image_to_data(processed_image, config=config,
                                                       output_type=pytesseract.Output.DICT)
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        avg_confidence = np.mean(confidences) if confidences else 0
                    except:
                        # אם לא ניתן לקבל ציון ודאות, נעריך לפי אורך הטקסט
                        avg_confidence = 70 if len(text.strip()) > 10 else 30

                    # בחירת התוצאה הטובה ביותר
                    if (len(text.strip()) > len(best_text.strip()) and
                        avg_confidence > 25 and
                        len(text.strip()) > 2):
                        best_text = text
                        best_confidence = avg_confidence
                        self.logger.info(f"✅ OCR הצליח עם: {config[:20]}...")
                        break  # אם מצאנו תוצאה טובה, נעצור

                except Exception as e:
                    self.logger.warning(f"OCR config נכשל: {e}")
                    continue

            # ניקוי הטקסט
            cleaned_text = self.clean_extracted_text(best_text)

            # תוצאות
            result = {
                'success': True,
                'text': cleaned_text,
                'confidence': best_confidence,
                'filename': filename,
                'character_count': len(cleaned_text),
                'word_count': len(cleaned_text.split()) if cleaned_text else 0
            }

            self.logger.info(f"✅ OCR הושלם: {len(cleaned_text)} תווים, ודאות: {best_confidence:.1f}%")
            return result

        except Exception as e:
            self.logger.error(f"❌ שגיאה בחילוץ טקסט: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': "",
                'confidence': 0,
                'filename': filename
            }

    def clean_extracted_text(self, text: str) -> str:
        """ניקוי הטקסט שחולץ מOCR"""
        if not text:
            return ""

        import re

        # החלפת ריווחים מרובים ברווח אחד
        text = re.sub(r'\s+', ' ', text)

        # הסרת שורות ריקות מרובות
        text = re.sub(r'\n\s*\n', '\n', text)

        # הסרת רווחים מתחילת וסוף
        text = text.strip()

        return text

# פונקציות עזר
def supported_image_formats():
    """רשימת פורמטי תמונה נתמכים"""
    return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']

def is_image_file(filename: str) -> bool:
    """בדיקה אם הקובץ הוא תמונה"""
    if not filename:
        return False

    ext = os.path.splitext(filename.lower())[1]
    return ext in supported_image_formats()

if __name__ == "__main__":
    print("🖼️ בדיקת מעבד התמונות")
    print("=" * 30)

    processor = ImageProcessor()
    print("✅ מעבד התמונות מוכן לשימוש!")