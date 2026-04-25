import pytesseract
from PIL import Image
import io

class OCRProcessor:
    """
    Handles OCR using Tesseract for local image text extraction.
    Supports English and Hebrew.
    """
    
    def __init__(self):
        # Configure Tesseract path (specific to Windows, if needed)
        # Assuming pytesseract.pytesseract.tesseract_cmd is already set globally 
        # or it is in the PATH. If not, it should be configured here.
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.lang = 'eng+heb'

    def extract_from_path(self, file_path: str) -> str:
        """Extract text from an image file path."""
        try:
            image = Image.open(file_path)
            return self.extract_from_image_obj(image)
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def extract_from_bytes(self, image_bytes: bytes) -> str:
        """Extract text from image bytes."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return self.extract_from_image_obj(image)
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def extract_from_image_obj(self, image: Image.Image) -> str:
        """Extract text from a PIL Image object."""
        try:
            # Basic preprocessing could be added here (e.g., converting to grayscale)
            # image = image.convert('L')
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
