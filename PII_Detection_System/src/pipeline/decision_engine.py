from typing import List, Dict, Any

class DecisionEngine:
    """
    Evaluates the detected PII entities and assigns a risk level.
    """
    
    RISK_SAFE = "SAFE"
    RISK_WARNING = "WARNING"
    RISK_UNSAFE = "UNSAFE"
    
    # Define which entity types are considered critical
    CRITICAL_ENTITIES = {
        "IL_ID", 
        "CREDIT_CARD", 
        "CRYPTO", 
        "IBAN_CODE", 
        "MEDICAL_LICENSE"
    }

    def __init__(self):
        pass

    def evaluate(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate the list of entities and determine risk.
        Returns a dictionary with the risk level and a summary.
        """
        if not entities:
            return {
                "risk_level": self.RISK_SAFE,
                "summary": "No sensitive information detected.",
                "critical_count": 0,
                "total_count": 0
            }
            
        total_count = len(entities)
        critical_count = sum(1 for e in entities if e["entity_type"] in self.CRITICAL_ENTITIES)
        
        # Decision Logic
        if critical_count > 0:
            risk_level = self.RISK_UNSAFE
            summary = f"Detected {critical_count} CRITICAL sensitive entities out of {total_count} total."
        elif total_count >= 3:
            risk_level = self.RISK_UNSAFE
            summary = f"Detected a high volume ({total_count}) of sensitive entities."
        else:
            risk_level = self.RISK_WARNING
            summary = f"Detected {total_count} medium-sensitivity entities."
            
        return {
            "risk_level": risk_level,
            "summary": summary,
            "critical_count": critical_count,
            "total_count": total_count
        }
