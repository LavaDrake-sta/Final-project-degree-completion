import io
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from src.detectors.basic_detector import BasicPIIDetector, SensitivityLevel, PIIMatch
from src.pipeline.pii_detector import PIIDetector
from src.pipeline.ocr_processor import OCRProcessor
from src.pipeline.file_handler import FileHandler
from src.pipeline.decision_engine import DecisionEngine
from src.pipeline.main_pipeline import PIIPipeline

# ==========================================
# 🔍 BasicPIIDetector Tests
# ==========================================

def test_basic_pii_detector_regex():
    detector = BasicPIIDetector()
    
    # Test Israeli ID
    res = detector.analyze_text("הת.ז שלי היא 123456789")
    assert res['total_matches'] >= 1
    assert any(m.category == "israeli_id" for m in res['matches'])
    
    # Test Email
    res_email = detector.analyze_text("yossi@example.com")
    assert res_email['total_matches'] == 1
    assert res_email['matches'][0].category == "email"

def test_basic_pii_detector_context():
    detector = BasicPIIDetector()
    
    # Test context name: שם: משה כהן
    res = detector.analyze_text("שם פרטי: משה כהן")
    assert any("context_name" in m.category for m in res['matches'])
    assert any("משה" in m.text for m in res['matches'])

def test_basic_pii_detector_span_dedup():
    detector = BasicPIIDetector()
    
    # Create two overlapping matches: one email (priority 7) and one general keyword (priority 2)
    m1 = PIIMatch(text="test@example.com", category="email", start_pos=0, end_pos=16, confidence=0.9, sensitivity=SensitivityLevel.HIGH)
    m2 = PIIMatch(text="test", category="keyword_personal", start_pos=0, end_pos=4, confidence=0.6, sensitivity=SensitivityLevel.MEDIUM)
    
    deduped = detector._span_dedup([m1, m2])
    assert len(deduped) == 1
    assert deduped[0].category == "email"


# ==========================================
# 🤖 PIIDetector Tests
# ==========================================

def test_pii_detector_overlap_dedup():
    # Test overlap dedup in Presidio wrapper
    e1 = {"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 16, "score": 0.9, "text": "test@example.com", "source": "presidio"}
    e2 = {"entity_type": "HEB_NAME", "start": 0, "end": 4, "score": 0.95, "text": "test", "source": "context_keyword"}
    
    deduped = PIIDetector._overlap_dedup([e1, e2])
    # e2 has source "context_keyword" which gets higher priority
    assert len(deduped) == 1
    assert deduped[0]["source"] == "context_keyword"

def test_pii_detector_context_keywords():
    detector = PIIDetector()
    res = detector.detect_context_keywords("מספר אישי: 1234567")
    assert len(res) >= 1
    assert res[0]["entity_type"] == "IL_PERSONAL_NUMBER"
    assert res[0]["text"] == "1234567"

@patch('presidio_analyzer.AnalyzerEngine.analyze')
@patch('presidio_anonymizer.AnonymizerEngine.anonymize')
def test_pii_detector_analyze_anonymize(mock_anon, mock_analyze):
    # Mock Presidio results
    mock_analyze.return_value = []
    
    mock_anon_result = MagicMock()
    mock_anon_result.text = "אנונימי"
    mock_anon.return_value = mock_anon_result
    
    detector = PIIDetector()
    
    entities = detector.analyze("שלום עולם")
    assert isinstance(entities, list)
    
    anonymized = detector.anonymize("שלום עולם", [MagicMock()])
    assert anonymized == "אנונימי"


# ==========================================
# 📷 OCRProcessor Tests
# ==========================================

@patch('pytesseract.image_to_string')
def test_ocr_processor(mock_to_string):
    mock_to_string.return_value = "Extracted OCR text"
    
    proc = OCRProcessor()
    img = Image.new('RGB', (50, 50), color='white')
    
    res = proc.extract_from_image_obj(img)
    assert res == "Extracted OCR text"
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    res_bytes = proc.extract_from_bytes(buf.getvalue())
    assert res_bytes == "Extracted OCR text"


# ==========================================
# 📂 FileHandler Tests
# ==========================================

def test_file_handler_detection():
    handler = FileHandler()
    assert handler.detect_file_type(filename="test.pdf") == "pdf"
    assert handler.detect_file_type(filename="test.docx") == "docx"
    assert handler.detect_file_type(filename="test.xlsx") == "xlsx"
    assert handler.detect_file_type(filename="test.png") == "image"
    assert handler.detect_file_type(filename="test.unknown") == "unknown"

@patch('src.pipeline.file_handler.FileHandler._process_pdf')
@patch('src.pipeline.file_handler.FileHandler._process_docx')
def test_file_handler_processing(mock_docx, mock_pdf):
    handler = FileHandler()
    
    mock_pdf.return_value = {"success": True, "text": "pdf content", "file_type": "pdf"}
    mock_docx.return_value = {"success": True, "text": "docx content", "file_type": "docx"}
    
    res_pdf = handler.process_file(filename="test.pdf", file_bytes=b"dummy")
    assert res_pdf["success"] is True
    assert res_pdf["text"] == "pdf content"
    
    res_docx = handler.process_file(filename="test.docx", file_bytes=b"dummy")
    assert res_docx["success"] is True
    assert res_docx["text"] == "docx content"


# ==========================================
# 🔧 DecisionEngine Tests
# ==========================================

def test_decision_engine():
    engine = DecisionEngine()
    
    # 1. Translate
    assert engine.translate_entity("IL_ID") == "תעודת זהות ישראלית"
    assert engine.translate_entity("UNKNOWN") == "UNKNOWN"
    
    # 2. Evaluate SAFE
    res_safe = engine.evaluate([])
    assert res_safe["risk_level"] == DecisionEngine.RISK_SAFE
    assert res_safe["critical_count"] == 0
    
    # 3. Evaluate UNSAFE due to critical PII
    res_critical = engine.evaluate([{"entity_type": "IL_ID"}])
    assert res_critical["risk_level"] == DecisionEngine.RISK_UNSAFE
    assert res_critical["critical_count"] == 1
    
    # 4. Evaluate WARNING
    res_warning = engine.evaluate([{"entity_type": "EMAIL_ADDRESS"}, {"entity_type": "PHONE_NUMBER"}])
    assert res_warning["risk_level"] == DecisionEngine.RISK_WARNING
    
    # 5. Evaluate UNSAFE due to high volume
    res_volume = engine.evaluate([
        {"entity_type": "EMAIL_ADDRESS"},
        {"entity_type": "PHONE_NUMBER"},
        {"entity_type": "LOCATION"}
    ])
    assert res_volume["risk_level"] == DecisionEngine.RISK_UNSAFE


# ==========================================
# 🚀 PIIPipeline Tests
# ==========================================

@patch('src.pipeline.file_handler.FileHandler.process_file')
@patch('presidio_analyzer.AnalyzerEngine.analyze')
@patch('presidio_anonymizer.AnonymizerEngine.anonymize')
def test_pii_pipeline(mock_anon, mock_analyze, mock_proc_file):
    # Mock text extraction
    mock_proc_file.return_value = {
        "success": True,
        "text": "שם פרטי: אבי כהן, מספר אישי: 987654",
        "file_type": "docx"
    }
    
    # Mock Presidio results
    mock_analyze.return_value = []
    
    mock_anon_result = MagicMock()
    mock_anon_result.text = "שם פרטי: [REDACTED], מספר אישי: [REDACTED]"
    mock_anon.return_value = mock_anon_result
    
    pipeline = PIIPipeline()
    report = pipeline.process_file(file_path="dummy.docx")
    
    assert report["success"] is True
    assert report["file_type"] == "docx"
    assert len(report["entities"]) >= 1  # Context keyword should detect the IL_PERSONAL_NUMBER or HEB_NAME
    assert report["risk_evaluation"]["risk_level"] == "UNSAFE"
