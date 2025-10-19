"""
Processors Module - מודול מעבדי קבצים
פרויקט גמר - זיהוי מידע אישי רגיש

מודול זה מכיל מעבדים לסוגי קבצים שונים:
- image_processor: עיבוד תמונות עם OCR
- pdf_processor: עיבוד קבצי PDF
- document_processor: עיבוד מסמכי Office (עתידי)
"""

# ייבוא המעבדים הזמינים
try:
    from .image_processor import ImageProcessor, is_image_file, supported_image_formats

    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSOR_AVAILABLE = False

try:
    from .pdf_processor import PDFProcessor, is_pdf_file, estimate_pdf_type

    PDF_PROCESSOR_AVAILABLE = True
except ImportError:
    PDF_PROCESSOR_AVAILABLE = False

__all__ = [
    'ImageProcessor',
    'PDFProcessor',
    'is_image_file',
    'is_pdf_file',
    'supported_image_formats',
    'estimate_pdf_type',
    'IMAGE_PROCESSOR_AVAILABLE',
    'PDF_PROCESSOR_AVAILABLE'
]


def get_available_processors():
    """החזרת רשימת מעבדים זמינים"""
    processors = []

    if IMAGE_PROCESSOR_AVAILABLE:
        processors.append('image')

    if PDF_PROCESSOR_AVAILABLE:
        processors.append('pdf')

    return processors


def check_processor_requirements():
    """בדיקת דרישות המעבדים"""
    requirements = {
        'image': {
            'available': IMAGE_PROCESSOR_AVAILABLE,
            'requirements': ['opencv-python', 'pytesseract', 'pillow']
        },
        'pdf': {
            'available': PDF_PROCESSOR_AVAILABLE,
            'requirements': ['pymupdf', 'PyPDF2']
        }
    }

    return requirements