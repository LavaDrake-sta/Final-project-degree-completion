"""
PDF Processor - עיבוד קבצי PDF
פרויקט גמר - זיהוי מידע אישי רגיש

מודול לחילוץ טקסט מקבצי PDF (רגילים וסרוקים)
שיפורים: OCR עברי + לוגים מרכזיים
"""

import fitz  # PyMuPDF
import PyPDF2
import io
import logging
from PIL import Image
import numpy as np
from typing import Dict, List, Optional, Union
import os

try:
    from src.logger_config import get_logger
except ImportError:
    try:
        from logger_config import get_logger
    except ImportError:
        def get_logger(name):
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger(name)



class PDFProcessor:
    """
    מעבד PDF עם תמיכה בקבצים רגילים וסרוקים.
    תומך ב-OCR עברי+אנגלי.
    """

    # OCR configs בסדר עדיפות: עברי+אנגלי → אנגלי בלבד → ברירת מחדל
    OCR_CONFIGS = [
        r'--oem 3 --psm 6 -l heb+eng',
        r'--oem 3 --psm 6 -l heb',
        r'--oem 3 --psm 6 -l eng',
        r'--oem 3 --psm 3',
    ]

    def __init__(self):
        """אתחול המעבד"""
        self.logger = get_logger("PII.Processor.PDF")
        self.logger.info("🔧 אתחול PDFProcessor...")

        try:
            from .image_processor import ImageProcessor
            self.image_processor = ImageProcessor()
            self.ocr_available = True
            self.logger.info("✅ OCR זמין למסמכים סרוקים")
        except ImportError:
            self.image_processor = None
            self.ocr_available = False
            self.logger.warning("⚠️ OCR לא זמין - רק PDF עם טקסט")


    def extract_text_from_pdf(self, pdf_data: Union[str, bytes],
                              filename: str = "") -> Dict:
        """
        חילוץ טקסט מPDF - נסה שיטות שונות
        """
        try:
            # נסה קודם עם PyMuPDF (מתקדם יותר)
            result = self._extract_with_pymupdf(pdf_data, filename)

            if result['success'] and len(result['text'].strip()) > 50:
                return result

            self.logger.info("💡 מנסה שיטה חלופית...")

            # אם לא הצליח, נסה עם PyPDF2
            fallback_result = self._extract_with_pypdf2(pdf_data, filename)

            # החזר את התוצאה הטובה יותר
            if (fallback_result['success'] and
                    len(fallback_result['text']) > len(result['text'])):
                return fallback_result

            return result

        except Exception as e:
            self.logger.error(f"❌ שגיאה כללית בעיבוד PDF: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': "",
                'pages': 0,
                'filename': filename,
                'method': 'none'
            }

    def _extract_with_pymupdf(self, pdf_data: Union[str, bytes],
                              filename: str) -> Dict:
        """
        חילוץ טקסט עם PyMuPDF (תומך גם בOCR)
        """
        try:
            # פתיחת המסמך
            if isinstance(pdf_data, str):
                # נתיב לקובץ
                doc = fitz.open(pdf_data)
            elif isinstance(pdf_data, bytes):
                # נתוני bytes
                doc = fitz.open(stream=pdf_data, filetype="pdf")
            else:
                raise ValueError("סוג נתוני PDF לא נתמך")

            extracted_text = ""
            page_texts = []
            images_processed = 0
            
            # ניתוח סוג המסמך מראש מתוך המטא-דאטה
            metadata = doc.metadata or {}
            creator = str(metadata.get('creator', '')).lower()
            producer = str(metadata.get('producer', '')).lower()
            is_from_word = 'word' in creator or 'word' in producer or 'office' in creator or 'office' in producer
            
            native_text_chars = 0
            ocr_text_chars = 0

            self.logger.info(f"📄 עיבוד PDF: {doc.page_count} עמודים, נוצר מ-Word: {is_from_word}")

            for page_num in range(doc.page_count):
                page = doc[page_num]

                # נסה לחלץ טקסט רגיל
                page_text = page.get_text()
                native_text_chars += len(page_text.strip())

                # אם אין טקסט כלל (מסמך סרוק לחלוטין), נסה OCR על כל העמוד
                if len(page_text.strip()) < 10 and self.ocr_available:
                    self.logger.info(f"🔍 עמוד {page_num + 1}: אין טקסט - מנסה OCR על העמוד")
                    ocr_text = self._ocr_pdf_page(page)
                    if ocr_text:
                        page_text = ocr_text
                        ocr_text_chars += len(ocr_text.strip())
                        images_processed += 1
                elif self.ocr_available:
                    # גם אם יש טקסט, בדוק אם יש תמונות מוטבעות עם טקסט נוסף
                    embedded_ocr_text = self._extract_text_from_embedded_images(page, page_num)
                    if embedded_ocr_text:
                        page_text += "\n" + embedded_ocr_text
                        ocr_text_chars += len(embedded_ocr_text.strip())
                        images_processed += 1

                page_texts.append(page_text)
                extracted_text += f"\n--- עמוד {page_num + 1} ---\n{page_text}\n"

            doc.close()

            # ניקוי הטקסט
            cleaned_text = self._clean_pdf_text(extracted_text)

            # החלטה על סוג המסמך
            if is_from_word:
                if ocr_text_chars > 0 and images_processed > 0:
                    pdf_type = "word_with_images"
                    pdf_type_desc = "מסמך Word שהומר ל-PDF (מכיל גם תמונות שעברו סריקה)"
                else:
                    pdf_type = "word_native"
                    pdf_type_desc = "מסמך Word שהומר ל-PDF (טקסט מקורי)"
            else:
                if native_text_chars < 50 and ocr_text_chars > 0:
                    pdf_type = "scanned"
                    pdf_type_desc = "מסמך סרוק (עבר זיהוי תווים - OCR)"
                elif native_text_chars >= 50 and ocr_text_chars > 0:
                    pdf_type = "mixed"
                    pdf_type_desc = "מסמך מעורב (טקסט מקורי + תמונות שעברו סריקה)"
                elif native_text_chars >= 50:
                    pdf_type = "native"
                    pdf_type_desc = "מסמך PDF רגיל (טקסט מקורי)"
                else:
                    pdf_type = "unknown"
                    pdf_type_desc = "סוג מסמך לא ידוע"

            result = {
                'success': True,
                'text': cleaned_text,
                'pages': len(page_texts),
                'filename': filename,
                'method': 'pymupdf',
                'ocr_pages': images_processed,
                'page_texts': page_texts,
                'character_count': len(cleaned_text),
                'word_count': len(cleaned_text.split()) if cleaned_text else 0,
                'pdf_type': pdf_type,
                'pdf_type_desc': pdf_type_desc,
                'is_from_word': is_from_word
            }

            self.logger.info(f"✅ PyMuPDF: {len(cleaned_text)} תווים מ-{len(page_texts)} עמודים")

            if images_processed > 0:
                self.logger.info(f"🖼️ OCR בוצע על {images_processed} עמודים")

            return result

        except Exception as e:
            self.logger.error(f"❌ שגיאה ב-PyMuPDF: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': "",
                'pages': 0,
                'filename': filename,
                'method': 'pymupdf'
            }

    def _extract_with_pypdf2(self, pdf_data: Union[str, bytes],
                             filename: str) -> Dict:
        """
        חילוץ טקסט עם PyPDF2 (פשוט יותר)
        """
        try:
            if isinstance(pdf_data, str):
                # נתיב לקובץ
                with open(pdf_data, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    pages_text = self._read_pages_pypdf2(pdf_reader)
            elif isinstance(pdf_data, bytes):
                # נתוני bytes
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
                pages_text = self._read_pages_pypdf2(pdf_reader)
            else:
                raise ValueError("סוג נתוני PDF לא נתמך")

            # איחוד כל הטקסט
            full_text = "\n".join(pages_text)
            cleaned_text = self._clean_pdf_text(full_text)

            result = {
                'success': True,
                'text': cleaned_text,
                'pages': len(pages_text),
                'filename': filename,
                'method': 'pypdf2',
                'character_count': len(cleaned_text),
                'word_count': len(cleaned_text.split()) if cleaned_text else 0
            }

            self.logger.info(f"✅ PyPDF2: {len(cleaned_text)} תווים מ-{len(pages_text)} עמודים")
            return result

        except Exception as e:
            self.logger.error(f"❌ שגיאה ב-PyPDF2: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': "",
                'pages': 0,
                'filename': filename,
                'method': 'pypdf2'
            }

    def _read_pages_pypdf2(self, pdf_reader) -> List[str]:
        """קריאת עמודים עם PyPDF2"""
        pages_text = []

        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                pages_text.append(page_text)
            except Exception as e:
                self.logger.warning(f"⚠️ בעיה בעמוד {page_num + 1}: {e}")
                pages_text.append("")

        return pages_text

    def _ocr_pdf_page(self, page) -> str:
        """
        OCR לעמוד PDF סרוק — מנסה configs עברי+אנגלי.
        """
        try:
            if not self.ocr_available:
                return ""

            import pytesseract
            # המרת עמוד לתמונה ברזולוציה גבוהה
            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
            img_data = pix.tobytes("png")

            # ניסיון OCR עם מספר configs
            for config in self.OCR_CONFIGS:
                try:
                    from PIL import Image
                    import io as _io
                    pil_img = Image.open(_io.BytesIO(img_data))
                    text = pytesseract.image_to_string(pil_img, config=config)
                    if text.strip():
                        self.logger.info(
                            f"✅ OCR עמוד הצליח עם config: {config[:30]} | "
                            f"{len(text)} תווים"
                        )
                        return text
                except Exception as e:
                    self.logger.debug(f"  OCR config נכשל ({config[:20]}): {e}")
                    continue

            # fallback: image_processor
            ocr_result = self.image_processor.extract_text_from_image(
                img_data, filename="pdf_page"
            )
            if ocr_result['success']:
                self.logger.info(f"✅ OCR fallback הצליח: {len(ocr_result['text'])} תווים")
                return ocr_result['text']
            else:
                self.logger.warning(f"⚠️ OCR נכשל: {ocr_result.get('error', 'לא ידוע')}")
                return ""

        except Exception as e:
            self.logger.error(f"❌ שגיאה ב-OCR של עמוד: {e}")
            return ""

    def _extract_text_from_embedded_images(self, page, page_num: int) -> str:
        """
        חילוץ טקסט מתמונות מוטבעות בתוך עמוד PDF שכבר מכיל טקסט.
        מטפל במקרה של PDF שמכיל תמונה מוסרקת בתוכו (לא PDF סרוק לחלוטין).
        """
        if not self.ocr_available:
            return ""

        ocr_texts = []

        try:
            # קבלת רשימת התמונות המוטבעות בעמוד
            image_list = page.get_images(full=True)

            if not image_list:
                return ""

            self.logger.info(
                f"🖼️ עמוד {page_num + 1}: נמצאו {len(image_list)} תמונות מוטבעות - מנסה OCR"
            )

            doc = page.parent  # הפניה למסמך

            for img_index, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]  # מזהה התמונה

                    # חילוץ נתוני התמונה
                    base_image = doc.extract_image(xref)
                    if not base_image:
                        continue

                    img_bytes = base_image["image"]
                    img_ext = base_image["ext"]  # png / jpeg וכדומה

                    # בדיקת גודל מינימלי - תמונות קטנות הן לרוב אייקונים/לוגו
                    if len(img_bytes) < 5000:  # פחות מ-5KB
                        self.logger.debug(
                            f"  ↳ תמונה {img_index + 1}: קטנה מדי ({len(img_bytes)} bytes), מדלג"
                        )
                        continue

                    self.logger.info(
                        f"  ↳ תמונה {img_index + 1}: מריץ OCR ({img_ext}, {len(img_bytes)} bytes)"
                    )

                    # OCR על התמונה המוטבעת
                    ocr_result = self.image_processor.extract_text_from_image(
                        img_bytes, filename=f"embedded_image_{page_num}_{img_index}"
                    )

                    if ocr_result['success'] and len(ocr_result['text'].strip()) > 5:
                        ocr_texts.append(ocr_result['text'].strip())
                        self.logger.info(
                            f"  ↳ ✅ OCR הצליח: {len(ocr_result['text'])} תווים"
                        )
                    else:
                        self.logger.debug(f"  ↳ OCR לא מצא טקסט בתמונה {img_index + 1}")

                except Exception as e:
                    self.logger.warning(f"  ↳ ⚠️ שגיאה בעיבוד תמונה {img_index + 1}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"❌ שגיאה בחילוץ תמונות מוטבעות מעמוד {page_num + 1}: {e}")

        if ocr_texts:
            combined = "\n".join(ocr_texts)
            self.logger.info(
                f"✅ עמוד {page_num + 1}: חולץ טקסט מ-{len(ocr_texts)} תמונות מוטבעות"
            )
            return combined

        return ""

    def _clean_pdf_text(self, text: str) -> str:
        """
        ניקוי טקסט שחולץ מPDF
        """
        if not text:
            return ""

        import re

        # הסרת תווי בקרה מיוחדים
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)

        # החלפת ריווחים מרובים ברווח אחד
        text = re.sub(r'[ \t]+', ' ', text)

        # ניקוי שורות ריקות מרובות
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

        # הסרת רווחים מתחילת וסוף השורות
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)

        return text.strip()

    def get_pdf_info(self, pdf_data: Union[str, bytes]) -> Dict:
        """
        קבלת מידע על קובץ PDF
        """
        try:
            if isinstance(pdf_data, str):
                doc = fitz.open(pdf_data)
            else:
                doc = fitz.open(stream=pdf_data, filetype="pdf")

            metadata = doc.metadata

            info = {
                'pages': doc.page_count,
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'encrypted': doc.needs_pass,
                'file_size': len(pdf_data) if isinstance(pdf_data, bytes) else os.path.getsize(pdf_data)
            }

            doc.close()
            return info

        except Exception as e:
            self.logger.error(f"❌ שגיאה בקבלת מידע PDF: {e}")
            return {}


# פונקציות עזר
def is_pdf_file(filename: str) -> bool:
    """בדיקה אם הקובץ הוא PDF"""
    if not filename:
        return False
    return filename.lower().endswith('.pdf')


def estimate_pdf_type(text_length: int, pages: int) -> str:
    """הערכה אם ה-PDF הוא טקסט או סרוק"""
    if pages == 0:
        return "unknown"

    avg_chars_per_page = text_length / pages

    if avg_chars_per_page < 100:
        return "scanned"  # כנראה סרוק
    elif avg_chars_per_page > 500:
        return "text"  # כנראה עם טקסט
    else:
        return "mixed"  # מעורב


# בדיקה מהירה
if __name__ == "__main__":
    print("📄 בדיקת מעבד PDF")
    print("=" * 25)

    processor = PDFProcessor()

    # בדיקה עם PDF לדוגמה (אם יש)
    test_pdf_path = "test_document.pdf"
    if os.path.exists(test_pdf_path):
        print(f"📄 בודק PDF: {test_pdf_path}")

        # מידע על הקובץ
        info = processor.get_pdf_info(test_pdf_path)
        print(f"📊 {info.get('pages', 0)} עמודים")

        # חילוץ טקסט
        result = processor.extract_text_from_pdf(test_pdf_path)

        if result['success']:
            print(f"✅ הצלחה! חולץ {len(result['text'])} תווים")
            print(f"📖 שיטה: {result['method']}")
            if result.get('ocr_pages', 0) > 0:
                print(f"🖼️ OCR: {result['ocr_pages']} עמודים")

            if result['text']:
                print(f"📝 דוגמה: {result['text'][:150]}...")
        else:
            print(f"❌ שגיאה: {result['error']}")
    else:
        print("💡 לבדיקה, שים קובץ PDF בשם 'test_document.pdf' בתיקייה")

    print("\n✅ מעבד PDF מוכן לשימוש!")