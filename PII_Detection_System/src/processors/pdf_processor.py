"""
PDF Processor - עיבוד קבצי PDF
פרויקט גמר - זיהוי מידע אישי רגיש

מודול לחילוץ טקסט מקבצי PDF (רגילים וסרוקים)
"""

import fitz  # PyMuPDF
import PyPDF2
import io
import logging
from PIL import Image
import numpy as np
from typing import Dict, List, Optional, Union
import os


class PDFProcessor:
    """
    מעבד PDF עם תמיכה בקבצים רגילים וסרוקים
    """

    def __init__(self):
        """אתחול המעבד"""
        self.setup_logging()

        # ייבוא מעבד התמונות לOCR
        try:
            from .image_processor import ImageProcessor
            self.image_processor = ImageProcessor()
            self.ocr_available = True
            self.logger.info("✅ OCR זמין למסמכים סרוקים")
        except ImportError:
            self.image_processor = None
            self.ocr_available = False
            self.logger.warning("⚠️ OCR לא זמין - רק PDF עם טקסט")

    def setup_logging(self):
        """הגדרת לוגים"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

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

            self.logger.info(f"📄 עיבוד PDF: {doc.page_count} עמודים")

            for page_num in range(doc.page_count):
                page = doc[page_num]

                # נסה לחלץ טקסט רגיל
                page_text = page.get_text()

                # אם אין טקסט (מסמך סרוק), נסה OCR
                if len(page_text.strip()) < 10 and self.ocr_available:
                    self.logger.info(f"🔍 עמוד {page_num + 1}: מנסה OCR")
                    ocr_text = self._ocr_pdf_page(page)
                    if ocr_text:
                        page_text = ocr_text
                        images_processed += 1

                page_texts.append(page_text)
                extracted_text += f"\n--- עמוד {page_num + 1} ---\n{page_text}\n"

            doc.close()

            # ניקוי הטקסט
            cleaned_text = self._clean_pdf_text(extracted_text)

            result = {
                'success': True,
                'text': cleaned_text,
                'pages': len(page_texts),
                'filename': filename,
                'method': 'pymupdf',
                'ocr_pages': images_processed,
                'page_texts': page_texts,
                'character_count': len(cleaned_text),
                'word_count': len(cleaned_text.split()) if cleaned_text else 0
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
        OCR לעמוד PDF סרוק
        """
        try:
            if not self.ocr_available:
                return ""

            # המרת העמוד לתמונה
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # הגדלה x2
            img_data = pix.tobytes("png")

            # OCR על התמונה
            ocr_result = self.image_processor.extract_text_from_image(
                img_data, filename="pdf_page"
            )

            if ocr_result['success']:
                return ocr_result['text']
            else:
                self.logger.warning(f"⚠️ OCR נכשל: {ocr_result.get('error', 'לא ידוע')}")
                return ""

        except Exception as e:
            self.logger.error(f"❌ שגיאה ב-OCR של עמוד: {e}")
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