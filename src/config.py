"""
Configuration Module
Central configuration for the PII Detection System
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
MODELS_DIR = PROJECT_ROOT / "models"

# Detection settings
USE_AI = True  # Set to False to use only regex detection
MIN_CONFIDENCE = 0.5  # Minimum confidence threshold for AI detection

# Anonymization settings
ANONYMIZATION_MODE = "replace"  # Options: redact, mask, replace, hash

# Supported file types
SUPPORTED_EXTENSIONS = {
    'documents': ['.pdf', '.docx'],
    'images': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
}

# AI Model settings
NER_MODEL = "Davlan/bert-base-multilingual-cased-ner-hrl"
SPACY_MODEL = "xx_ent_wiki_sm"

# OCR settings (for Tesseract)
OCR_LANGUAGES = "heb+eng"  # Hebrew and English
TESSERACT_PATH = None  # Auto-detect, or set path on Windows

# Report settings
REPORT_FORMATS = ['excel', 'csv', 'text']  # Which formats to generate
MAX_EXAMPLES_IN_REPORT = 3  # Max examples to show per entity type

# Processing settings
BATCH_SIZE = 10  # Number of files to process in batch
VERBOSE = True  # Print detailed progress

# Entity types to detect
ENTITY_TYPES = [
    'PERSON',
    'ID_NUMBER',
    'PHONE',
    'EMAIL',
    'ADDRESS',
    'CREDIT_CARD',
    'BANK_ACCOUNT',
    'ORGANIZATION',
    'LOCATION'
]

# Hebrew labels for entity types
ENTITY_LABELS_HE = {
    'PERSON': 'שם אדם',
    'ID_NUMBER': 'תעודת זהות',
    'PHONE': 'טלפון',
    'EMAIL': 'דוא"ל',
    'ADDRESS': 'כתובת',
    'CREDIT_CARD': 'כרטיס אשראי',
    'BANK_ACCOUNT': 'חשבון בנק',
    'ORGANIZATION': 'ארגון',
    'LOCATION': 'מיקום'
}


def ensure_directories():
    """Create necessary directories if they don't exist"""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "anonymized").mkdir(exist_ok=True)


# Auto-create directories on import
ensure_directories()
