from typing import List, Tuple


class ScoringEngine:
    """Deterministic scoring based on extracted clauses"""
    
    ELIGIBILITY_POINTS = 10
    VERDICT_THRESHOLDS = {
        "eligible": 0.8,
        "partially_eligible": 0.5
    }
    
    RISK_RULES = {
        "penalty_clause_present": 2,
        "short_deadline": 2,
        "high_emd": 2,
        "complex_scope": 1,
        "missing_key_docs": 1
    }
    
    EFFORT_RULES = {
        "many_documents": 2,
        "multi_location_execution": 2,
        "high_experience_required": 1,
        "high_turnover_required": 1
    }
    
    @staticmethod
    def calculate_eligibility(clause_evaluations: List[dict]) -> Tuple[str, int]:
        """Calculate eligibility verdict based on clause evaluations"""
        if not clause_evaluations:
            return "not_eligible", 0
        
        total_points = len(clause_evaluations) * ScoringEngine.ELIGIBILITY_POINTS
        scored_points = 0
        
        for clause in clause_evaluations:
            if clause.get("status") == "eligible":
                scored_points += ScoringEngine.ELIGIBILITY_POINTS
            elif clause.get("status") == "partially_eligible":
                scored_points += ScoringEngine.ELIGIBILITY_POINTS / 2
        
        ratio = scored_points / total_points if total_points > 0 else 0
        score_percent = round(ratio * 100)
        
        if ratio >= ScoringEngine.VERDICT_THRESHOLDS["eligible"]:
            verdict = "eligible"
        elif ratio >= ScoringEngine.VERDICT_THRESHOLDS["partially_eligible"]:
            verdict = "partially_eligible"
        else:
            verdict = "not_eligible"
        
        return verdict, score_percent
    
    @staticmethod
    def calculate_risk(risk_flags: List[str]) -> Tuple[int, str]:
        """Calculate risk score and level"""
        score = 0
        for flag in risk_flags:
            score += ScoringEngine.RISK_RULES.get(flag, 0)
        
        if score <= 2:
            level = "low"
        elif score <= 5:
            level = "medium"
        else:
            level = "high"
        
        return score, level
    
    @staticmethod
    def calculate_effort(effort_flags: List[str]) -> Tuple[int, str]:
        """Calculate effort score and level"""
        score = 0
        for flag in effort_flags:
            score += ScoringEngine.EFFORT_RULES.get(flag, 0)
        
        if score <= 2:
            level = "low"
        elif score <= 4:
            level = "medium"
        else:
            level = "high"
        
        return score, level
    
    @staticmethod
    def detect_risk_flags(text: str, deadline_days: int = None) -> List[str]:
        """Detect risk factors from tender text"""
        flags = []
        
        # Simple pattern matching for risk indicators
        penalty_keywords = ["penalty", "fine", "breach", "non-compliance", "forfeiture"]
        if any(kw.lower() in text.lower() for kw in penalty_keywords):
            flags.append("penalty_clause_present")
        
        if deadline_days and deadline_days < 7:
            flags.append("short_deadline")
        
        emd_keywords = ["emd", "earnest money deposit", "security deposit", "bid bond"]
        if any(kw.lower() in text.lower() for kw in emd_keywords):
            flags.append("high_emd")
        
        complex_keywords = ["complex", "intricate", "sophisticated", "multi-phase", "multiple locations"]
        if any(kw.lower() in text.lower() for kw in complex_keywords):
            flags.append("complex_scope")
        
        return flags
    
    @staticmethod
    def detect_effort_flags(text: str, turnover: float = None, years: int = None) -> List[str]:
        """Detect effort factors"""
        flags = []
        
        # Document count detection
        doc_keywords = ["document", "attachment", "annex", "exhibit", "appendix"]
        doc_count = sum(text.lower().count(kw) for kw in doc_keywords)
        if doc_count > 15:
            flags.append("many_documents")
        
        # Multi-location
        location_keywords = ["multiple locations", "nationwide", "across states", "multi-region"]
        if any(kw.lower() in text.lower() for kw in location_keywords):
            flags.append("multi_location_execution")
        
        # Experience requirement
        experience_keywords = ["5 years", "10 years", "15 years", "proven track record"]
        if any(kw.lower() in text.lower() for kw in experience_keywords):
            flags.append("high_experience_required")
        
        # Turnover requirement
        if turnover and turnover > 10_000_000:
            flags.append("high_turnover_required")
        
        return flags
