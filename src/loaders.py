"""
File Loaders Module
Loads text from PDF, Word documents, and images (with OCR support)
"""

import os
from pathlib import Path
from typing import Optional, Tuple
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract

class FileLoader:
    """Main class for loading different file types"""

    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize FileLoader

        Args:
            tesseract_path: Path to Tesseract executable (Windows only)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def load_file(self, file_path: str) -> Tuple[str, str]:
        """
        Load file and extract text based on file type

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (text, file_type)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        if extension == '.pdf':
            return self._load_pdf(file_path), 'PDF'
        elif extension == '.docx':
            return self._load_docx(file_path), 'DOCX'
        elif extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return self._load_image(file_path), 'IMAGE'
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    def _load_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        # If no text found, try OCR on page image
                        try:
                            img = page.to_image(resolution=300)
                            page_text = pytesseract.image_to_string(
                                img.original,
                                lang='heb+eng'
                            )
                            text += page_text + "\n"
                        except Exception as e:
                            print(f"Warning: Could not extract text from page: {e}")
        except Exception as e:
            raise Exception(f"Error loading PDF: {e}")

        return text.strip()

    def _load_docx(self, file_path: Path) -> str:
        """Extract text from Word document"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error loading DOCX: {e}")

    def _load_image(self, file_path: Path) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            # Use Hebrew and English for OCR
            text = pytesseract.image_to_string(image, lang='heb+eng')
            return text.strip()
        except Exception as e:
            raise Exception(f"Error loading image: {e}")


def load_all_files(input_dir: str, loader: Optional[FileLoader] = None) -> dict:
    """
    Load all supported files from a directory

    Args:
        input_dir: Directory containing files to load
        loader: FileLoader instance (creates new one if None)

    Returns:
        Dictionary mapping filename to (text, file_type)
    """
    if loader is None:
        loader = FileLoader()

    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")

    results = {}
    supported_extensions = {'.pdf', '.docx', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            try:
                text, file_type = loader.load_file(str(file_path))
                results[file_path.name] = {
                    'text': text,
                    'file_type': file_type,
                    'path': str(file_path)
                }
                print(f"✓ Loaded: {file_path.name} ({file_type})")
            except Exception as e:
                print(f"✗ Failed to load {file_path.name}: {e}")
                results[file_path.name] = {
                    'text': "",
                    'file_type': "ERROR",
                    'error': str(e)
                }

    return results
