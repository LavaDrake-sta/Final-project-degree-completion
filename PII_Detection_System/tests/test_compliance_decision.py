import pytest
from unittest.mock import MagicMock
from datetime import datetime

from src.compliance.privacy_law_compliance import (
    PrivacyLawCompliance,
    PrivacyLawCategory,
    ComplianceStatus,
    ViolationType,
    quick_compliance_check
)
from src.compliance.ai_decision_engine import (
    AIDecisionEngine,
    Decision,
    RiskScore,
    AIDecisionResult,
    quick_decision
)

# ==========================================
# ⚖️ PrivacyLawCompliance Tests
# ==========================================

def test_privacy_law_compliance_empty():
    checker = PrivacyLawCompliance()
    res = checker.check_compliance({})
    
    assert res['compliant'] is True
    assert res['status'] == ComplianceStatus.COMPLIANT
    assert len(res['issues']) == 0
    assert "לא מכיל מידע אישי" in res['summary']

def test_privacy_law_compliance_critical():
    checker = PrivacyLawCompliance()
    
    # Mock a critical match, e.g. credit card
    match = MagicMock()
    match.category = "credit_card"
    match.text = "4580-1234-5678-9012"
    
    pii_results = {"matches": [match]}
    res = checker.check_compliance(pii_results)
    
    assert res['compliant'] is False
    assert res['status'] == ComplianceStatus.HIGH_RISK or res['status'] == ComplianceStatus.NON_COMPLIANT
    assert len(res['issues']) == 1
    assert res['issues'][0].category == PrivacyLawCategory.FINANCIAL
    assert "מידע פיננסי" in res['law_categories_found']
    
    # Test quick check
    assert quick_compliance_check(pii_results) is False

def test_privacy_law_compliance_report():
    checker = PrivacyLawCompliance()
    
    match = MagicMock()
    match.category = "phone_number"
    match.text = "052-1234567"
    
    pii_results = {"matches": [match]}
    res = checker.check_compliance(pii_results)
    
    report = checker.generate_compliance_report(res)
    assert "דוח תאימות" in report
    assert "סטטוס:" in report


# ==========================================
# 🤖 AIDecisionEngine Tests
# ==========================================

def test_ai_decision_engine_approved():
    engine = AIDecisionEngine()
    
    pii_results = {"matches": []}
    compliance_results = {
        "compliant": True,
        "status": ComplianceStatus.COMPLIANT,
        "total_issues": 0,
        "critical_issues": 0,
        "summary": "OK"
    }
    
    res = engine.make_decision(pii_results, compliance_results)
    
    assert res.decision == Decision.APPROVED
    assert res.risk_score == 0
    assert res.risk_level == "נמוך מאוד"
    assert "APPROVED" in res.decision.name

def test_ai_decision_engine_rejected():
    engine = AIDecisionEngine()
    
    # Mock critical matches
    match1 = MagicMock()
    match1.category = "israeli_id"
    match1.sensitivity.name = "CRITICAL"
    match1.confidence = 0.95
    
    match2 = MagicMock()
    match2.category = "credit_card"
    match2.sensitivity.name = "CRITICAL"
    match2.confidence = 0.9
    
    pii_results = {"matches": [match1, match2]}
    compliance_results = {
        "compliant": False,
        "status": ComplianceStatus.HIGH_RISK,
        "total_issues": 2,
        "critical_issues": 2,
        "summary": "CRITICAL ISSUES"
    }
    
    res = engine.make_decision(pii_results, compliance_results)
    
    # High risk score because of critical matches and categories
    assert res.risk_score > 50
    assert res.decision in [Decision.REJECTED, Decision.REQUIRES_MODIFICATIONS, Decision.CRITICAL_VIOLATION]
    assert len(res.reasoning) > 0
    assert len(res.required_actions) > 0
    
    # Test quick decision helper
    qd = quick_decision(pii_results, compliance_results)
    assert qd == res.decision.value

def test_ai_decision_report():
    engine = AIDecisionEngine()
    
    res = AIDecisionResult(
        decision=Decision.APPROVED,
        risk_score=10,
        risk_level="Low",
        confidence=0.9,
        reasoning=["OK"],
        required_actions=["None"],
        estimated_fix_time="0m",
        legal_implications=["None"],
        timestamp=datetime.now().isoformat()
    )
    
    report = engine.generate_decision_report(res)
    assert "דוח החלטה" in report
    assert "APPROVED" in report or "מאושר" in report
