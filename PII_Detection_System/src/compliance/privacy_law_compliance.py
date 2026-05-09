"""
Privacy Law Compliance - תאימות לחוק הגנת הפרטיות תיקון 13
פרויקט גמר - זיהוי מידע אישי רגיש

מודול לבדיקת תאימות לחוק הגנת הפרטיות, התשמ״א-1981 (תיקון מס' 13)
"""

from typing import Dict, List
from enum import Enum
from dataclasses import dataclass


class PrivacyLawCategory(Enum):
    """קטגוריות מידע לפי חוק הגנת הפרטיות"""
    IDENTIFICATION = "מידע מזהה"  # סעיף 7 - ת.ז, דרכון
    FINANCIAL = "מידע פיננסי"  # סעיף 7(1) - חשבונות, אשראי
    MEDICAL = "מידע רפואי"  # סעיף 7(2) - מצב בריאות
    GENETIC = "מידע גנטי"  # סעיף 7(3)
    BIOMETRIC = "מידע ביומטרי"  # סעיף 7(4) - טביעות אצבע, זיהוי פנים
    SEXUAL_ORIENTATION = "נטייה מינית"  # סעיף 7(5)
    POLITICAL_OPINION = "דעות פוליטיות"  # סעיף 7(6)
    CRIMINAL_RECORD = "רישום פלילי"  # סעיף 7(7)
    LOCATION = "מיקום"  # סעיף 7א - מעקב אחר מיקום
    CONTACT = "פרטי התקשרות"  # טלפון, אימייל
    PERSONAL = "מידע אישי כללי"


class ComplianceStatus(Enum):
    """סטטוס תאימות למסמך"""
    COMPLIANT = "תקין - עומד בדרישות החוק"
    REQUIRES_REVIEW = "דורש בדיקה - יש מידע רגיש שצריך אישור"
    NON_COMPLIANT = "לא תקין - הפרת דרישות החוק"
    HIGH_RISK = "סיכון גבוה - מידע רגיש ביותר"


class ViolationType(Enum):
    """סוגי הפרות אפשריות"""
    SENSITIVE_DATA_EXPOSURE = "חשיפת מידע רגיש ללא הסכמה"
    EXCESSIVE_DATA_COLLECTION = "איסוף מידע מוגזם"
    LACK_OF_CONSENT = "העדר הסכמה מדווחת"
    IMPROPER_PURPOSE = "שימוש שלא למטרה המוצהרת"
    INSUFFICIENT_SECURITY = "אבטחה לא מספקת"
    UNAUTHORIZED_TRANSFER = "העברת מידע לא מורשית"


@dataclass
class ComplianceIssue:
    """תיאור בעיית תאימות"""
    violation_type: ViolationType
    category: PrivacyLawCategory
    description: str
    severity: str  # "קריטי", "גבוה", "בינוני", "נמוך"
    law_reference: str  # הפניה לסעיף בחוק
    recommendation: str


class PrivacyLawCompliance:
    """
    מחלקה לבדיקת תאימות לחוק הגנת הפרטיות תיקון 13
    """

    def __init__(self):
        """אתחול המודול"""

        # מיפוי בין קטגוריות PII לקטגוריות בחוק
        self.pii_to_law_mapping = {
            'israeli_id': PrivacyLawCategory.IDENTIFICATION,
            'phone_number': PrivacyLawCategory.CONTACT,
            'email': PrivacyLawCategory.CONTACT,
            'credit_card': PrivacyLawCategory.FINANCIAL,
            'bank_account': PrivacyLawCategory.FINANCIAL,
            'keyword_medical': PrivacyLawCategory.MEDICAL,
            'keyword_financial': PrivacyLawCategory.FINANCIAL,
            'keyword_personal': PrivacyLawCategory.PERSONAL,
            'keyword_identification': PrivacyLawCategory.IDENTIFICATION,
        }

        # הגדרת רמות רגישות לפי החוק
        self.sensitivity_by_category = {
            PrivacyLawCategory.IDENTIFICATION: "קריטי",
            PrivacyLawCategory.FINANCIAL: "קריטי",
            PrivacyLawCategory.MEDICAL: "קריטי",
            PrivacyLawCategory.GENETIC: "קריטי",
            PrivacyLawCategory.BIOMETRIC: "קריטי",
            PrivacyLawCategory.SEXUAL_ORIENTATION: "קריטי",
            PrivacyLawCategory.POLITICAL_OPINION: "גבוה",
            PrivacyLawCategory.CRIMINAL_RECORD: "קריטי",
            PrivacyLawCategory.LOCATION: "גבוה",
            PrivacyLawCategory.CONTACT: "בינוני",
            PrivacyLawCategory.PERSONAL: "נמוך",
        }

    def check_compliance(self, pii_results: Dict) -> Dict:
        """
        בדיקת תאימות מסמך לחוק הגנת הפרטיות
        """

        if not pii_results or not pii_results.get('matches'):
            return {
                'status': ComplianceStatus.COMPLIANT,
                'compliant': True,
                'issues': [],
                'summary': "✅ המסמך לא מכיל מידע אישי רגיש - תקין לפי החוק",
                'recommendations': ["המסמך בטוח לשיתוף ללא הגבלות"],
                'law_categories_found': [],
                'risk_level': 'נמוך'
            }

        # ניתוח הfindings
        issues = []
        law_categories_found = set()
        critical_count = 0

        for match in pii_results['matches']:
            # מיפוי לקטגוריית חוק
            law_category = self.pii_to_law_mapping.get(
                match.category,
                PrivacyLawCategory.PERSONAL
            )
            law_categories_found.add(law_category)

            # בדיקה אם זה מידע קריטי
            severity = self.sensitivity_by_category[law_category]

            if severity == "קריטי":
                critical_count += 1
                # יצירת issue
                issue = self._create_issue_for_match(match, law_category)
                if issue:
                    issues.append(issue)

        # קביעת סטטוס תאימות כללי
        status, compliant, risk_level = self._determine_compliance_status(
            critical_count,
            len(issues),
            law_categories_found
        )

        # יצירת סיכום והמלצות
        summary = self._generate_compliance_summary(status, critical_count, len(issues))
        recommendations = self._generate_recommendations(issues, law_categories_found)

        return {
            'status': status,
            'compliant': compliant,
            'issues': issues,
            'summary': summary,
            'recommendations': recommendations,
            'law_categories_found': [cat.value for cat in law_categories_found],
            'risk_level': risk_level,
            'critical_issues': critical_count,
            'total_issues': len(issues),
            'detailed_analysis': self._create_detailed_analysis(law_categories_found)
        }

    def _create_issue_for_match(self, match, law_category: PrivacyLawCategory) -> ComplianceIssue:
        """יצירת issue לפי סוג המידע"""

        severity = self.sensitivity_by_category[law_category]

        # קביעת סוג ההפרה
        if law_category in [PrivacyLawCategory.IDENTIFICATION,
                            PrivacyLawCategory.FINANCIAL]:
            violation_type = ViolationType.SENSITIVE_DATA_EXPOSURE
            law_ref = "סעיף 7 לחוק הגנת הפרטיות, תיקון 13"
            description = f"זוהה {law_category.value}: {match.text}"
            recommendation = f"יש להסיר או להצפין את {law_category.value}. נדרשת הסכמה מפורשת לפי סעיף 13א."

        elif law_category == PrivacyLawCategory.MEDICAL:
            violation_type = ViolationType.SENSITIVE_DATA_EXPOSURE
            law_ref = "סעיף 7(2) לחוק הגנת הפרטיות"
            description = f"זוהה מידע רפואי רגיש: {match.text}"
            recommendation = "מידע רפואי מוגן במיוחד. נדרשת הסכמה מפורשת ואבטחה מוגברת לפי תקנות אבטחת מידע."

        elif law_category == PrivacyLawCategory.CONTACT:
            violation_type = ViolationType.EXCESSIVE_DATA_COLLECTION
            law_ref = "עקרון המידתיות - סעיף 2 לחוק"
            description = f"זוהה פרטי התקשרות: {match.text}"
            recommendation = "וודא שפרטי ההתקשרות נאספו למטרה לגיטימית ובהסכמה."

        else:
            violation_type = ViolationType.LACK_OF_CONSENT
            law_ref = "סעיף 13א לחוק"
            description = f"זוהה מידע אישי: {match.text}"
            recommendation = "וודא קיום הסכמה לשימוש במידע זה."

        return ComplianceIssue(
            violation_type=violation_type,
            category=law_category,
            description=description,
            severity=severity,
            law_reference=law_ref,
            recommendation=recommendation
        )

    def _determine_compliance_status(self, critical_count: int,
                                     total_issues: int,
                                     categories: set) -> tuple:
        """קביעת סטטוס תאימות"""

        # בדיקת קטגוריות מיוחדות
        has_critical_category = any(
            cat in [PrivacyLawCategory.IDENTIFICATION,
                    PrivacyLawCategory.FINANCIAL,
                    PrivacyLawCategory.MEDICAL,
                    PrivacyLawCategory.GENETIC,
                    PrivacyLawCategory.BIOMETRIC]
            for cat in categories
        )

        if critical_count >= 3 or has_critical_category:
            return ComplianceStatus.HIGH_RISK, False, "גבוה מאוד"
        elif critical_count >= 1:
            return ComplianceStatus.NON_COMPLIANT, False, "גבוה"
        elif total_issues > 0:
            return ComplianceStatus.REQUIRES_REVIEW, True, "בינוני"
        else:
            return ComplianceStatus.COMPLIANT, True, "נמוך"

    def _generate_compliance_summary(self, status: ComplianceStatus,
                                     critical: int, total: int) -> str:
        """יצירת סיכום תאימות"""

        if status == ComplianceStatus.COMPLIANT:
            return "✅ המסמך תקין ועומד בדרישות חוק הגנת הפרטיות"

        elif status == ComplianceStatus.REQUIRES_REVIEW:
            return f"⚠️ המסמך דורש בדיקה - Found {total} בעיות תאימות פוטנציאליות"

        elif status == ComplianceStatus.NON_COMPLIANT:
            return f"❌ המסמך לא תקין - Found {critical} בעיות קריטיות שדורשות טיפול מיידי"

        else:  # HIGH_RISK
            return f"🚨 סיכון גבוה! Found {critical} בעיות קריטיות. המסמך אינו עומד בדרישות החוק"

    def _generate_recommendations(self, issues: List[ComplianceIssue],
                                  categories: set) -> List[str]:
        """יצירת המלצות לתיקון"""

        recommendations = []

        if not issues:
            recommendations.append("✅ המסמך תקין - אין צורך בפעולות נוספות")
            return recommendations

        # המלצות כלליות
        recommendations.append("📋 פעולות נדרשות לתאימות לחוק:")
        recommendations.append("")

        # המלצות ספציפיות לפי קטגוריות
        if PrivacyLawCategory.IDENTIFICATION in categories:
            recommendations.append("🆔 מידע מזהה:")
            recommendations.append("  • הסר או הצפן מספרי תעודת זהות")
            recommendations.append("  • קבל הסכמה מפורשת לפי סעיף 13א")
            recommendations.append("  • תעד את מטרת השימוש במידע")
            recommendations.append("")

        if PrivacyLawCategory.FINANCIAL in categories:
            recommendations.append("💳 מידע פיננסי:")
            recommendations.append("  • הצפן מספרי חשבון ואשראי")
            recommendations.append("  • הגבל גישה רק למורשים")
            recommendations.append("  • נהל לוג גישה למידע")
            recommendations.append("")

        if PrivacyLawCategory.MEDICAL in categories:
            recommendations.append("🏥 מידע רפואי:")
            recommendations.append("  • נדרשת הסכמה מפורשת בכתב")
            recommendations.append("  • אבטחה מוגברת לפי תקנות")
            recommendations.append("  • הגבל שיתוף למקרים מוצדקים בלבד")
            recommendations.append("")

        # המלצות כלליות
        recommendations.append("🔒 המלצות אבטחה:")
        recommendations.append("  • שמור את המידע במאגר מאובטח")
        recommendations.append("  • הגבל גישה ע״י סיסמה והרשאות")
        recommendations.append("  • צור מדיניות אבטחת מידע")
        recommendations.append("  • הכשר עובדים על חוק הגנת הפרטיות")
        recommendations.append("")

        recommendations.append("📞 לייעוץ משפטי:")
        recommendations.append("  • התייעץ עם יועץ משפטי בנושא הגנת פרטיות")
        recommendations.append("  • רשום את המאגר ברשם מאגרי המידע אם נדרש")

        return recommendations

    def _create_detailed_analysis(self, categories: set) -> Dict:
        """יצירת ניתוח מפורט"""

        analysis = {
            'categories_details': {},
            'legal_requirements': [],
            'consent_required': False,
            'registration_required': False,
        }

        for category in categories:
            analysis['categories_details'][category.value] = {
                'severity': self.sensitivity_by_category[category],
                'legal_protection': self._get_legal_protection_level(category)
            }

        # בדיקת דרישות
        critical_categories = [
            PrivacyLawCategory.IDENTIFICATION,
            PrivacyLawCategory.FINANCIAL,
            PrivacyLawCategory.MEDICAL,
            PrivacyLawCategory.GENETIC,
            PrivacyLawCategory.BIOMETRIC,
        ]

        if any(cat in categories for cat in critical_categories):
            analysis['consent_required'] = True
            analysis['registration_required'] = True
            analysis['legal_requirements'].append("נדרשת הסכמה מפורשת של בעל המידע")
            analysis['legal_requirements'].append("יש לרשום מאגר ברשם מאגרי המידע")
            analysis['legal_requirements'].append("נדרש מינוי אחראי על אבטחת מידע")

        return analysis

    def _get_legal_protection_level(self, category: PrivacyLawCategory) -> str:
        """קבלת רמת ההגנה המשפטית"""

        high_protection = [
            PrivacyLawCategory.IDENTIFICATION,
            PrivacyLawCategory.FINANCIAL,
            PrivacyLawCategory.MEDICAL,
            PrivacyLawCategory.GENETIC,
            PrivacyLawCategory.BIOMETRIC,
            PrivacyLawCategory.SEXUAL_ORIENTATION,
            PrivacyLawCategory.CRIMINAL_RECORD,
        ]

        if category in high_protection:
            return "הגנה מוגברת - סעיף 7 לחוק"
        else:
            return "הגנה רגילה"

    def generate_compliance_report(self, compliance_results: Dict) -> str:
        """יצירת דוח תאימות מלא"""

        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("דוח תאימות לחוק הגנת הפרטיות, התשמ״א-1981 (תיקון מס' 13)")
        report_lines.append("=" * 70)
        report_lines.append("")

        # סטטוס
        report_lines.append(f"📊 סטטוס: {compliance_results['status'].value}")
        report_lines.append(f"🎯 תקין: {'כן' if compliance_results['compliant'] else 'לא'}")
        report_lines.append(f"⚠️ Risk level: {compliance_results['risk_level']}")
        report_lines.append("")

        # סיכום
        report_lines.append("📋 סיכום:")
        report_lines.append(compliance_results['summary'])
        report_lines.append("")

        # קטגוריות שנמצאו
        if compliance_results['law_categories_found']:
            report_lines.append("🔍 קטגוריות מידע שזוהו:")
            for cat in compliance_results['law_categories_found']:
                report_lines.append(f"  • {cat}")
            report_lines.append("")

        # בעיות
        if compliance_results['issues']:
            report_lines.append(f"⚠️ בעיות תאימות ({len(compliance_results['issues'])}):")
            report_lines.append("")

            for i, issue in enumerate(compliance_results['issues'], 1):
                report_lines.append(f"{i}. {issue.description}")
                report_lines.append(f"   חומרה: {issue.severity}")
                report_lines.append(f"   הפניה משפטית: {issue.law_reference}")
                report_lines.append(f"   המלצה: {issue.recommendation}")
                report_lines.append("")

        # המלצות
        report_lines.append("💡 המלצות:")
        for rec in compliance_results['recommendations']:
            report_lines.append(rec)

        report_lines.append("")
        report_lines.append("=" * 70)

        return "\n".join(report_lines)


# פונקציות עזר
def quick_compliance_check(pii_results: Dict) -> bool:
    """בדיקה מהירה - האם תקין או לא"""
    checker = PrivacyLawCompliance()
    result = checker.check_compliance(pii_results)
    return result['compliant']


if __name__ == "__main__":
    print("⚖️ בדיקת מודול תאימות לחוק הגנת הפרטיות")
    print("=" * 50)

    checker = PrivacyLawCompliance()
    print("✅ מודול תאימות מוכן!")
    print("\nהמודול בודק תאימות לפי:")
    print("• חוק הגנת הפרטיות, התשמ״א-1981")
    print("• תיקון מס' 13 - הגנה מוגברת על מידע רגיש")
    print("• סעיף 7 - סוגי מידע רגיש")
    print("• סעיף 13א - דרישת הסכמה")