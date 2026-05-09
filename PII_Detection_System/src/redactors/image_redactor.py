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

try:
    from src.logger_config import get_logger, trace_execution
except ImportError:
    try:
        from logger_config import get_logger, trace_execution
    except ImportError:
        def trace_execution(func): return func

import pytesseract
from PIL import Image, ImageDraw

class ImageRedactor:
    """
    מחלקה לביצוע השחרה גרפית על תמונות.
    עובדת על PNG, JPG, BMP וכל פורמט שנתמך על ידי Pillow.
    """

    def __init__(self):
        self._setup_logging()

    @trace_execution
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @trace_execution
    def _find_word_boxes_with_easyocr(self, image: Image.Image, pii_texts: List[str]) -> List[tuple]:
        """
        מחפש את המיקום הפיזי של כל מחרוזת PII בתמונה בעזרת EasyOCR.
        """
        import numpy as np
        try:
            from app import load_ocr_engine
            reader = load_ocr_engine()
        except:
            # Fallback if app import fails
            import easyocr
            reader = easyocr.Reader(['heb', 'en'])

        img_array = np.array(image)
        results = reader.readtext(img_array)
        
        boxes_to_redact = []
        for bbox, text, conf in results:
            clean_text = text.strip()
            if not clean_text: continue
            
            for pii in pii_texts:
                if pii and (pii.lower() in clean_text.lower() or pii[::-1].lower() in clean_text.lower()):
                    x_coords = [p[0] for p in bbox]
                    y_coords = [p[1] for p in bbox]
                    rect = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
                    boxes_to_redact.append(rect)
                    self.logger.info(f"Found PII '{pii}' at {rect}")
                    
        return boxes_to_redact

    @trace_execution
    def _find_word_boxes(self, image: Image.Image, pii_texts: List[str]) -> List[tuple]:
        """חיפוש בעזרת Tesseract (Fallback)"""
        boxes_to_redact = []
        try:
            data = pytesseract.image_to_data(image, lang='eng+heb', output_type=pytesseract.Output.DICT)
            n_boxes = len(data['text'])
            words = []
            for i in range(n_boxes):
                word = str(data['text'][i]).strip()
                if word and int(data['conf'][i]) > 10:
                    words.append({
                        'text': word,
                        'left': int(data['left'][i]),
                        'top': int(data['top'][i]),
                        'width': int(data['width'][i]),
                        'height': int(data['height'][i]),
                    })

            for pii in pii_texts:
                if not pii: continue
                pii_clean = pii.strip()
                for w in words:
                    if pii_clean.lower() in w['text'].lower():
                        boxes_to_redact.append((w['left'], w['top'], w['left']+w['width'], w['top']+w['height']))
        except Exception as e:
            self.logger.error(f"Tesseract fallback failed: {e}")
        return boxes_to_redact

    @trace_execution
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
            image_data: נתיב לFile, bytes, או אובייקט PIL Image
            pii_texts: רשימת טקסטים להשחרה (כפי שחולצו על ידי ה-PIIDetector)
            output_path: נתיב לשמירת התמונה. אם None, יוחזרו bytes.
            fill_color: צבע המלבן (RGB tuple). ברירת מחדל שחור.

        Returns:
            bytes של התמונה המושחרת, נתיב הFile, או None במקרה כשל.
        """
        if not pii_texts:
            self.logger.warning("No texts received for redaction.")
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

            self.logger.info(f"🔒 Starting image redaction. Size: {image.size}. PII strings: {len(pii_texts)}")

            # 2. מאתר את המיקום של כל PII בתמונה - ניסיון ראשון עם EasyOCR
            boxes = self._find_word_boxes_with_easyocr(image, pii_texts)
            
            # אם לא נמצא, נסה עם Tesseract
            if not boxes:
                boxes = self._find_word_boxes(image, pii_texts)

            if not boxes:
                self.logger.warning("⚠️ No boxes found to redact. OCR might not have detected the texts in the image.")
                return image_data, 0

            # 3. מצייר מלבן שחור מעל כל אזור PII
            draw = ImageDraw.Draw(image)
            for (x1, y1, x2, y2) in boxes:
                # מוסיף שוליים קטנים (padding) כדי לכסות לגמרי
                padding = 3
                draw.rectangle(
                    [x1 - padding, y1 - padding, x2 + padding, y2 + padding],
                    fill=fill_color
                )

            self.logger.info(f"✅ Image redaction finished. Performed {len(boxes)} redactions.")

            # 4. שמירה
            if output_path:
                image.save(output_path)
                return output_path, len(boxes)
            else:
                output = io.BytesIO()
                # שמירה בפורמט PNG כדי לשמור על איכות
                image.save(output, format='PNG')
                return output.getvalue(), len(boxes)

        except Exception as e:
            self.logger.error(f"❌ Error redacting image: {e}")
            return None
