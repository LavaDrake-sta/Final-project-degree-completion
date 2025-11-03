"""
Israeli Privacy Protection Law - Amendment 13 Compliance
Defines categories according to Israeli Privacy Protection Law (Amendment No. 13), 2024
Effective date: August 14, 2025
"""

from dataclasses import dataclass
from typing import List, Set

@dataclass
class PrivacyLawCategory:
    """Category of personal information according to Israeli law"""
    name: str
    hebrew_name: str
    sensitivity_level: str  # "standard" or "special"
    description: str


# Categories defined by Amendment 13 to Israeli Privacy Protection Law
ISRAELI_PRIVACY_CATEGORIES = {
    # Standard Personal Information
    'ID_NUMBER': PrivacyLawCategory(
        name='ID_NUMBER',
        hebrew_name='מספר תעודת זהות',
        sensitivity_level='standard',
        description='Israeli ID number (9 digits)'
    ),

    'PASSPORT_NUMBER': PrivacyLawCategory(
        name='PASSPORT_NUMBER',
        hebrew_name='מספר דרכון',
        sensitivity_level='standard',
        description='Passport number'
    ),

    'DRIVERS_LICENSE': PrivacyLawCategory(
        name='DRIVERS_LICENSE',
        hebrew_name='מספר רישיון נהיגה',
        sensitivity_level='standard',
        description='Driver license number'
    ),

    'PERSON': PrivacyLawCategory(
        name='PERSON',
        hebrew_name='שם אדם',
        sensitivity_level='standard',
        description='Person name'
    ),

    'PHONE': PrivacyLawCategory(
        name='PHONE',
        hebrew_name='מספר טלפון',
        sensitivity_level='standard',
        description='Phone number'
    ),

    'EMAIL': PrivacyLawCategory(
        name='EMAIL',
        hebrew_name='דוא"ל',
        sensitivity_level='standard',
        description='Email address'
    ),

    'ADDRESS': PrivacyLawCategory(
        name='ADDRESS',
        hebrew_name='כתובת מגורים',
        sensitivity_level='standard',
        description='Residential address'
    ),

    'DATE_OF_BIRTH': PrivacyLawCategory(
        name='DATE_OF_BIRTH',
        hebrew_name='תאריך לידה',
        sensitivity_level='standard',
        description='Date of birth'
    ),

    # Specially Sensitive Information (מידע בעל רגישות מיוחדת)
    # According to Amendment 13, Section 7(c)

    'MEDICAL_INFO': PrivacyLawCategory(
        name='MEDICAL_INFO',
        hebrew_name='מידע רפואי',
        sensitivity_level='special',
        description='Medical information, health conditions, treatments'
    ),

    'GENETIC_INFO': PrivacyLawCategory(
        name='GENETIC_INFO',
        hebrew_name='מידע גנטי',
        sensitivity_level='special',
        description='Genetic information and DNA data'
    ),

    'BIOMETRIC_ID': PrivacyLawCategory(
        name='BIOMETRIC_ID',
        hebrew_name='מזהה ביומטרי',
        sensitivity_level='special',
        description='Biometric identifiers (fingerprints, face recognition, etc.)'
    ),

    'SEXUAL_ORIENTATION': PrivacyLawCategory(
        name='SEXUAL_ORIENTATION',
        hebrew_name='נטייה מינית',
        sensitivity_level='special',
        description='Sexual orientation'
    ),

    'POLITICAL_OPINION': PrivacyLawCategory(
        name='POLITICAL_OPINION',
        hebrew_name='דעה פוליטית',
        sensitivity_level='special',
        description='Political opinions and affiliations'
    ),

    'RELIGIOUS_BELIEF': PrivacyLawCategory(
        name='RELIGIOUS_BELIEF',
        hebrew_name='אמונה דתית',
        sensitivity_level='special',
        description='Religious beliefs and practices'
    ),

    'CRIMINAL_RECORD': PrivacyLawCategory(
        name='CRIMINAL_RECORD',
        hebrew_name='עבר פלילי',
        sensitivity_level='special',
        description='Criminal history and records'
    ),

    'LOCATION_DATA': PrivacyLawCategory(
        name='LOCATION_DATA',
        hebrew_name='נתוני מיקום',
        sensitivity_level='special',
        description='Location and tracking data'
    ),

    'ETHNIC_ORIGIN': PrivacyLawCategory(
        name='ETHNIC_ORIGIN',
        hebrew_name='מוצא אתני',
        sensitivity_level='special',
        description='Ethnic or racial origin'
    ),

    'PERSONALITY_ASSESSMENT': PrivacyLawCategory(
        name='PERSONALITY_ASSESSMENT',
        hebrew_name='הערכת תכונות אישיות',
        sensitivity_level='special',
        description='Personality traits assessment'
    ),

    'SALARY_FINANCIAL': PrivacyLawCategory(
        name='SALARY_FINANCIAL',
        hebrew_name='שכר ונתוני פעילות כלכלית',
        sensitivity_level='special',
        description='Salary and financial activity data'
    ),

    'CREDIT_CARD': PrivacyLawCategory(
        name='CREDIT_CARD',
        hebrew_name='כרטיס אשראי',
        sensitivity_level='special',
        description='Credit card number'
    ),

    'BANK_ACCOUNT': PrivacyLawCategory(
        name='BANK_ACCOUNT',
        hebrew_name='חשבון בנק',
        sensitivity_level='special',
        description='Bank account number'
    ),

    'FAMILY_PRIVACY': PrivacyLawCategory(
        name='FAMILY_PRIVACY',
        hebrew_name='פרטיות חיי המשפחה',
        sensitivity_level='special',
        description='Family life privacy information'
    ),

    'CONFIDENTIAL_INFO': PrivacyLawCategory(
        name='CONFIDENTIAL_INFO',
        hebrew_name='מידע חסוי מכוח דין',
        sensitivity_level='special',
        description='Information subject to confidentiality by law'
    ),

    # Additional categories
    'ORGANIZATION': PrivacyLawCategory(
        name='ORGANIZATION',
        hebrew_name='ארגון',
        sensitivity_level='standard',
        description='Organization name'
    ),

    'LOCATION': PrivacyLawCategory(
        name='LOCATION',
        hebrew_name='מיקום גיאוגרפי',
        sensitivity_level='standard',
        description='Geographic location'
    ),
}


def get_special_sensitivity_categories() -> Set[str]:
    """Get list of specially sensitive categories per Amendment 13"""
    return {
        name for name, cat in ISRAELI_PRIVACY_CATEGORIES.items()
        if cat.sensitivity_level == 'special'
    }


def get_standard_categories() -> Set[str]:
    """Get list of standard personal information categories"""
    return {
        name for name, cat in ISRAELI_PRIVACY_CATEGORIES.items()
        if cat.sensitivity_level == 'standard'
    }


def get_category_hebrew_name(category: str) -> str:
    """Get Hebrew name for category"""
    if category in ISRAELI_PRIVACY_CATEGORIES:
        return ISRAELI_PRIVACY_CATEGORIES[category].hebrew_name
    return category


def is_special_sensitivity(category: str) -> bool:
    """Check if category is specially sensitive per Amendment 13"""
    if category in ISRAELI_PRIVACY_CATEGORIES:
        return ISRAELI_PRIVACY_CATEGORIES[category].sensitivity_level == 'special'
    return False


# Keywords for detecting specially sensitive information
MEDICAL_KEYWORDS_HE = [
    'רופא', 'בית חולים', 'קופת חולים', 'מרפאה', 'מחלה', 'אבחנה',
    'טיפול', 'תרופה', 'רפואי', 'בריאות', 'חולה', 'מכאב', 'סימפטום',
    'בדיקת דם', 'צילום רנטגן', 'CT', 'MRI', 'אופרציה', 'ניתוח'
]

MEDICAL_KEYWORDS_EN = [
    'doctor', 'hospital', 'clinic', 'medical', 'health', 'disease',
    'diagnosis', 'treatment', 'medication', 'patient', 'pain', 'symptom',
    'blood test', 'x-ray', 'surgery', 'prescription'
]

FINANCIAL_KEYWORDS_HE = [
    'משכורת', 'שכר', 'הכנסה', 'הלוואה', 'משכנתא', 'חוב', 'אשראי',
    'כרטיס אשראי', 'חשבון בנק', 'העברה בנקאית', 'מס הכנסה'
]

FINANCIAL_KEYWORDS_EN = [
    'salary', 'income', 'loan', 'mortgage', 'debt', 'credit',
    'credit card', 'bank account', 'transfer', 'income tax'
]

POLITICAL_KEYWORDS_HE = [
    'מפלגה', 'הצבעה', 'בחירות', 'קלפי', 'מועמד', 'פוליטי',
    'ימין', 'שמאל', 'מרכז', 'קואליציה', 'אופוזיציה'
]

POLITICAL_KEYWORDS_EN = [
    'party', 'vote', 'election', 'candidate', 'political',
    'left', 'right', 'coalition', 'opposition'
]

RELIGIOUS_KEYWORDS_HE = [
    'דת', 'דתי', 'חילוני', 'חרדי', 'כשר', 'כשרות', 'שבת',
    'תפילה', 'בית כנסת', 'כנסייה', 'מסגד', 'רב', 'כומר', 'אימאם'
]

RELIGIOUS_KEYWORDS_EN = [
    'religion', 'religious', 'secular', 'kosher', 'prayer',
    'synagogue', 'church', 'mosque', 'rabbi', 'priest', 'imam'
]

CRIMINAL_KEYWORDS_HE = [
    'עבר פלילי', 'הרשעה', 'עבירה', 'משטרה', 'מעצר', 'כלא',
    'בית משפט', 'פסק דין', 'תיק פלילי', 'עונש'
]

CRIMINAL_KEYWORDS_EN = [
    'criminal record', 'conviction', 'offense', 'police', 'arrest',
    'prison', 'court', 'sentence', 'criminal case', 'punishment'
]


def get_keywords_for_category(category: str) -> List[str]:
    """Get detection keywords for specially sensitive categories"""
    keywords_map = {
        'MEDICAL_INFO': MEDICAL_KEYWORDS_HE + MEDICAL_KEYWORDS_EN,
        'SALARY_FINANCIAL': FINANCIAL_KEYWORDS_HE + FINANCIAL_KEYWORDS_EN,
        'POLITICAL_OPINION': POLITICAL_KEYWORDS_HE + POLITICAL_KEYWORDS_EN,
        'RELIGIOUS_BELIEF': RELIGIOUS_KEYWORDS_HE + RELIGIOUS_KEYWORDS_EN,
        'CRIMINAL_RECORD': CRIMINAL_KEYWORDS_HE + CRIMINAL_KEYWORDS_EN,
    }

    return keywords_map.get(category, [])
