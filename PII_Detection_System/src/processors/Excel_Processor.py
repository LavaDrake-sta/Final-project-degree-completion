"""
Excel Processor - עיבוד קבצי Excel
פרויקט גמר - זיהוי מידע אישי רגיש

מודול לחילוץ וניתוח טקסט מקבצי Excel
"""

import pandas as pd
import openpyxl
import io
import logging
from typing import Dict, List, Union, Optional
import os

try:
    from src.logger_config import get_logger, trace_execution
except ImportError:
    try:
        from logger_config import get_logger, trace_execution
    except ImportError:
        def trace_execution(func): return func

class ExcelProcessor:
    """
    מעבד Excel עם תמיכה בכל סוגי הגיליונות
    """

    def __init__(self):
        """אתחול המעבד"""
        self.setup_logging()

    def setup_logging(self):
        """הגדרת לוגים"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @trace_execution
    def extract_text_from_excel(self, excel_data: Union[str, bytes],
                                filename: str = "") -> Dict:
        """
        חילוץ טקסט מFile Excel
        """
        try:
            # קריאת הFile
            if isinstance(excel_data, str):
                # נתיב לFile
                df_dict = pd.read_excel(excel_data, sheet_name=None)
            elif isinstance(excel_data, bytes):
                # נתוני bytes
                df_dict = pd.read_excel(io.BytesIO(excel_data), sheet_name=None)
            else:
                raise ValueError("סוג נתוני Excel לא נתמך")

            self.logger.info(f"📊 Processing Excel: {len(df_dict)} sheets")

            # חילוץ טקסט מכל הגיליונות
            all_text = []
            sheet_data = {}

            for sheet_name, df in df_dict.items():
                # חילוץ כל הערכים מהגיליון
                sheet_text = self._extract_sheet_text(df, sheet_name)
                all_text.append(f"\n=== גיליון: {sheet_name} ===\n{sheet_text}")

                sheet_data[sheet_name] = {
                    'text': sheet_text,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'cells_with_data': df.count().sum()
                }

            # איחוד כל הטקסט
            full_text = "\n".join(all_text)

            result = {
                'success': True,
                'text': full_text,
                'sheets': list(df_dict.keys()),
                'sheet_count': len(df_dict),
                'sheet_data': sheet_data,
                'filename': filename,
                'character_count': len(full_text),
                'word_count': len(full_text.split()) if full_text else 0
            }

            self.logger.info(f"✅ Excel: {len(full_text)} characters from {len(df_dict)} sheets")
            return result

        except Exception as e:
            self.logger.error(f"❌ Error processing Excel: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': "",
                'sheets': [],
                'sheet_count': 0,
                'filename': filename
            }

    @trace_execution
    def _extract_sheet_text(self, df: pd.DataFrame, sheet_name: str) -> str:
        """
        חילוץ טקסט מגיליון בודד
        """
        try:
            text_parts = []

            # הוספת שמות העמודות
            text_parts.append("כותרות: " + " | ".join(str(col) for col in df.columns))

            # חילוץ כל השורות
            for index, row in df.iterrows():
                row_text = []
                for col_name, value in row.items():
                    # דלג על ערכים ריקים
                    if pd.notna(value) and str(value).strip():
                        row_text.append(f"{col_name}: {value}")

                if row_text:
                    text_parts.append(" | ".join(row_text))

            return "\n".join(text_parts)

        except Exception as e:
            self.logger.error(f"❌ Error extracting sheet {sheet_name}: {e}")
            return ""

    @trace_execution
    def get_excel_info(self, excel_data: Union[str, bytes]) -> Dict:
        """
        קבלת מידע על File Excel
        """
        try:
            if isinstance(excel_data, str):
                df_dict = pd.read_excel(excel_data, sheet_name=None)
                file_size = os.path.getsize(excel_data)
            else:
                df_dict = pd.read_excel(io.BytesIO(excel_data), sheet_name=None)
                file_size = len(excel_data)

            info = {
                'sheets': list(df_dict.keys()),
                'sheet_count': len(df_dict),
                'file_size': file_size,
                'total_rows': sum(len(df) for df in df_dict.values()),
                'total_columns': sum(len(df.columns) for df in df_dict.values()),
            }

            return info

        except Exception as e:
            self.logger.error(f"❌ Error getting Excel info: {e}")
            return {}

    @trace_execution
    def analyze_excel_structure(self, excel_data: Union[str, bytes]) -> Dict:
        """
        ניתוח מבנה File Excel
        """
        try:
            if isinstance(excel_data, str):
                df_dict = pd.read_excel(excel_data, sheet_name=None)
            else:
                df_dict = pd.read_excel(io.BytesIO(excel_data), sheet_name=None)

            structure = {}

            for sheet_name, df in df_dict.items():
                # זיהוי סוגי עמודות
                column_types = {}
                for col in df.columns:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        # ניסיון לזהות סוג הנתונים
                        if col_data.dtype == 'int64':
                            column_types[col] = 'מספר שלם'
                        elif col_data.dtype == 'float64':
                            column_types[col] = 'מספר עשרוני'
                        elif col_data.dtype == 'datetime64[ns]':
                            column_types[col] = 'תאריך'
                        else:
                            # בדיקה אם יש דפוס מסוים
                            sample = str(col_data.iloc[0])
                            if '@' in sample:
                                column_types[col] = 'אימייל (חשוד)'
                            elif any(char.isdigit() for char in sample):
                                column_types[col] = 'טקסט עם מספרים'
                            else:
                                column_types[col] = 'טקסט'

                structure[sheet_name] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': list(df.columns),
                    'column_types': column_types,
                    'has_empty_cells': df.isnull().sum().sum() > 0,
                    'empty_cells_count': int(df.isnull().sum().sum())
                }

            return structure

        except Exception as e:
            self.logger.error(f"❌ Error analyzing structure: {e}")
            return {}


# פונקציות עזר
def is_excel_file(filename: str) -> bool:
    """בדיקה אם הFile הוא Excel"""
    if not filename:
        return False
    return filename.lower().endswith(('.xlsx', '.xls', '.xlsm'))


def supported_excel_formats():
    """רשימת פורמטי Excel נתמכים"""
    return ['.xlsx', '.xls', '.xlsm']


# בדיקה מהירה
if __name__ == "__main__":
    print("📊 בדיקת מעבד Excel")
    print("=" * 30)

    processor = ExcelProcessor()
    print("✅ מעבד Excel מוכן לשימוש!")

    # אם יש File לדוגמה
    test_file = "test_data.xlsx"
    if os.path.exists(test_file):
        print(f"\n📊 בודק File: {test_file}")
        result = processor.extract_text_from_excel(test_file)

        if result['success']:
            print(f"✅ הצלחה!")
            print(f"📄 sheets: {', '.join(result['sheets'])}")
            print(f"📝 characters: {result['character_count']:,}")
        else:
            print(f"❌ שגיאה: {result['error']}")