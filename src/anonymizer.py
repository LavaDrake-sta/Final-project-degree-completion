"""
Anonymizer Module
Hides/redacts detected PII from text
"""

from typing import Dict, List
from enum import Enum
from .pii_detector_il import PIIEntity


class AnonymizationMode(Enum):
    """Different modes for anonymizing PII"""
    REDACT = "redact"  # Replace with [REDACTED]
    MASK = "mask"      # Replace with ***
    REPLACE = "replace"  # Replace with placeholder like [NAME], [EMAIL]
    HASH = "hash"      # Replace with hash (preserves uniqueness)


class PIIAnonymizer:
    """Anonymize detected PII entities"""

    def __init__(self, mode: AnonymizationMode = AnonymizationMode.REPLACE):
        """
        Initialize anonymizer

        Args:
            mode: Anonymization mode to use
        """
        self.mode = mode

    def anonymize(self, text: str, entities: Dict[str, List[PIIEntity]]) -> str:
        """
        Anonymize text by replacing PII entities

        Args:
            text: Original text
            entities: Detected PII entities

        Returns:
            Anonymized text
        """
        # Collect all entities with positions
        all_entities = []
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                all_entities.append((entity.start, entity.end, entity_type, entity.text))

        # Sort by position (reverse order to maintain positions)
        all_entities.sort(reverse=True)

        # Replace entities
        anonymized_text = text
        for start, end, entity_type, original_text in all_entities:
            replacement = self._get_replacement(entity_type, original_text)
            anonymized_text = anonymized_text[:start] + replacement + anonymized_text[end:]

        return anonymized_text

    def anonymize_preserving_structure(
        self,
        text: str,
        entities: Dict[str, List[PIIEntity]]
    ) -> str:
        """
        Anonymize while preserving text structure (length)

        Args:
            text: Original text
            entities: Detected PII entities

        Returns:
            Anonymized text with preserved structure
        """
        all_entities = []
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                all_entities.append((entity.start, entity.end, entity_type, entity.text))

        all_entities.sort(reverse=True)

        anonymized_text = text
        for start, end, entity_type, original_text in all_entities:
            # Create replacement that matches original length
            replacement = self._get_replacement_with_length(
                entity_type,
                original_text,
                end - start
            )
            anonymized_text = anonymized_text[:start] + replacement + anonymized_text[end:]

        return anonymized_text

    def _get_replacement(self, entity_type: str, original_text: str) -> str:
        """Get replacement text based on anonymization mode"""

        if self.mode == AnonymizationMode.REDACT:
            return "[REDACTED]"

        elif self.mode == AnonymizationMode.MASK:
            return "***"

        elif self.mode == AnonymizationMode.REPLACE:
            # Use descriptive placeholders
            placeholders = {
                'PERSON': '[שם אדם]',
                'ID_NUMBER': '[תעודת זהות]',
                'PHONE': '[טלפון]',
                'EMAIL': '[דוא"ל]',
                'ADDRESS': '[כתובת]',
                'CREDIT_CARD': '[כרטיס אשראי]',
                'BANK_ACCOUNT': '[חשבון בנק]',
                'ORGANIZATION': '[ארגון]',
                'LOCATION': '[מיקום]'
            }
            return placeholders.get(entity_type, '[מידע רגיש]')

        elif self.mode == AnonymizationMode.HASH:
            # Simple hash for demonstration
            import hashlib
            hash_obj = hashlib.sha256(original_text.encode())
            return f"[{hash_obj.hexdigest()[:8]}]"

        return "[REDACTED]"

    def _get_replacement_with_length(
        self,
        entity_type: str,
        original_text: str,
        target_length: int
    ) -> str:
        """Get replacement text that matches original length"""

        if self.mode == AnonymizationMode.MASK:
            return '*' * target_length

        # For other modes, try to match length with placeholder
        placeholder = self._get_replacement(entity_type, original_text)

        if len(placeholder) > target_length:
            return placeholder[:target_length]
        elif len(placeholder) < target_length:
            # Pad with spaces
            padding = target_length - len(placeholder)
            return placeholder + ' ' * padding
        else:
            return placeholder

    def create_side_by_side_comparison(
        self,
        original: str,
        entities: Dict[str, List[PIIEntity]],
        max_length: int = 100
    ) -> str:
        """
        Create a comparison showing original vs anonymized text

        Args:
            original: Original text
            entities: Detected PII entities
            max_length: Maximum length per line

        Returns:
            Formatted comparison string
        """
        anonymized = self.anonymize(original, entities)

        lines = []
        lines.append("=" * 80)
        lines.append("השוואה: מקור לעומת טקסט מוסתר")
        lines.append("=" * 80)
        lines.append("")

        # Split into chunks if too long
        if len(original) > max_length:
            lines.append("מקור (חלק ראשון):")
            lines.append(original[:max_length] + "...")
            lines.append("")
            lines.append("מוסתר (חלק ראשון):")
            lines.append(anonymized[:max_length] + "...")
        else:
            lines.append("מקור:")
            lines.append(original)
            lines.append("")
            lines.append("מוסתר:")
            lines.append(anonymized)

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def get_statistics(self, entities: Dict[str, List[PIIEntity]]) -> Dict:
        """
        Get anonymization statistics

        Args:
            entities: Detected PII entities

        Returns:
            Statistics dictionary
        """
        total_entities = sum(len(elist) for elist in entities.values())

        stats = {
            'total_entities_found': total_entities,
            'breakdown': {},
            'anonymization_mode': self.mode.value
        }

        for entity_type, entity_list in entities.items():
            if entity_list:
                stats['breakdown'][entity_type] = {
                    'count': len(entity_list),
                    'examples': [e.text for e in entity_list[:3]]  # First 3 examples
                }

        return stats


def anonymize_text(
    text: str,
    entities: Dict[str, List[PIIEntity]],
    mode: str = "replace"
) -> str:
    """
    Quick function to anonymize text

    Args:
        text: Original text
        entities: Detected PII entities
        mode: Anonymization mode (redact/mask/replace/hash)

    Returns:
        Anonymized text
    """
    mode_enum = AnonymizationMode(mode)
    anonymizer = PIIAnonymizer(mode=mode_enum)
    return anonymizer.anonymize(text, entities)
