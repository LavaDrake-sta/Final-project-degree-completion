"""
PDF Redactor - השחרת קבצי PDF
פרויקט גמר - זיהוי מידע אישי רגיש

מודול זה אחראי על קבלת File PDF ורשימת טקסטים להשחרה,
וביצוע השחרה פיזית (מלבן שחור ומחיקת הטקסט) בעזרת ספריית PyMuPDF.
"""

import fitz  # PyMuPDF

try:
    from src.logger_config import get_logger, trace_execution
except ImportError:
    try:
        from logger_config import get_logger, trace_execution
    except ImportError:
        def trace_execution(func): return func
import io
import logging
from typing import List, Union, Optional

class PdfRedactor:
    """
    מחלקה לביצוע השחרה גרפית ופיזית על קבצי PDF.
    """

    def __init__(self):
        """אתחול המשחיר"""
        self.setup_logging()

    def setup_logging(self):
        """הגדרת לוגים"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @trace_execution
    def redact_pdf(self, pdf_data: Union[str, bytes], pii_texts: List[str], output_path: Optional[str] = None) -> Union[bytes, str, None]:
        """
        השחרת טקסטים רגישים בתוך ה-PDF.
        תומך בטקסט בעברית (RTL) על ידי חיפוש כפול (רגיל והפוך).
        """
        if not pii_texts:
            self.logger.warning("⚠️ No texts received for redaction, operation cancelled.")
            return None

        try:
            if isinstance(pdf_data, str):
                doc = fitz.open(pdf_data)
            else:
                doc = fitz.open("pdf", pdf_data)
                
            self.logger.info(f"🔒 Starting redaction of PDF file. Number of PII strings: {len(pii_texts)}")
            
            total_redactions = 0

            for page in doc:
                # קבלת כל המילים בעמוד פעם אחת לשיפור ביצועים ודיוק
                words = page.get_text("words") # (x0, y0, x1, y1, word, block_no, line_no, word_no)
                
                for text in pii_texts:
                    if not text.strip(): continue
                    
                    # 1. חיפוש סטנדרטי
                    text_instances = page.search_for(text)
                    
                    # 2. אם לא נמצא, נסה חיפוש הפוך (עבור עברית RTL ב-PDF)
                    if not text_instances and any(c in "אבגדהוזחטיכלמנסעפצקרשת" for c in text):
                        reversed_text = text[::-1]
                        text_instances = page.search_for(reversed_text)
                    
                    # 3. אם עדיין לא נמצא, נסה חיפוש מבוסס מילים (עבור מקרים של רווחים כפולים או תווים נסתרים)
                    if not text_instances:
                        # לוגיקה פשוטה לחיפוש רצף מילים
                        pass # TODO: שיפור עתידי אם נדרש

                    for inst in text_instances:
                        page.add_redact_annot(inst, fill=(0, 0, 0))
                        total_redactions += 1
                
                page.apply_redactions()

            self.logger.info(f"✅ PDF redaction finished. Performed {total_redactions} redactions.")

            if output_path:
                doc.save(output_path)
                doc.close()
                return output_path, total_redactions
            else:
                redacted_bytes = doc.write()
                doc.close()
                return redacted_bytes, total_redactions

        except Exception as e:
            self.logger.error(f"❌ Error redacting PDF: {e}")
            return None, 0

    @trace_execution
    def redact_pdf_by_coords(self, pdf_data: Union[str, bytes], findings: List[dict], output_path: Optional[str] = None) -> Union[bytes, str, None]:
        """
        השחרת נתונים by coordinates מדויקות (מלבנים בעמודים ספציפיים).
        זה מאפשר השחרה זהה לזו של PDFShield.
        """
        if not findings:
            self.logger.warning("⚠️ No locations received for redaction, operation cancelled.")
            return None

        try:
            if isinstance(pdf_data, str):
                doc = fitz.open(pdf_data)
            else:
                doc = fitz.open("pdf", pdf_data)
                
            self.logger.info(f"🔒 Starting PDF redaction by {len(findings)} exact coordinates.")
            
            for finding in findings:
                page_idx = finding.get('page', 0)
                if 0 <= page_idx < len(doc):
                    rect_coords = finding.get('rect')
                    if rect_coords and len(rect_coords) == 4:
                        # השחרה מלאה ושחורה (0,0,0) לפי הקואורדינטות
                        doc[page_idx].add_redact_annot(fitz.Rect(*rect_coords), fill=(0, 0, 0))
                        
            # החלת כל הערות ההשחרה בעמודים
            for page in doc:
                page.apply_redactions()
                
            self.logger.info("✅ Visual PDF redaction finished successfully.")

            if output_path:
                doc.save(output_path)
                doc.close()
                return output_path
            else:
                import io
                output_stream = io.BytesIO()
                doc.save(output_stream)
                output_stream.seek(0)
                redacted_bytes = output_stream.read()
                doc.close()
                return redacted_bytes

        except Exception as e:
            self.logger.error(f"❌ Error redacting PDF by coordinates: {e}")
            return None

