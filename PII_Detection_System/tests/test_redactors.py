import io
import os
import sys
from unittest.mock import patch, MagicMock

# Mock easyocr and app before any imports to speed up tests and avoid real reader/Streamlit loads
sys.modules['easyocr'] = MagicMock()
sys.modules['app'] = MagicMock()

import pytest
from PIL import Image

from src.redactors.excel_redactor import ExcelRedactor
from src.redactors.word_redactor import WordRedactor
from src.redactors.pdf_redactor import PdfRedactor
from src.redactors.image_redactor import ImageRedactor

# ==========================================
# 📄 PdfRedactor Tests
# ==========================================

def test_pdf_redactor_text():
    import fitz
    redactor = PdfRedactor()
    
    # Create tiny PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Israel Israeli ID: 123456789")
    pdf_bytes = doc.write()
    doc.close()
    
    # Redact
    redacted_bytes, count = redactor.redact_pdf(pdf_bytes, ["123456789"])
    assert count > 0
    assert isinstance(redacted_bytes, bytes)
    
    # Verify redacted PDF can be opened
    doc2 = fitz.open(stream=redacted_bytes, filetype="pdf")
    assert doc2.page_count == 1
    doc2.close()

def test_pdf_redactor_by_coords():
    import fitz
    redactor = PdfRedactor()
    
    # Create tiny PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Israel Israeli ID: 123456789")
    pdf_bytes = doc.write()
    doc.close()
    
    findings = [
        {"page": 0, "rect": [90, 90, 200, 110]}
    ]
    
    redacted_bytes = redactor.redact_pdf_by_coords(pdf_bytes, findings)
    assert isinstance(redacted_bytes, bytes)


# ==========================================
# 📊 ExcelRedactor Tests
# ==========================================

def test_excel_redactor():
    import openpyxl
    redactor = ExcelRedactor()
    
    # Create Excel in memory
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"] = "ישראל ישראלי"
    ws["B1"] = "052-1234567"
    
    buf = io.BytesIO()
    wb.save(buf)
    excel_bytes = buf.getvalue()
    
    redacted_bytes, count = redactor.redact_excel(excel_bytes, ["052-1234567"])
    assert count == 1
    assert isinstance(redacted_bytes, bytes)
    
    # Verify values inside Excel cell are replaced with binary string (0 and 1)
    wb2 = openpyxl.load_workbook(io.BytesIO(redacted_bytes))
    ws2 = wb2.active
    val = ws2["B1"].value
    assert val != "052-1234567"
    assert all(c in "01" for c in val)
    # Check that style is black font and black background
    assert ws2["B1"].fill.start_color.rgb == "00000000" or ws2["B1"].fill.start_color.rgb == "000000"


# ==========================================
# 📝 WordRedactor Tests
# ==========================================

def test_word_redactor():
    import docx
    redactor = WordRedactor()
    
    # Create Word document in memory
    doc = docx.Document()
    doc.add_paragraph("שם פרטי: משה כהן")
    
    table = doc.add_table(rows=1, cols=1)
    table.cell(0, 0).paragraphs[0].text = "סודי ביותר"
    
    buf = io.BytesIO()
    doc.save(buf)
    word_bytes = buf.getvalue()
    
    redacted_bytes, count = redactor.redact_word(word_bytes, ["משה כהן", "סודי ביותר"])
    assert count >= 2
    assert isinstance(redacted_bytes, bytes)
    
    # Verify values in Docx
    doc2 = docx.Document(io.BytesIO(redacted_bytes))
    text = "\n".join([p.text for p in doc2.paragraphs])
    assert "משה כהן" not in text


# ==========================================
# 🖼️ ImageRedactor Tests
# ==========================================

@patch('easyocr.Reader')
@patch('pytesseract.image_to_data')
def test_image_redactor(mock_tess, mock_easyocr):
    redactor = ImageRedactor()
    
    # Mock EasyOCR to return no results so it falls back to Tesseract
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = []
    mock_easyocr.return_value = mock_reader
    
    # Mock Tesseract image_to_data to return a bounding box for our search word "secret"
    mock_tess.return_value = {
        'text': ['hello', 'secret', 'world'],
        'conf': ['90', '95', '90'],
        'left': [10, 30, 80],
        'top': [10, 15, 10],
        'width': [15, 40, 20],
        'height': [10, 12, 10]
    }
    
    # Create simple PIL image
    img = Image.new('RGB', (150, 50), color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    
    redacted_bytes, count = redactor.redact_image(img_bytes, ["secret"])
    assert count == 1
    assert isinstance(redacted_bytes, bytes)
    
    # Check that image draws
    img2 = Image.open(io.BytesIO(redacted_bytes))
    assert img2.size == (150, 50)
