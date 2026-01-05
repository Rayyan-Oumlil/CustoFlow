"""Quality Assurance & Compliance System"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class QAChecker:
    """
    Quality Assurance and Compliance checker for agent responses.
    """
    
    def __init__(self):
        """Initialize the QA checker."""
        # Compliance keywords (GDPR, privacy, etc.)
        self.compliance_keywords = {
            "gdpr": ["gdpr", "data protection", "personal data", "right to be forgotten", "data subject"],
            "privacy": ["privacy policy", "privacy", "personal information", "data privacy", "confidential"],
            "security": ["security breach", "data breach", "hack", "unauthorized access", "security issue"],
            "legal": ["lawsuit", "legal action", "attorney", "lawyer", "sue", "litigation"],
            "financial": ["refund policy", "money back", "chargeback", "payment issue", "billing"]
        }
        
        # Profanity detection (common words - can be expanded)
        self.profanity_patterns = [
            r'\b(shit|damn|hell|fuck|asshole|bitch)\b',  # Common profanity
            r'\b(idiot|stupid|dumb|moron)\b',  # Insults
        ]
        
        # Quality indicators
        self.positive_quality_indicators = [
            "helpful", "clear", "professional", "polite", "thank you", "please",
            "understand", "apologize", "sorry", "assist", "support"
        ]
        
        self.negative_quality_indicators = [
            "i don't know", "can't help", "not my problem", "not responsible",
            "blame", "fault", "your mistake", "you should have"
        ]
    
    def check_response(
        self,
        response: str,
        user_message: Optional[str] = None,
        agent_used: Optional[str] = None
    ) -> Dict:
        """
        Perform comprehensive QA check on a response.
        
        Args:
            response: The agent's response text
            user_message: Optional user message for context
            agent_used: Optional agent name for tracking
            
        Returns:
            Dict with QA results:
            {
                "quality_score": float (0.0-1.0),
                "compliance_flags": List[str],
                "profanity_detected": bool,
                "quality_issues": List[str],
                "quality_strengths": List[str],
                "overall_status": "pass|warning|fail",
                "recommendations": List[str]
            }
        """
        result = {
            "quality_score": 1.0,  # Start with perfect score
            "compliance_flags": [],
            "profanity_detected": False,
            "quality_issues": [],
            "quality_strengths": [],
            "overall_status": "pass",
            "recommendations": []
        }
        
        response_lower = response.lower()
        
        # 1. Check for profanity
        profanity_found = self._check_profanity(response)
        if profanity_found:
            result["profanity_detected"] = True
            result["quality_score"] -= 0.5  # Major penalty
            result["quality_issues"].append("Profanity detected in response")
            result["overall_status"] = "fail"
        
        # 2. Check compliance keywords
        compliance_flags = self._check_compliance(response_lower)
        if compliance_flags:
            result["compliance_flags"] = compliance_flags
            result["quality_score"] -= 0.1 * len(compliance_flags)  # Penalty per flag
            result["quality_issues"].append(f"Compliance keywords detected: {', '.join(compliance_flags)}")
            if result["overall_status"] == "pass":
                result["overall_status"] = "warning"
        
        # 3. Check quality indicators
        quality_analysis = self._check_quality_indicators(response_lower)
        result["quality_strengths"] = quality_analysis["strengths"]
        result["quality_issues"].extend(quality_analysis["issues"])
        
        # Adjust score based on quality indicators
        if quality_analysis["issues"]:
            result["quality_score"] -= 0.1 * len(quality_analysis["issues"])
        if quality_analysis["strengths"]:
            result["quality_score"] += 0.05 * len(quality_analysis["strengths"])  # Bonus for good practices
        
        # 4. Check response length (too short or too long)
        if len(response) < 20:
            result["quality_issues"].append("Response is too short (may lack detail)")
            result["quality_score"] -= 0.1
        elif len(response) > 2000:
            result["quality_issues"].append("Response is very long (may be overwhelming)")
            result["quality_score"] -= 0.05
        
        # 5. Check for helpfulness (contains actionable information)
        if not self._is_helpful(response_lower):
            result["quality_issues"].append("Response may lack actionable information")
            result["quality_score"] -= 0.1
        
        # 6. Check for politeness
        if not self._is_polite(response_lower):
            result["quality_issues"].append("Response may lack politeness")
            result["quality_score"] -= 0.1
        
        # Ensure score is between 0.0 and 1.0
        result["quality_score"] = max(0.0, min(1.0, result["quality_score"]))
        
        # Determine overall status
        if result["quality_score"] < 0.5:
            result["overall_status"] = "fail"
        elif result["quality_score"] < 0.7:
            result["overall_status"] = "warning"
        else:
            result["overall_status"] = "pass"
        
        # Generate recommendations
        result["recommendations"] = self._generate_recommendations(result)
        
        return result
    
    def _check_profanity(self, text: str) -> bool:
        """Check for profanity in text."""
        text_lower = text.lower()
        for pattern in self.profanity_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _check_compliance(self, text_lower: str) -> List[str]:
        """Check for compliance-related keywords."""
        flags = []
        for category, keywords in self.compliance_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    flags.append(category)
                    break  # Only flag once per category
        return flags
    
    def _check_quality_indicators(self, text_lower: str) -> Dict:
        """Check for positive and negative quality indicators."""
        strengths = []
        issues = []
        
        # Check positive indicators
        for indicator in self.positive_quality_indicators:
            if indicator in text_lower:
                strengths.append(f"Uses {indicator} (good practice)")
        
        # Check negative indicators
        for indicator in self.negative_quality_indicators:
            if indicator in text_lower:
                issues.append(f"Contains negative phrase: '{indicator}'")
        
        return {
            "strengths": strengths,
            "issues": issues
        }
    
    def _is_helpful(self, text_lower: str) -> bool:
        """Check if response appears helpful."""
        helpful_indicators = [
            "here", "you can", "i can help", "let me", "i'll", "i will",
            "solution", "option", "suggest", "recommend", "try"
        ]
        return any(indicator in text_lower for indicator in helpful_indicators)
    
    def _is_polite(self, text_lower: str) -> bool:
        """Check if response is polite."""
        polite_indicators = [
            "please", "thank you", "sorry", "apologize", "appreciate",
            "welcome", "glad", "happy to help"
        ]
        return any(indicator in text_lower for indicator in polite_indicators)
    
    def _generate_recommendations(self, result: Dict) -> List[str]:
        """Generate recommendations based on QA results."""
        recommendations = []
        
        if result["profanity_detected"]:
            recommendations.append("⚠️ CRITICAL: Remove profanity from response")
        
        if result["compliance_flags"]:
            recommendations.append(f"⚠️ Review compliance concerns: {', '.join(result['compliance_flags'])}")
        
        if result["quality_score"] < 0.7:
            recommendations.append("Consider improving response clarity and helpfulness")
        
        if not result["quality_strengths"]:
            recommendations.append("Add polite phrases and helpful language")
        
        if len(result["quality_issues"]) > 2:
            recommendations.append("Multiple quality issues detected - review response carefully")
        
        return recommendations
    
    def check_batch(self, responses: List[Dict]) -> Dict:
        """
        Check multiple responses and generate aggregate report.
        
        Args:
            responses: List of dicts with 'response', 'user_message', 'agent_used'
            
        Returns:
            Aggregate QA report
        """
        total_score = 0.0
        total_responses = len(responses)
        failed_count = 0
        warning_count = 0
        all_compliance_flags = set()
        profanity_count = 0
        
        for resp_data in responses:
            result = self.check_response(
                response=resp_data.get("response", ""),
                user_message=resp_data.get("user_message"),
                agent_used=resp_data.get("agent_used")
            )
            
            total_score += result["quality_score"]
            if result["overall_status"] == "fail":
                failed_count += 1
            elif result["overall_status"] == "warning":
                warning_count += 1
            
            all_compliance_flags.update(result["compliance_flags"])
            if result["profanity_detected"]:
                profanity_count += 1
        
        avg_score = total_score / total_responses if total_responses > 0 else 0.0
        
        return {
            "total_responses": total_responses,
            "average_quality_score": round(avg_score, 3),
            "failed_count": failed_count,
            "warning_count": warning_count,
            "pass_count": total_responses - failed_count - warning_count,
            "compliance_flags_found": list(all_compliance_flags),
            "profanity_detected_count": profanity_count,
            "overall_status": "pass" if failed_count == 0 and warning_count < total_responses * 0.2 else "warning"
        }


# Singleton instance
_qa_checker: Optional[QAChecker] = None


def get_qa_checker() -> QAChecker:
    """Get singleton instance of QAChecker."""
    global _qa_checker
    if _qa_checker is None:
        _qa_checker = QAChecker()
    return _qa_checker

