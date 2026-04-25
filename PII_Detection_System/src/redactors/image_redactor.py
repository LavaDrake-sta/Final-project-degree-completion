"""
Image Redactor - השחרת תמונות
פרויקט גמר - זיהוי מידע אישי רגיש

מודול זה מקבל תמונה ורשימת טקסטים להשחרה.
הוא משתמש ב-pytesseract.image_to_data כדי לאתר
את המיקום הפיזי המדויק (x, y, w, h) של כל מילה בתמונה,
ולאחר מכן מצייר מלבן שחור מעליה בעזרת Pillow.
"""

import io
import logging
from typing import List, Union, Optional

import pytesseract
from PIL import Image, ImageDraw

class ImageRedactor:
    """
    מחלקה לביצוע השחרה גרפית על תמונות.
    עובדת על PNG, JPG, BMP וכל פורמט שנתמך על ידי Pillow.
    """

    def __init__(self):
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _find_word_boxes(self, image: Image.Image, pii_texts: List[str]) -> List[tuple]:
        """
        מחפש את המיקום הפיזי של כל מחרוזת PII בתמונה.
        מחזיר רשימה של tuples: (x, y, x+w, y+h) - קואורדינטות המלבן להשחרה.

        הלוגיקה:
        1. מריץ image_to_data שמחזיר טבלה של כל מילה + מיקומה.
        2. עבור כל PII text - בודק אם מילה/מחרוזת מופיעה בנתונים.
        3. אם PII מורכב מכמה מילים - מאחד את המלבנים שלהן.
        """
        boxes_to_redact = []

        try:
            # image_to_data מחזיר DataFrame-style string עם עמודות:
            # level, page_num, block_num, par_num, line_num, word_num,
            # left, top, width, height, conf, text
            data = pytesseract.image_to_data(
                image,
                lang='eng+heb',
                output_type=pytesseract.Output.DICT
            )

            n_boxes = len(data['text'])

            # בנה רשימת מילים עם הקואורדינטות שלהן (מסנן מילים ריקות)
            words = []
            for i in range(n_boxes):
                word = str(data['text'][i]).strip()
                if word and int(data['conf'][i]) > 10:  # סף ודאות מינימלי
                    words.append({
                        'text': word,
                        'left': int(data['left'][i]),
                        'top': int(data['top'][i]),
                        'width': int(data['width'][i]),
                        'height': int(data['height'][i]),
                    })

            # עבור כל PII שצריך להשחיר
            for pii in pii_texts:
                if not pii or not pii.strip():
                    continue

                pii_clean = pii.strip()
                pii_words = pii_clean.split()  # מפצל PII למילים בודדות

                if len(pii_words) == 1:
                    # PII מילה בודדת - חפש ישירות
                    for w in words:
                        if pii_clean.lower() in w['text'].lower():
                            x1 = w['left']
                            y1 = w['top']
                            x2 = w['left'] + w['width']
                            y2 = w['top'] + w['height']
                            boxes_to_redact.append((x1, y1, x2, y2))
                            self.logger.info(f"נמצא PII '{pii_clean}' בקואורדינטות ({x1},{y1},{x2},{y2})")
                else:
                    # PII ממספר מילים - חפש רצף של מילים תואמות
                    for i in range(len(words) - len(pii_words) + 1):
                        match = True
                        for j, pii_word in enumerate(pii_words):
                            if pii_word.lower() not in words[i + j]['text'].lower():
                                match = False
                                break
                        if match:
                            # מאחד את כל המלבנים של המילים הרצופות למלבן אחד
                            matched_words = words[i: i + len(pii_words)]
                            x1 = min(w['left'] for w in matched_words)
                            y1 = min(w['top'] for w in matched_words)
                            x2 = max(w['left'] + w['width'] for w in matched_words)
                            y2 = max(w['top'] + w['height'] for w in matched_words)
                            boxes_to_redact.append((x1, y1, x2, y2))
                            self.logger.info(f"נמצא PII מרובה מילים '{pii_clean}' בקואורדינטות ({x1},{y1},{x2},{y2})")

        except Exception as e:
            self.logger.error(f"שגיאה בחיפוש מיקום PII בתמונה: {e}")

        return boxes_to_redact

    def redact_image(
        self,
        image_data: Union[str, bytes, Image.Image],
        pii_texts: List[str],
        output_path: Optional[str] = None,
        fill_color: tuple = (0, 0, 0)  # ברירת מחדל: שחור
    ) -> Union[bytes, str, None]:
        """
        השחרת אזורים בתמונה המכילים PII על ידי ציור מלבנים צבועים.

        Args:
            image_data: נתיב לקובץ, bytes, או אובייקט PIL Image
            pii_texts: רשימת טקסטים להשחרה (כפי שחולצו על ידי ה-PIIDetector)
            output_path: נתיב לשמירת התמונה. אם None, יוחזרו bytes.
            fill_color: צבע המלבן (RGB tuple). ברירת מחדל שחור.

        Returns:
            bytes של התמונה המושחרת, נתיב הקובץ, או None במקרה כשל.
        """
        if not pii_texts:
            self.logger.warning("לא התקבלו טקסטים להשחרה.")
            return None

        try:
            # 1. טעינת התמונה
            if isinstance(image_data, Image.Image):
                image = image_data.copy()
            elif isinstance(image_data, str):
                image = Image.open(image_data)
            else:
                image = Image.open(io.BytesIO(image_data))

            # המרה ל-RGB אם נדרש (RGBA, L וכו')
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')

            self.logger.info(f"🔒 מתחיל השחרת תמונה. גודל: {image.size}. מחרוזות PII: {len(pii_texts)}")

            # 2. מאתר את המיקום של כל PII בתמונה
            boxes = self._find_word_boxes(image, pii_texts)

            if not boxes:
                self.logger.warning("⚠️ לא נמצאו תיבות להשחרה. ייתכן שה-OCR לא זיהה את הטקסטים בתמונה.")
                return None

            # 3. מצייר מלבן שחור מעל כל אזור PII
            draw = ImageDraw.Draw(image)
            for (x1, y1, x2, y2) in boxes:
                # מוסיף שוליים קטנים (padding) כדי לכסות לגמרי
                padding = 3
                draw.rectangle(
                    [x1 - padding, y1 - padding, x2 + padding, y2 + padding],
                    fill=fill_color
                )

            self.logger.info(f"✅ השחרת תמונה הסתיימה. בוצעו {len(boxes)} השחרות.")

            # 4. שמירה
            if output_path:
                image.save(output_path)
                return output_path
            else:
                output = io.BytesIO()
                # שמירה בפורמט PNG כדי לשמור על איכות
                image.save(output, format='PNG')
                return output.getvalue()

        except Exception as e:
            self.logger.error(f"❌ שגיאה בהשחרת התמונה: {e}")
            return None
