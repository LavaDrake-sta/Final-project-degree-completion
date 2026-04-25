import sys
import os
import fitz

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from redactors.pdf_redactor import PdfRedactor

def test_pdf_redactor():
    print("Testing PDF Redactor...")
    
    # 1. Create a dummy PDF file using fitz
    doc = fitz.open()
    page = doc.new_page()
    
    # Insert some text into the page
    # Insert English and Hebrew to test. (Note: PyMuPDF handles text search visually)
    page.insert_text(fitz.Point(50, 50), "Hello, my ID is 123456789 and my phone is 052-1234567.")
    page.insert_text(fitz.Point(50, 100), "This is highly confidential information.")
    
    dummy_path = "dummy_test.pdf"
    doc.save(dummy_path)
    doc.close()
    
    # 2. Initialize redactor
    redactor = PdfRedactor()
    
    # The PII strings we pretend the system detected
    pii_texts = ["123456789", "052-1234567", "confidential"]
    
    output_path = "dummy_test_redacted.pdf"
    
    # 3. Redact the PDF
    result = redactor.redact_pdf(dummy_path, pii_texts, output_path)
    
    if result:
        print(f"Redaction successful! Saved to {result}")
    else:
        print("Redaction failed!")
        
    # Clean up (optional)
    if os.path.exists(dummy_path):
        os.remove(dummy_path)

if __name__ == "__main__":
    test_pdf_redactor()
