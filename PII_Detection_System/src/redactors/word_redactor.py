"""
Word Redactor - השחרת קבצי Word
פרויקט גמר - זיהוי מידע אישי רגיש

מודול להשחרה אקטיבית של PII מקבצי Word
"""

import docx
from docx.enum.text import WD_COLOR_INDEX
from docx.shared import RGBColor
import io

try:
    from src.logger_config import get_logger, trace_execution
except ImportError:
    try:
        from logger_config import get_logger, trace_execution
    except ImportError:
        def trace_execution(func): return func
import logging
import random
from typing import List, Union, Optional

class WordRedactor:
    """
    מחלקה האחראית על השחרת מידע רגיש מקבצי Word.
    המחלקה מקבלת File ורשימת טקסטים להסרה, משנה את הטקסט באופן בלתי הפיך ל-0 ול-1
    ומייצרת File Word חדש ובטוח.
    """

    def __init__(self):
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @trace_execution
    def _mask_text_binary(self, original_text: str) -> str:
        """מחליף כל תו בטקסט הרגיש ב-0 או 1 אקראיים כדי למנוע שחזור"""
        return "".join(random.choice(['0', '1']) for _ in original_text)

    @trace_execution
    def _redact_paragraph(self, para, pii_texts: List[str]) -> int:
        redact_count = 0
        
        # שלב 1: ניסיון השחרה ברמת ה-Run (שומר על עיצוב מקורי)
        for run in para.runs:
            if not run.text: 
                continue
            modified = False
            new_text = run.text
            for pii in pii_texts:
                if pii and pii in new_text:
                    masked = self._mask_text_binary(pii)
                    new_text = new_text.replace(pii, masked)
                    modified = True
                    redact_count += 1
            if modified:
                run.text = new_text
                # צביעת הרקע בשחור והטקסט בשחור (כדי ליצור מלבן שחור אטום ללא טקסט קריא)
                run.font.highlight_color = WD_COLOR_INDEX.BLACK
                run.font.color.rgb = RGBColor(0, 0, 0)
                
        # שלב 2: בדיקה אם נשאר מידע רגיש שפוצל בין כמה Runs
        remaining_pii = False
        para_text = para.text
        for pii in pii_texts:
            if pii and pii in para_text:
                remaining_pii = True
                break
                
        if remaining_pii:
            # Fallback: דריסת הפסקה כולה כדי להבטיח מחיקה (על חשבון עיצוב)
            new_text = para.text
            for pii in pii_texts:
                if pii and pii in new_text:
                    masked = self._mask_text_binary(pii)
                    new_text = new_text.replace(pii, masked)
                    redact_count += 1
            para.clear()
            run = para.add_run(new_text)
            
        return redact_count

    @trace_execution
    def redact_word(self, word_data: Union[str, bytes], pii_texts: List[str], output_path: Optional[str] = None) -> Union[bytes, str, bool]:
        """
        השחרת נתונים רגישים מתוך File Word.
        - word_data: נתיב לFile מקור או נתוני bytes
        - pii_texts: רשימה של מחרוזות (הטקסט של המידע הרגיש) שיש להשחיר
        - output_path: נתיב לשמירת הFile. אם None, יוחזרו bytes.
        """
        try:
            if isinstance(word_data, str):
                doc = docx.Document(word_data)
            else:
                doc = docx.Document(io.BytesIO(word_data))
                
            self.logger.info(f"🔒 Starting redaction of Word file. Number of PII strings to redact: {len(pii_texts)}")
            total_redact_count = 0

            # 1. מעבר על paragraphs רגילות
            for para in doc.paragraphs:
                total_redact_count += self._redact_paragraph(para, pii_texts)

            # 2. מעבר על paragraphs בתוך טבלאות
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            total_redact_count += self._redact_paragraph(para, pii_texts)

            self.logger.info(f"✅ Finished redaction. {total_redact_count} pieces of information converted to binary string (0 and 1).")

            # שמירת התוצאה - החזרת הFile למשתמש להורדה
            if output_path is not None:
                doc.save(output_path)
                return output_path, total_redact_count
            else:
                output = io.BytesIO()
                doc.save(output)
                return output.getvalue(), total_redact_count
                
        except Exception as e:
            self.logger.error(f"❌ Error redacting Word: {e}")
            return False