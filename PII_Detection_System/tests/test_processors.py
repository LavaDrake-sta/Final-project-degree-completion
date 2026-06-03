import io
import os
import sys
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

# Add PROJECT_ROOT to sys.path is handled by conftest.py, but just in case:
from src.processors.image_processor import ImageProcessor, is_image_file, supported_image_formats
from src.processors.pdf_processor import PDFProcessor, is_pdf_file, estimate_pdf_type
from src.processors.word_processor import WordProcessor, is_word_file

# ==========================================
# 🖼️ ImageProcessor Tests
# ==========================================

def test_image_helpers():
    assert is_image_file("test.png") is True
    assert is_image_file("test.PNG") is True
    assert is_image_file("test.pdf") is False
    assert is_image_file("") is False
    assert ".png" in supported_image_formats()

def test_image_processor_clean_text():
    proc = ImageProcessor()
    assert proc.clean_extracted_text("   hello   \n\n   world   ") == "hello world"
    assert proc.clean_extracted_text("") == ""
    assert proc.clean_extracted_text(None) == ""

def test_image_processor_preprocess():
    proc = ImageProcessor()
    # Create a small dummy grayscale image
    dummy_img = np.zeros((100, 100), dtype=np.uint8)
    processed = proc.preprocess_image(dummy_img)
    # Check that it returns a numpy array of same or scaled dimensions
    assert isinstance(processed, np.ndarray)

@patch('pytesseract.image_to_string')
@patch('pytesseract.image_to_data')
def test_image_processor_extract_text_bytes(mock_to_data, mock_to_string):
    mock_to_string.return_value = "שלום עולם"
    mock_to_data.return_value = {'conf': ['90', '95']}
    
    proc = ImageProcessor()
    
    # Create tiny in-memory image
    img = Image.new('RGB', (100, 100), color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    
    res = proc.extract_text_from_image(img_bytes, filename="test.png")
    assert res['success'] is True
    assert "שלום עולם" in res['text']
    assert res['confidence'] > 0
    assert res['filename'] == "test.png"


# ==========================================
# 📄 PDFProcessor Tests
# ==========================================

def test_pdf_helpers():
    assert is_pdf_file("test.pdf") is True
    assert is_pdf_file("test.PDF") is True
    assert is_pdf_file("test.docx") is False
    
    assert estimate_pdf_type(50, 1) == "scanned"
    assert estimate_pdf_type(600, 1) == "text"
    assert estimate_pdf_type(300, 1) == "mixed"
    assert estimate_pdf_type(10, 0) == "unknown"

def test_pdf_processor_get_info():
    import fitz
    proc = PDFProcessor()
    
    # Create tiny PDF using fitz in memory
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test PDF info")
    pdf_bytes = doc.write()
    doc.close()
    
    info = proc.get_pdf_info(pdf_bytes)
    assert info['pages'] == 1
    assert info['encrypted'] == False

def test_pdf_processor_extract_text_native():
    import fitz
    proc = PDFProcessor()
    
    # Create tiny PDF using fitz in memory
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello world from PDF")
    pdf_bytes = doc.write()
    doc.close()
    
    res = proc.extract_text_from_pdf(pdf_bytes, filename="test.pdf")
    assert res['success'] is True
    assert "Hello world from PDF" in res['text']
    assert res['pages'] == 1
    assert res['pdf_type'] in ["native", "mixed", "word_native", "scanned", "unknown"]


# ==========================================
# 📝 WordProcessor Tests
# ==========================================

def test_word_helpers():
    assert is_word_file("doc.docx") is True
    assert is_word_file("doc.doc") is True
    assert is_word_file("doc.pdf") is False

def test_word_processor_extract():
    import docx
    proc = WordProcessor()
    
    # Create a tiny docx in memory
    doc = docx.Document()
    doc.add_paragraph("שמי ישראל ישראלי ות.ז שלי היא 123456789")
    doc.add_paragraph("Another paragraph")
    
    # Add a table
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "מכבי"
    table.cell(0, 1).text = "כללית"
    
    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()
    
    # Extract
    res = proc.extract_text_from_word(docx_bytes, filename="test.docx")
    assert res['success'] is True
    assert "ישראל ישראלי" in res['text']
    assert "מכבי | כללית" in res['text'] or "מכבי" in res['text']
    assert res['paragraphs'] == 2
    assert res['tables'] == 1
    
    # Info
    info = proc.get_word_info(docx_bytes)
    assert info['paragraphs'] == 2
    assert info['tables'] == 1
