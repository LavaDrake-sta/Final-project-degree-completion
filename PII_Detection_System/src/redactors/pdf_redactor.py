"""
PDF Redactor - השחרת קבצי PDF
פרויקט גמר - זיהוי מידע אישי רגיש

מודול זה אחראי על קבלת קובץ PDF ורשימת טקסטים להשחרה,
וביצוע השחרה פיזית (מלבן שחור ומחיקת הטקסט) בעזרת ספריית PyMuPDF.
"""

import fitz  # PyMuPDF
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

    def redact_pdf(self, pdf_data: Union[str, bytes], pii_texts: List[str], output_path: Optional[str] = None) -> Union[bytes, str, None]:
        """
        השחרת טקסטים רגישים בתוך ה-PDF.
        
        Args:
            pdf_data: נתיב לקובץ ה-PDF או אובייקט bytes של הקובץ
            pii_texts: רשימת מחרוזות רגישות להשחרה
            output_path: נתיב לשמירת הקובץ המושחר (אופציונלי, אם לא סופק יוחזר אובייקט bytes)
            
        Returns:
            נתיב הקובץ החדש (אם סופק output_path), 
            או אובייקט bytes של הקובץ המושחר,
            או None במקרה של שגיאה.
        """
        if not pii_texts:
            self.logger.warning("⚠️ לא התקבלו טקסטים להשחרה, הפעולה מבוטלת.")
            return None

        try:
            # 1. טעינת הקובץ
            if isinstance(pdf_data, str):
                doc = fitz.open(pdf_data)
            else:
                doc = fitz.open("pdf", pdf_data)
                
            self.logger.info(f"🔒 מתחיל השחרת קובץ PDF. מספר מחרוזות PII להשחרה: {len(pii_texts)}")
            
            total_redactions = 0

            # 2. מעבר על כל עמוד במסמך
            for page in doc:
                for text in pii_texts:
                    # חיפוש הטקסט בעמוד הנוכחי (מחזיר רשימה של מלבנים המקיפים את הטקסט)
                    text_instances = page.search_for(text)
                    
                    for inst in text_instances:
                        # הוספת "הערת השחרה" (מלבן אדום זמני שיהפוך לשחור מוחלט בהחלה)
                        # fill=(0, 0, 0) קובע צבע מילוי שחור
                        page.add_redact_annot(inst, fill=(0, 0, 0))
                        total_redactions += 1
                
                # החלת כל הערות ההשחרה בעמוד (מוחק פיזית את הטקסט שמתחת ומצייר את המלבן)
                page.apply_redactions()

            self.logger.info(f"✅ השחרת PDF הסתיימה. בוצעו {total_redactions} השחרות במסמך.")

            # 3. שמירה וסיום
            if output_path:
                doc.save(output_path)
                doc.close()
                return output_path
            else:
                redacted_bytes = doc.write()
                doc.close()
                return redacted_bytes

        except Exception as e:
            self.logger.error(f"❌ שגיאה בהשחרת ה-PDF: {e}")
            return None

    def redact_pdf_by_coords(self, pdf_data: Union[str, bytes], findings: List[dict], output_path: Optional[str] = None) -> Union[bytes, str, None]:
        """
        השחרת נתונים לפי קואורדינטות מדויקות (מלבנים בעמודים ספציפיים).
        זה מאפשר השחרה זהה לזו של PDFShield.
        """
        if not findings:
            self.logger.warning("⚠️ לא התקבלו מיקומים להשחרה, הפעולה מבוטלת.")
            return None

        try:
            if isinstance(pdf_data, str):
                doc = fitz.open(pdf_data)
            else:
                doc = fitz.open("pdf", pdf_data)
                
            self.logger.info(f"🔒 מתחיל השחרת קובץ PDF לפי {len(findings)} קואורדינטות מדויקות.")
            
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
                
            self.logger.info("✅ השחרת PDF ויזואלית הסתיימה בהצלחה.")

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
            self.logger.error(f"❌ שגיאה בהשחרת ה-PDF לפי קואורדינטות: {e}")
            return None

