"""
AI Decision Engine - מנוע החלטות AI אוטומטי
פרויקט גמר - זיהוי מידע אישי רגיש

מנוע בינה מלאכותית לקבלת החלטות אוטומטיות על תאימות מסמכים
"""

from typing import Dict, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class Decision(Enum):
    """החלטות אפשריות"""
    APPROVED = "✅ מאושר - המסמך תקין"
    APPROVED_WITH_CONDITIONS = "✅⚠️ מאושר בתנאים - דורש תיקונים קלים"
    REQUIRES_MODIFICATIONS = "⚠️ דורש שינויים - יש לתקן לפני שימוש"
    REJECTED = "❌ נדחה - המסמך לא עומד בדרישות"
    CRITICAL_VIOLATION = "🚨 הפרה קריטית - אסור להשתמש במסמך זה"


class RiskScore(Enum):
    """ציון סיכון"""
    VERY_LOW = (0, 20, "נמוך מאוד")
    LOW = (21, 40, "נמוך")
    MEDIUM = (41, 60, "בינוני")
    HIGH = (61, 80, "גבוה")
    CRITICAL = (81, 100, "קריטי")


@dataclass
class AIDecisionResult:
    """תוצאת החלטת AI"""
    decision: Decision
    risk_score: int  # 0-100
    risk_level: str
    confidence: float  # 0-1
    reasoning: List[str]
    required_actions: List[str]
    estimated_fix_time: str
    legal_implications: List[str]
    timestamp: str


class AIDecisionEngine:
    """
    מנוע החלטות AI מתקדם
    מנתח מסמכים ומחליט אוטומטית על תקינותם
    """

    def __init__(self):
        """אתחול מנוע ההחלטות"""

        # משקלות לחישוב ציון סיכון
        self.risk_weights = {
            'critical_pii_count': 30,  # מספר ממצאים קריטיים
            'high_pii_count': 15,  # ממצאים ברמה גבוהה
            'total_pii_count': 10,  # סך כל הממצאים
            'critical_categories': 25,  # קטגוריות קריטיות (ת.ז, רפואי)
            'compliance_issues': 20,  # בעיות תאימות
        }

    def make_decision(self, pii_results: Dict, compliance_results: Dict) -> AIDecisionResult:
        """
        קבלת החלטה אוטומטית על המסמך
        """

        # חישוב ציון סיכון
        risk_score = self._calculate_risk_score(pii_results, compliance_results)
        risk_level = self._get_risk_level(risk_score)

        # קביעת ההחלטה
        decision = self._determine_decision(risk_score, compliance_results)

        # חישוב רמת ביטחון בהחלטה
        confidence = self._calculate_confidence(pii_results, compliance_results)

        # יצירת נימוקים
        reasoning = self._generate_reasoning(
            pii_results, compliance_results, risk_score, decision
        )

        # פעולות נדרשות
        required_actions = self._generate_required_actions(
            decision, compliance_results, pii_results
        )

        # הערכת זמן תיקון
        estimated_fix_time = self._estimate_fix_time(
            pii_results, compliance_results, decision
        )

        # השלכות משפטיות
        legal_implications = self._assess_legal_implications(
            compliance_results, risk_score
        )

        return AIDecisionResult(
            decision=decision,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=confidence,
            reasoning=reasoning,
            required_actions=required_actions,
            estimated_fix_time=estimated_fix_time,
            legal_implications=legal_implications,
            timestamp=datetime.now().isoformat()
        )

    def _calculate_risk_score(self, pii_results: Dict, compliance_results: Dict) -> int:
        """חישוב ציון סיכון (0-100)"""

        score = 0

        # ספירת ממצאים לפי רמת רגישות
        critical_count = 0
        high_count = 0

        if pii_results.get('matches'):
            for match in pii_results['matches']:
                if match.sensitivity.name == 'CRITICAL':
                    critical_count += 1
                elif match.sensitivity.name == 'HIGH':
                    high_count += 1

        # חישוב ציון
        score += min(critical_count * 10, self.risk_weights['critical_pii_count'])
        score += min(high_count * 5, self.risk_weights['high_pii_count'])
        score += min(len(pii_results.get('matches', [])) * 2,
                     self.risk_weights['total_pii_count'])

        # קטגוריות קריטיות
        critical_categories = ['israeli_id', 'credit_card']
        has_critical = any(
            m.category in critical_categories
            for m in pii_results.get('matches', [])
        )
        if has_critical:
            score += self.risk_weights['critical_categories']

        # בעיות תאימות
        if compliance_results.get('total_issues', 0) > 0:
            score += min(
                compliance_results['total_issues'] * 5,
                self.risk_weights['compliance_issues']
            )

        return min(score, 100)

    def _get_risk_level(self, score: int) -> str:
        """קביעת רמת סיכון על בסיס הציון"""

        for risk_enum in RiskScore:
            min_score, max_score, level_name = risk_enum.value
            if min_score <= score <= max_score:
                return level_name

        return "לא ידוע"

    def _determine_decision(self, risk_score: int, compliance_results: Dict) -> Decision:
        """קביעת ההחלטה הסופית"""

        # בדיקות קריטיות
        if risk_score >= 81:
            return Decision.CRITICAL_VIOLATION

        if not compliance_results.get('compliant', True):
            if compliance_results.get('critical_issues', 0) >= 3:
                return Decision.REJECTED
            elif compliance_results.get('critical_issues', 0) >= 1:
                return Decision.REQUIRES_MODIFICATIONS

        # בדיקות לפי ציון
        if risk_score <= 20:
            return Decision.APPROVED
        elif risk_score <= 40:
            return Decision.APPROVED_WITH_CONDITIONS
        elif risk_score <= 60:
            return Decision.REQUIRES_MODIFICATIONS
        else:
            return Decision.REJECTED

    def _calculate_confidence(self, pii_results: Dict, compliance_results: Dict) -> float:
        """חישוב רמת ביטחון בהחלטה (0-1)"""

        confidence = 1.0

        # הפחתת ביטחון אם יש אי-וודאות
        if pii_results.get('matches'):
            avg_match_confidence = sum(
                m.confidence for m in pii_results['matches']
            ) / len(pii_results['matches'])
            confidence *= avg_match_confidence

        # הפחתת ביטחון אם יש מעט ממצאים (אולי יש עוד שלא זוהו)
        if len(pii_results.get('matches', [])) < 3:
            confidence *= 0.9

        return round(confidence, 2)

    def _generate_reasoning(self, pii_results: Dict, compliance_results: Dict,
                            risk_score: int, decision: Decision) -> List[str]:
        """יצירת נימוקים להחלטה"""

        reasoning = []

        # הסבר כללי
        reasoning.append(f"🎯 ציון סיכון: {risk_score}/100")
        reasoning.append(
            f"📊 סטטוס תאימות: {compliance_results.get('status', 'לא ידוע').value if hasattr(compliance_results.get('status', ''), 'value') else 'לא ידוע'}")
        reasoning.append("")

        # ניתוח ממצאים
        total_matches = len(pii_results.get('matches', []))
        if total_matches > 0:
            reasoning.append(f"🔍 נמצאו {total_matches} פריטי מידע רגיש:")

            # ספירה לפי סוג
            by_sensitivity = {}
            for match in pii_results['matches']:
                sens = match.sensitivity.name
                by_sensitivity[sens] = by_sensitivity.get(sens, 0) + 1

            for sens, count in sorted(by_sensitivity.items(), reverse=True):
                icon = "🔴" if sens == "CRITICAL" else "🟠" if sens == "HIGH" else "🟡"
                reasoning.append(f"  {icon} {sens}: {count} ממצאים")
            reasoning.append("")

        # נימוק ההחלטה
        if decision == Decision.APPROVED:
            reasoning.append("✅ הנימוק: המסמך נקי ממידע רגיש מדאיג")

        elif decision == Decision.APPROVED_WITH_CONDITIONS:
            reasoning.append("⚠️ הנימוק: יש מידע רגיש אך הוא מנוהל בצורה סבירה")
            reasoning.append("   דורש תשומת לב קלה לפני שימוש")

        elif decision == Decision.REQUIRES_MODIFICATIONS:
            reasoning.append("⚠️ הנימוק: נמצא מידע רגיש שדורש טיפול")
            reasoning.append("   יש לתקן את הבעיות לפני שימוש במסמך")

        elif decision == Decision.REJECTED:
            reasoning.append("❌ הנימוק: המסמך מכיל מידע רגיש בכמות מדאיגה")
            reasoning.append("   לא ניתן לאשר את המסמך במצבו הנוכחי")

        elif decision == Decision.CRITICAL_VIOLATION:
            reasoning.append("🚨 הנימוק: זוהתה הפרת פרטיות חמורה")
            reasoning.append("   המסמך מהווה סיכון משפטי משמעותי")

        return reasoning

    def _generate_required_actions(self, decision: Decision,
                                   compliance_results: Dict,
                                   pii_results: Dict) -> List[str]:
        """יצירת רשימת פעולות נדרשות"""

        actions = []

        if decision == Decision.APPROVED:
            actions.append("✅ אין פעולות נדרשות - המסמך ניתן לשימוש")
            return actions

        actions.append("📋 פעולות נדרשות:")
        actions.append("")

        # פעולות לפי סוג הבעיה
        if pii_results.get('matches'):
            # בדיקה לפי קטגוריות
            has_id = any(m.category == 'israeli_id' for m in pii_results['matches'])
            has_credit = any(m.category == 'credit_card' for m in pii_results['matches'])
            has_phone = any(m.category == 'phone_number' for m in pii_results['matches'])
            has_email = any(m.category == 'email' for m in pii_results['matches'])

            if has_id:
                actions.append("🔴 דחוף: הסר או הצפן את מספרי תעודת הזהות")

            if has_credit:
                actions.append("🔴 דחוף: הסר או הצפן את מספרי כרטיסי האשראי")

            if has_phone:
                actions.append("🟠 החלף מספרי טלפון ב-05X-XXXXXXX או הסר")

            if has_email:
                actions.append("🟠 שקול הסתרת כתובות אימייל או השתמש בכתובות כלליות")

        actions.append("")
        actions.append("📝 פעולות כלליות:")
        actions.append("  1. סקור את כל הממצאים ברשימה")
        actions.append("  2. תקן או הסר מידע רגיש")
        actions.append("  3. הרץ שוב את הבדיקה")
        actions.append("  4. אם נדרש - התייעץ עם יועץ משפטי")

        if decision == Decision.CRITICAL_VIOLATION:
            actions.append("")
            actions.append("🚨 חשוב: אל תשתף או תשתמש במסמך זה עד לתיקון!")

        return actions

    def _estimate_fix_time(self, pii_results: Dict, compliance_results: Dict,
                           decision: Decision) -> str:
        """הערכת זמן תיקון"""

        if decision == Decision.APPROVED:
            return "0 דקות - אין צורך בתיקון"

        total_issues = len(pii_results.get('matches', []))

        if total_issues <= 3:
            return "5-10 דקות"
        elif total_issues <= 10:
            return "15-30 דקות"
        elif total_issues <= 20:
            return "30-60 דקות"
        else:
            return "1-2 שעות"

    def _assess_legal_implications(self, compliance_results: Dict,
                                   risk_score: int) -> List[str]:
        """הערכת השלכות משפטיות"""

        implications = []

        if risk_score <= 40:
            implications.append("✅ סיכון משפטי נמוך")
            implications.append("המסמך לא צפוי לגרום לבעיות משפטיות")

        elif risk_score <= 60:
            implications.append("⚠️ סיכון משפטי בינוני")
            implications.append("מומלץ לתקן לפני שימוש ציבורי")
            implications.append("ייתכנו תלונות לרשות הגנת הפרטיות")

        elif risk_score <= 80:
            implications.append("❌ סיכון משפטי גבוה")
            implications.append("חשיפת מידע עלולה להוביל לתביעות אזרחיות")
            implications.append("הפרה אפשרית של חוק הגנת הפרטיות")
            implications.append("קנס פלילי אפשרי: עד 232,000 ₪")

        else:
            implications.append("🚨 סיכון משפטי קריטי")
            implications.append("הפרה חמורה של חוק הגנת הפרטיות")
            implications.append("חשיפה לתביעות ייצוגיות")
            implications.append("קנס פלילי: עד 232,000 ₪ למקרה")
            implications.append("נזקים אזרחיים: ללא הגבלה")
            implications.append("פגיעה חמורה במוניטין החברה")

        return implications

    def generate_decision_report(self, decision_result: AIDecisionResult) -> str:
        """יצירת דוח החלטה מפורט"""

        report = []
        report.append("=" * 70)
        report.append("דוח החלטה אוטומטי - מנוע AI")
        report.append("=" * 70)
        report.append("")

        # החלטה
        report.append(f"🎯 החלטה: {decision_result.decision.value}")
        report.append(f"📊 ציון סיכון: {decision_result.risk_score}/100 ({decision_result.risk_level})")
        report.append(f"🎲 רמת ביטחון: {decision_result.confidence:.0%}")
        report.append(f"🕐 זמן: {decision_result.timestamp}")
        report.append("")

        # נימוקים
        report.append("🧠 נימוקי ההחלטה:")
        for reason in decision_result.reasoning:
            report.append(reason)
        report.append("")

        # פעולות נדרשות
        report.append("📋 פעולות נדרשות:")
        for action in decision_result.required_actions:
            report.append(action)
        report.append("")

        # זמן תיקון
        report.append(f"⏱️ זמן תיקון משוער: {decision_result.estimated_fix_time}")
        report.append("")

        # השלכות משפטיות
        report.append("⚖️ השלכות משפטיות:")
        for implication in decision_result.legal_implications:
            report.append(f"  {implication}")
        report.append("")

        report.append("=" * 70)

        return "\n".join(report)


# פונקציה מהירה להחלטה
def quick_decision(pii_results: Dict, compliance_results: Dict) -> str:
    """קבלת החלטה מהירה - מאושר/נדחה"""
    engine = AIDecisionEngine()
    result = engine.make_decision(pii_results, compliance_results)
    return result.decision.value


if __name__ == "__main__":
    print("🤖 בדיקת מנוע החלטות AI")
    print("=" * 40)

    engine = AIDecisionEngine()
    print("✅ מנוע ההחלטות מוכן!")
    print("\nהמנוע מספק:")
    print("• החלטה אוטומטית על תקינות המסמך")
    print("• ציון סיכון 0-100")
    print("• נימוקים מפורטים")
    print("• פעולות נדרשות")
    print("• הערכת זמן תיקון")
    print("• השלכות משפטיות")