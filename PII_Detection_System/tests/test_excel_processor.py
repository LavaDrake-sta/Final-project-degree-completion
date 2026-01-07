import io
import pandas as pd
import pytest

from src.processors.Excel_Processor import ExcelProcessor


def make_test_excel_bytes() -> bytes:
    """
    יוצר קובץ Excel (xlsx) בזיכרון עם 2 גיליונות וערכים 'אמיתיים' לבדיקה.
    """
    buf = io.BytesIO()

    df1 = pd.DataFrame({
        "name": ["Alice", "Bob"],
        "email": ["alice@example.com", "bob@example.com"],
        "phone": ["050-1234567", "052-7654321"],
        "id": ["123456789", "987654321"],
    })

    df2 = pd.DataFrame({
        "city": ["Tel Aviv", "Haifa"],
        "salary": [12000, 9800],
        "notes": ["test row", "another test"],
    })

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Employees", index=False)
        df2.to_excel(writer, sheet_name="Meta", index=False)

    return buf.getvalue()


def test_analyze_excel_structure_bytes():
    processor = ExcelProcessor()
    excel_bytes = make_test_excel_bytes()

    result = processor.analyze_excel_structure(excel_bytes)

    # בדיקות בסיסיות
    assert isinstance(result, dict)
    assert "sheets" in result or len(result) > 0  # תלוי איך בנית את ה-dict בפונקציה שלך

    # אם אצלך המפתחות הם שמות גיליונות:
    assert "Employees" in result
    assert "Meta" in result


def test_get_excel_info_bytes():
    processor = ExcelProcessor()
    excel_bytes = make_test_excel_bytes()

    info = processor.get_excel_info(excel_bytes)

    assert isinstance(info, dict)
    # בדיקות שמצופות בקונבנציה שלך — תתאים לפי הפלט אצלך:
    # למשל: מספר גיליונות, שמות גיליונות, גודל, וכו'
    # לדוגמה:
    if "sheet_names" in info:
        assert "Employees" in info["sheet_names"]
        assert "Meta" in info["sheet_names"]


from src.processors.Excel_Processor import ExcelProcessor

def test_excel_corrupted_bytes_returns_empty_or_safe():
    p = ExcelProcessor()
    bad = b"not an excel file"

    info = p.get_excel_info(bad)
    assert isinstance(info, dict)  # שלא יקרוס


import io
import pandas as pd
from src.processors.Excel_Processor import ExcelProcessor

def test_excel_empty_sheet():
    buf = io.BytesIO()
    df = pd.DataFrame()

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Empty", index=False)

    p = ExcelProcessor()
    result = p.analyze_excel_structure(buf.getvalue())

    assert isinstance(result, dict)
    assert "Empty" in result