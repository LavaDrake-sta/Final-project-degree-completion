"""
AI-Based PII Detector Module
Uses Transformers NER models + Regex patterns for accurate PII detection
Supports both Hebrew and English
"""

import re
import warnings
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

warnings.filterwarnings('ignore')


@dataclass
class PIIEntity:
    """Represents a detected PII entity"""
    text: str
    type: str
    start: int
    end: int
    confidence: float


class PIIDetector:
    """AI-powered PII detection with multi-language support"""

    def __init__(self, use_ai: bool = True):
        """
        Initialize PII Detector

        Args:
            use_ai: Whether to use AI models (disable for faster but less accurate detection)
        """
        self.use_ai = use_ai
        self.ner_model = None
        self.nlp = None

        if self.use_ai:
            self._load_models()

        # Compile regex patterns
        self._compile_patterns()

    def _load_models(self):
        """Load AI models for NER"""
        try:
            print("🔄 Loading AI models (this may take a moment on first run)...")

            # Load multilingual NER model
            model_name = "Davlan/bert-base-multilingual-cased-ner-hrl"
            self.ner_model = pipeline(
                "ner",
                model=model_name,
                aggregation_strategy="simple"
            )

            # Try to load spaCy model
            try:
                self.nlp = spacy.load("xx_ent_wiki_sm")
            except:
                print("⚠️  SpaCy model not found. Install with: python -m spacy download xx_ent_wiki_sm")
                self.nlp = None

            print("✓ AI models loaded successfully")

        except Exception as e:
            print(f"⚠️  Warning: Could not load AI models: {e}")
            print("   Falling back to regex-only detection")
            self.use_ai = False

    def _compile_patterns(self):
        """Compile regex patterns for PII detection"""

        # Israeli ID number (9 digits with validation)
        self.id_pattern = re.compile(r'\b\d{9}\b')

        # Phone numbers (Israeli format)
        self.phone_pattern = re.compile(
            r'''
            (?:
                (?:\+972|972|0)           # Country code or 0
                [-\s]?                     # Optional separator
                (?:5[0-9]|[2-4]|[8-9])    # Mobile or landline prefix
                [-\s]?
                \d{3}
                [-\s]?
                \d{4}
            )
            ''',
            re.VERBOSE
        )

        # Email addresses
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )

        # Credit card numbers
        self.credit_card_pattern = re.compile(
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        )

        # Addresses - Hebrew and English
        self.address_keywords = {
            'hebrew': ['רחוב', 'רח\'', 'שד\'', 'שדרות', 'כביש', 'דרך', 'מעלה', 'סמטת'],
            'english': ['street', 'st.', 'avenue', 'ave.', 'road', 'rd.', 'boulevard', 'blvd.']
        }

        # Common Hebrew names patterns
        self.hebrew_name_indicators = ['שם:', 'שם מלא:', 'שם פרטי:', 'שם משפחה:']

        # Bank account (Israeli format)
        self.bank_account_pattern = re.compile(
            r'\b\d{2,3}[-/]\d{3,6}[-/]\d{1,2}\b'
        )

    def detect_pii(self, text: str) -> Dict[str, List[PIIEntity]]:
        """
        Detect all PII entities in text

        Args:
            text: Input text to analyze

        Returns:
            Dictionary mapping PII type to list of entities
        """
        entities = {
            'PERSON': [],
            'ID_NUMBER': [],
            'PHONE': [],
            'EMAIL': [],
            'ADDRESS': [],
            'CREDIT_CARD': [],
            'BANK_ACCOUNT': [],
            'ORGANIZATION': [],
            'LOCATION': []
        }

        # AI-based detection
        if self.use_ai and self.ner_model:
            ai_entities = self._detect_with_ai(text)
            for entity in ai_entities:
                if entity.type in entities:
                    entities[entity.type].append(entity)

        # Regex-based detection
        regex_entities = self._detect_with_regex(text)
        for entity in regex_entities:
            # Avoid duplicates
            if not self._is_duplicate(entity, entities[entity.type]):
                entities[entity.type].append(entity)

        # Post-process and validate
        entities = self._validate_entities(entities, text)

        return entities

    def _detect_with_ai(self, text: str) -> List[PIIEntity]:
        """Use AI models to detect named entities"""
        entities = []

        try:
            # Use transformers NER
            ner_results = self.ner_model(text)

            for item in ner_results:
                entity_type = self._map_entity_type(item['entity_group'])
                if entity_type:
                    entities.append(PIIEntity(
                        text=item['word'].strip(),
                        type=entity_type,
                        start=item['start'],
                        end=item['end'],
                        confidence=item['score']
                    ))

            # Use spaCy if available
            if self.nlp:
                doc = self.nlp(text)
                for ent in doc.ents:
                    entity_type = self._map_spacy_entity(ent.label_)
                    if entity_type:
                        entities.append(PIIEntity(
                            text=ent.text,
                            type=entity_type,
                            start=ent.start_char,
                            end=ent.end_char,
                            confidence=0.8
                        ))

        except Exception as e:
            print(f"⚠️  AI detection warning: {e}")

        return entities

    def _detect_with_regex(self, text: str) -> List[PIIEntity]:
        """Use regex patterns to detect PII"""
        entities = []

        # ID Numbers
        for match in self.id_pattern.finditer(text):
            if self._validate_israeli_id(match.group()):
                entities.append(PIIEntity(
                    text=match.group(),
                    type='ID_NUMBER',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95
                ))

        # Phone numbers
        for match in self.phone_pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(),
                type='PHONE',
                start=match.start(),
                end=match.end(),
                confidence=0.9
            ))

        # Emails
        for match in self.email_pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(),
                type='EMAIL',
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))

        # Credit cards
        for match in self.credit_card_pattern.finditer(text):
            if self._validate_credit_card(match.group()):
                entities.append(PIIEntity(
                    text=match.group(),
                    type='CREDIT_CARD',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85
                ))

        # Bank accounts
        for match in self.bank_account_pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(),
                type='BANK_ACCOUNT',
                start=match.start(),
                end=match.end(),
                confidence=0.8
            ))

        # Addresses
        address_entities = self._detect_addresses(text)
        entities.extend(address_entities)

        return entities

    def _detect_addresses(self, text: str) -> List[PIIEntity]:
        """Detect addresses based on keywords"""
        entities = []
        lines = text.split('\n')

        for line_idx, line in enumerate(lines):
            # Check for Hebrew address keywords
            for keyword in self.address_keywords['hebrew']:
                if keyword in line:
                    # Extract the full address line
                    entities.append(PIIEntity(
                        text=line.strip(),
                        type='ADDRESS',
                        start=text.find(line),
                        end=text.find(line) + len(line),
                        confidence=0.7
                    ))
                    break

            # Check for English address keywords
            line_lower = line.lower()
            for keyword in self.address_keywords['english']:
                if keyword in line_lower:
                    entities.append(PIIEntity(
                        text=line.strip(),
                        type='ADDRESS',
                        start=text.find(line),
                        end=text.find(line) + len(line),
                        confidence=0.7
                    ))
                    break

        return entities

    def _validate_israeli_id(self, id_num: str) -> bool:
        """Validate Israeli ID using Luhn algorithm"""
        if len(id_num) != 9 or not id_num.isdigit():
            return False

        # Luhn check
        total = 0
        for i, digit in enumerate(id_num):
            num = int(digit)
            if i % 2 == 0:
                num *= 1
            else:
                num *= 2
                if num > 9:
                    num = num // 10 + num % 10
            total += num

        return total % 10 == 0

    def _validate_credit_card(self, card_num: str) -> bool:
        """Basic credit card validation"""
        # Remove spaces and dashes
        card_num = re.sub(r'[-\s]', '', card_num)

        if len(card_num) < 13 or len(card_num) > 19:
            return False

        # Simple Luhn check
        def luhn_check(num_str):
            digits = [int(d) for d in num_str]
            checksum = 0
            for i, digit in enumerate(reversed(digits)):
                if i % 2 == 1:
                    digit *= 2
                    if digit > 9:
                        digit -= 9
                checksum += digit
            return checksum % 10 == 0

        return luhn_check(card_num)

    def _map_entity_type(self, entity_label: str) -> str:
        """Map NER model entity labels to our PII types"""
        mapping = {
            'PER': 'PERSON',
            'PERSON': 'PERSON',
            'ORG': 'ORGANIZATION',
            'ORGANIZATION': 'ORGANIZATION',
            'LOC': 'LOCATION',
            'LOCATION': 'LOCATION',
            'GPE': 'LOCATION'
        }
        return mapping.get(entity_label.upper(), None)

    def _map_spacy_entity(self, entity_label: str) -> str:
        """Map spaCy entity labels to our PII types"""
        mapping = {
            'PERSON': 'PERSON',
            'PER': 'PERSON',
            'ORG': 'ORGANIZATION',
            'GPE': 'LOCATION',
            'LOC': 'LOCATION',
            'FAC': 'LOCATION'
        }
        return mapping.get(entity_label.upper(), None)

    def _is_duplicate(self, new_entity: PIIEntity, existing: List[PIIEntity]) -> bool:
        """Check if entity overlaps with existing entities"""
        for entity in existing:
            # Check for overlap
            if (new_entity.start <= entity.end and new_entity.end >= entity.start):
                return True
        return False

    def _validate_entities(self, entities: Dict[str, List[PIIEntity]], text: str) -> Dict[str, List[PIIEntity]]:
        """Post-process and validate detected entities"""
        # Remove duplicates and low-confidence entities
        for entity_type in entities:
            # Sort by confidence
            entities[entity_type].sort(key=lambda x: x.confidence, reverse=True)

            # Remove overlapping entities (keep higher confidence)
            filtered = []
            for entity in entities[entity_type]:
                if entity.confidence >= 0.5:  # Confidence threshold
                    if not self._is_duplicate(entity, filtered):
                        filtered.append(entity)

            entities[entity_type] = filtered

        return entities

    def get_summary(self, entities: Dict[str, List[PIIEntity]]) -> Dict[str, int]:
        """Get count summary of detected entities"""
        return {
            entity_type: len(entity_list)
            for entity_type, entity_list in entities.items()
        }
