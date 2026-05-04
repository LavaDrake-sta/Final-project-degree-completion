"""
Decision Engine — הערכת סיכון
שיפורים:
  - ישויות קריטיות מורחבות
  - Summary בעברית
  - לוגים
"""

from typing import List, Dict, Any

try:
    from src.logger_config import get_logger
except ImportError:
    try:
        from logger_config import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger(name)

logger = get_logger("PII.Pipeline.Decision")


class DecisionEngine:
    """
    מעריך את ישויות ה-PII שזוהו ומחזיר רמת סיכון.
    """

    RISK_SAFE    = "SAFE"
    RISK_WARNING = "WARNING"
    RISK_UNSAFE  = "UNSAFE"

    # ישויות קריטיות (כל אחת מהן מספיקה להכריז UNSAFE)
    CRITICAL_ENTITIES = {
        "IL_ID",
        "CREDIT_CARD",
        "CRYPTO",
        "IBAN_CODE",
        "MEDICAL_LICENSE",
        "IL_PERSONAL_NUMBER",
        "US_SSN",
        "DATE_OF_BIRTH",
        "IL_BANK_ACCOUNT",
    }

    # תרגום לעברית
    ENTITY_HEBREW = {
        "IL_ID":             "תעודת זהות ישראלית",
        "IL_PHONE":          "מספר טלפון ישראלי",
        "HEB_ADDRESS":       "כתובת בעברית",
        "HEB_NAME":          "שם בעברית",
        "DATE_OF_BIRTH":     "תאריך לידה",
        "IL_PERSONAL_NUMBER":"מספר אישי",
        "IL_BANK_ACCOUNT":   "חשבון בנק",
        "IL_BANK_BRANCH":    "סניף בנק",
        "PERSON":            "שם אדם",
        "EMAIL_ADDRESS":     "כתובת אימייל",
        "PHONE_NUMBER":      "מספר טלפון",
        "CREDIT_CARD":       "כרטיס אשראי",
        "IBAN_CODE":         "IBAN (חשבון בנק)",
        "CRYPTO":            "ארנק קריפטו",
        "LOCATION":          "מיקום / כתובת",
        "DATE_TIME":         "תאריך / שעה",
        "NRP":               "לאום / דת / גזע",
        "MEDICAL_LICENSE":   "רישיון רפואי",
        "URL":               "כתובת אתר",
        "IP_ADDRESS":        "כתובת IP",
        "US_SSN":            "מזהה אמריקאי (SSN)",
        "JOB_TITLE":         "תפקיד",
        "PROFESSION":        "מקצוע",
        "PASSWORD":          "סיסמה",
        "HEALTH_FUND":       "מספר עמית קופת חולים",
        "IL_COMPANY_ID":     "ח.פ / תיק ניכויים",
        "context_password":  "סיסמה",
        "context_health_fund": "קופת חולים",
        "context_company_id": "ח.פ / תיק ניכויים",
        "MEDICAL_RECORD":     "מספר תיק רפואי",
        "BLOOD_TYPE":         "סוג דם",
        "MILITARY_PROFILE":   "פרופיל צבאי/רפואי",
        "CVV":                "קוד אבטחה (CVV)",
        "AUTH_CODE":          "קוד אימות / PIN",
        "USERNAME":           "שם משתמש",
        "PASSPORT":           "דרכון",
        "DRIVER_LICENSE":     "רישיון נהיגה",
        "LICENSE_PLATE":      "לוחית רישוי / רכב",
        "MAC_ADDRESS":        "כתובת MAC",
        "ZIPCODE":            "מיקוד",
        "context_medical_record": "תיק רפואי",
        "context_blood_type": "סוג דם",
        "context_military_profile": "פרופיל צבאי",
        "context_cvv": "קוד אבטחה (CVV)",
        "context_auth_code": "קוד אימות",
        "context_username": "שם משתמש",
        "context_passport": "דרכון",
        "context_driver_license": "רישיון נהיגה",
        "context_license_plate": "לוחית רישוי",
        "context_mac_address": "כתובת MAC",
        "context_zipcode": "מיקוד",
    }

    def __init__(self):
        logger.info("🔧 DecisionEngine מוכן")

    def translate_entity(self, entity_type: str) -> str:
        return self.ENTITY_HEBREW.get(entity_type, entity_type)

    def evaluate(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        מעריך את רשימת הישויות ומחזיר רמת סיכון וסיכום.
        """
        if not entities:
            return {
                "risk_level":     self.RISK_SAFE,
                "summary":        "✅ לא זוהה מידע רגיש במסמך.",
                "critical_count": 0,
                "total_count":    0,
                "critical_types": [],
            }

        total_count    = len(entities)
        critical_types = list({e["entity_type"] for e in entities
                                if e["entity_type"] in self.CRITICAL_ENTITIES})
        critical_count = len([e for e in entities
                               if e["entity_type"] in self.CRITICAL_ENTITIES])

        if critical_count > 0:
            risk_level = self.RISK_UNSAFE
            types_str  = ", ".join(self.translate_entity(t) for t in critical_types)
            summary    = (
                f"🚨 זוהו {critical_count} ישויות קריטיות מתוך {total_count} סה\"כ. "
                f"סוגים: {types_str}"
            )
        elif total_count >= 3:
            risk_level = self.RISK_UNSAFE
            summary    = f"🚨 זוהה נפח גבוה ({total_count}) של פריטי מידע רגיש."
        else:
            risk_level = self.RISK_WARNING
            summary    = f"⚠️ זוהו {total_count} פריטי מידע ברמת רגישות בינונית."

        logger.info(f"⚠️ סיכון: {risk_level} | {summary}")

        return {
            "risk_level":     risk_level,
            "summary":        summary,
            "critical_count": critical_count,
            "total_count":    total_count,
            "critical_types": critical_types,
        }
