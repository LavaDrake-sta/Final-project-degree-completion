"""
AI-Based PII Detector Module - Israeli Privacy Law Amendment 13 Compliant
Detects Personal Information according to Israeli Privacy Protection Law (Amendment No. 13), 2024

This module identifies both:
1. Standard personal information
2. Specially sensitive information (מידע בעל רגישות מיוחדת)

Effective compliance date: August 14, 2025
"""

import re
import warnings
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import spacy
from transformers import pipeline

from .israeli_privacy_law import (
    ISRAELI_PRIVACY_CATEGORIES,
    get_special_sensitivity_categories,
    get_keywords_for_category,
    is_special_sensitivity,
    MEDICAL_KEYWORDS_HE, MEDICAL_KEYWORDS_EN,
    FINANCIAL_KEYWORDS_HE, FINANCIAL_KEYWORDS_EN,
    POLITICAL_KEYWORDS_HE, POLITICAL_KEYWORDS_EN,
    RELIGIOUS_KEYWORDS_HE, RELIGIOUS_KEYWORDS_EN,
    CRIMINAL_KEYWORDS_HE, CRIMINAL_KEYWORDS_EN
)

warnings.filterwarnings('ignore')


@dataclass
class PIIEntity:
    """Represents a detected PII entity according to Israeli Privacy Law"""
    text: str
    type: str  # Category from ISRAELI_PRIVACY_CATEGORIES
    start: int
    end: int
    confidence: float
    sensitivity_level: str  # "standard" or "special"


class IsraeliPIIDetector:
    """
    AI-powered PII detection compliant with Israeli Privacy Protection Law
    Amendment No. 13, 2024
    """

    def __init__(self, use_ai: bool = True):
        """
        Initialize Israeli PII Detector

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
            print("🔄 טוען מודלי AI... (עשוי לקחת זמן בהרצה ראשונה)")

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
                print("⚠️  מודל SpaCy לא נמצא. התקן עם: python -m spacy download xx_ent_wiki_sm")
                self.nlp = None

            print("✓ מודלי AI נטענו בהצלחה")

        except Exception as e:
            print(f"⚠️  אזהרה: לא ניתן לטעון מודלי AI: {e}")
            print("   עובר לזיהוי מבוסס Regex בלבד")
            self.use_ai = False

    def _compile_patterns(self):
        """Compile regex patterns for Israeli-specific PII"""

        # ===== Standard Personal Information =====

        # Israeli ID number (9 digits with Luhn validation)
        self.id_pattern = re.compile(r'\b\d{9}\b')

        # Israeli passport (old: 7 digits, new: 8 digits)
        self.passport_pattern = re.compile(r'\b\d{7,8}\b')

        # Israeli driver's license (7-8 digits)
        self.drivers_license_pattern = re.compile(r'\b(?:רישיון[:\s]+)?(\d{7,8})\b')

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

        # Addresses - Israeli format
        self.address_keywords = {
            'hebrew': [
                'רחוב', 'רח\'', 'שד\'', 'שדרות', 'כביש', 'דרך',
                'מעלה', 'סמטת', 'שכונת', 'דירה', 'קומה'
            ],
            'english': [
                'street', 'st.', 'avenue', 'ave.', 'road', 'rd.',
                'boulevard', 'blvd.', 'apartment', 'apt.', 'floor'
            ]
        }

        # Date of birth patterns (Israeli formats)
        self.dob_pattern = re.compile(
            r'''
            (?:
                # DD/MM/YYYY or DD.MM.YYYY or DD-MM-YYYY
                \b(?:0[1-9]|[12][0-9]|3[01])[\./-](?:0[1-9]|1[0-2])[\./-](?:19|20)\d{2}\b
                |
                # YYYY-MM-DD (ISO)
                \b(?:19|20)\d{2}[-](?:0[1-9]|1[0-2])[-](?:0[1-9]|[12][0-9]|3[01])\b
            )
            ''',
            re.VERBOSE
        )

        # ===== Specially Sensitive Information =====

        # Credit card numbers
        self.credit_card_pattern = re.compile(
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        )

        # Bank account (Israeli format)
        self.bank_account_pattern = re.compile(
            r'\b\d{2,3}[-/]\d{3,6}[-/]\d{1,2}\b'
        )

        # Israeli social security number (ביטוח לאומי)
        self.social_security_pattern = re.compile(
            r'\b(?:ביטוח\s+לאומי[:\s]+)?(\d{9})\b'
        )

    def detect_pii(self, text: str) -> Dict[str, List[PIIEntity]]:
        """
        Detect all PII entities in text according to Israeli Privacy Law

        Args:
            text: Input text to analyze

        Returns:
            Dictionary mapping PII type to list of entities
        """
        # Initialize results with all Israeli categories
        entities = {category: [] for category in ISRAELI_PRIVACY_CATEGORIES.keys()}

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

        # Context-based detection for specially sensitive info
        sensitive_entities = self._detect_special_sensitivity(text)
        for entity in sensitive_entities:
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
                    sensitivity = 'special' if is_special_sensitivity(entity_type) else 'standard'
                    entities.append(PIIEntity(
                        text=item['word'].strip(),
                        type=entity_type,
                        start=item['start'],
                        end=item['end'],
                        confidence=item['score'],
                        sensitivity_level=sensitivity
                    ))

            # Use spaCy if available
            if self.nlp:
                doc = self.nlp(text)
                for ent in doc.ents:
                    entity_type = self._map_spacy_entity(ent.label_)
                    if entity_type:
                        sensitivity = 'special' if is_special_sensitivity(entity_type) else 'standard'
                        entities.append(PIIEntity(
                            text=ent.text,
                            type=entity_type,
                            start=ent.start_char,
                            end=ent.end_char,
                            confidence=0.8,
                            sensitivity_level=sensitivity
                        ))

        except Exception as e:
            print(f"⚠️  אזהרת זיהוי AI: {e}")

        return entities

    def _detect_with_regex(self, text: str) -> List[PIIEntity]:
        """Use regex patterns to detect Israeli-specific PII"""
        entities = []

        # ID Numbers
        for match in self.id_pattern.finditer(text):
            if self._validate_israeli_id(match.group()):
                entities.append(PIIEntity(
                    text=match.group(),
                    type='ID_NUMBER',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95,
                    sensitivity_level='standard'
                ))

        # Phone numbers
        for match in self.phone_pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(),
                type='PHONE',
                start=match.start(),
                end=match.end(),
                confidence=0.9,
                sensitivity_level='standard'
            ))

        # Emails
        for match in self.email_pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(),
                type='EMAIL',
                start=match.start(),
                end=match.end(),
                confidence=0.95,
                sensitivity_level='standard'
            ))

        # Date of birth
        for match in self.dob_pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(),
                type='DATE_OF_BIRTH',
                start=match.start(),
                end=match.end(),
                confidence=0.85,
                sensitivity_level='standard'
            ))

        # Credit cards (specially sensitive)
        for match in self.credit_card_pattern.finditer(text):
            if self._validate_credit_card(match.group()):
                entities.append(PIIEntity(
                    text=match.group(),
                    type='CREDIT_CARD',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85,
                    sensitivity_level='special'
                ))

        # Bank accounts (specially sensitive)
        for match in self.bank_account_pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(),
                type='BANK_ACCOUNT',
                start=match.start(),
                end=match.end(),
                confidence=0.8,
                sensitivity_level='special'
            ))

        # Addresses
        address_entities = self._detect_addresses(text)
        entities.extend(address_entities)

        return entities

    def _detect_special_sensitivity(self, text: str) -> List[PIIEntity]:
        """
        Detect specially sensitive information based on context and keywords
        This covers categories defined in Amendment 13, Section 7(c)
        """
        entities = []

        # Medical information
        entities.extend(self._detect_by_keywords(
            text, MEDICAL_KEYWORDS_HE + MEDICAL_KEYWORDS_EN,
            'MEDICAL_INFO', 'special'
        ))

        # Financial/Salary information
        entities.extend(self._detect_by_keywords(
            text, FINANCIAL_KEYWORDS_HE + FINANCIAL_KEYWORDS_EN,
            'SALARY_FINANCIAL', 'special'
        ))

        # Political opinions
        entities.extend(self._detect_by_keywords(
            text, POLITICAL_KEYWORDS_HE + POLITICAL_KEYWORDS_EN,
            'POLITICAL_OPINION', 'special'
        ))

        # Religious beliefs
        entities.extend(self._detect_by_keywords(
            text, RELIGIOUS_KEYWORDS_HE + RELIGIOUS_KEYWORDS_EN,
            'RELIGIOUS_BELIEF', 'special'
        ))

        # Criminal records
        entities.extend(self._detect_by_keywords(
            text, CRIMINAL_KEYWORDS_HE + CRIMINAL_KEYWORDS_EN,
            'CRIMINAL_RECORD', 'special'
        ))

        return entities

    def _detect_by_keywords(
        self,
        text: str,
        keywords: List[str],
        category: str,
        sensitivity: str
    ) -> List[PIIEntity]:
        """Detect information based on keyword presence"""
        entities = []

        # Split text into sentences
        sentences = re.split(r'[.!?\n]+', text)

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Check if any keyword appears
            for keyword in keywords:
                if keyword.lower() in sentence_lower:
                    # Found sensitive context
                    start_pos = text.find(sentence)
                    if start_pos != -1:
                        entities.append(PIIEntity(
                            text=sentence.strip(),
                            type=category,
                            start=start_pos,
                            end=start_pos + len(sentence),
                            confidence=0.7,
                            sensitivity_level=sensitivity
                        ))
                    break  # One match per sentence is enough

        return entities

    def _detect_addresses(self, text: str) -> List[PIIEntity]:
        """Detect addresses based on keywords"""
        entities = []
        lines = text.split('\n')

        for line in lines:
            # Check for Hebrew address keywords
            for keyword in self.address_keywords['hebrew']:
                if keyword in line:
                    start_pos = text.find(line)
                    entities.append(PIIEntity(
                        text=line.strip(),
                        type='ADDRESS',
                        start=start_pos,
                        end=start_pos + len(line),
                        confidence=0.7,
                        sensitivity_level='standard'
                    ))
                    break

            # Check for English address keywords
            line_lower = line.lower()
            for keyword in self.address_keywords['english']:
                if keyword in line_lower:
                    start_pos = text.find(line)
                    entities.append(PIIEntity(
                        text=line.strip(),
                        type='ADDRESS',
                        start=start_pos,
                        end=start_pos + len(line),
                        confidence=0.7,
                        sensitivity_level='standard'
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
        """Map NER model entity labels to Israeli Privacy Law categories"""
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
        """Map spaCy entity labels to Israeli Privacy Law categories"""
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

    def _validate_entities(
        self,
        entities: Dict[str, List[PIIEntity]],
        text: str
    ) -> Dict[str, List[PIIEntity]]:
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

    def get_summary(self, entities: Dict[str, List[PIIEntity]]) -> Dict[str, any]:
        """Get count summary of detected entities with sensitivity levels"""
        standard_count = 0
        special_count = 0

        breakdown = {}
        for entity_type, entity_list in entities.items():
            if entity_list:
                breakdown[entity_type] = len(entity_list)

                if is_special_sensitivity(entity_type):
                    special_count += len(entity_list)
                else:
                    standard_count += len(entity_list)

        return {
            'total_entities': standard_count + special_count,
            'standard_personal_info': standard_count,
            'specially_sensitive_info': special_count,
            'breakdown': breakdown,
            'compliance': 'Israeli Privacy Protection Law - Amendment 13 (2024)'
        }
