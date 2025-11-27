"""
A/B Testing Framework for Agent Optimization

Tests different agent instructions and response strategies to optimize customer satisfaction.
Uses statistical analysis to determine which variant performs better.
"""
import logging
import statistics
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ABTesting:
    """
    A/B Testing system for comparing agent variants.
    """
    
    def __init__(self):
        """Initialize the A/B Testing system."""
        self.active_tests: Dict[str, Dict] = {}  # agent_name -> test config
        self.variant_metrics: Dict[str, Dict] = defaultdict(lambda: {
            "variant_a": {
                "conversations": 0,
                "satisfaction_scores": [],
                "response_times": [],
                "escalations": 0,
                "resolutions": 0,
                "thumbs_up": 0,
                "thumbs_down": 0
            },
            "variant_b": {
                "conversations": 0,
                "satisfaction_scores": [],
                "response_times": [],
                "escalations": 0,
                "resolutions": 0,
                "thumbs_up": 0,
                "thumbs_down": 0
            }
        })
        
        # Load active tests from database
        self._load_active_tests()
    
    def _load_active_tests(self):
        """Load active A/B tests from database."""
        try:
            from utils.supabase_client import SUPABASE_ENABLED, supabase
            if SUPABASE_ENABLED:
                # Check if ab_tests table exists (we'll create it if needed)
                # For now, we'll use in-memory storage
                logger.info("A/B Testing: Using in-memory storage (can be migrated to Supabase)")
        except Exception as e:
            logger.debug(f"Could not load A/B tests from database: {e}")
    
    def create_test(
        self,
        agent_name: str,
        variant_a_instruction: str,
        variant_b_instruction: str,
        description: Optional[str] = None
    ) -> bool:
        """
        Create a new A/B test for an agent.
        
        Args:
            agent_name: Name of the agent to test (e.g., "order_agent")
            variant_a_instruction: Instruction for variant A (current/control)
            variant_b_instruction: Instruction for variant B (test)
            description: Optional description of the test
            
        Returns:
            True if test created successfully
        """
        try:
            self.active_tests[agent_name] = {
                "agent_name": agent_name,
                "variant_a_instruction": variant_a_instruction,
                "variant_b_instruction": variant_b_instruction,
                "description": description or f"A/B test for {agent_name}",
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Initialize metrics if not exists
            if agent_name not in self.variant_metrics:
                self.variant_metrics[agent_name] = {
                    "variant_a": {
                        "conversations": 0,
                        "satisfaction_scores": [],
                        "response_times": [],
                        "escalations": 0,
                        "resolutions": 0,
                        "thumbs_up": 0,
                        "thumbs_down": 0
                    },
                    "variant_b": {
                        "conversations": 0,
                        "satisfaction_scores": [],
                        "response_times": [],
                        "escalations": 0,
                        "resolutions": 0,
                        "thumbs_up": 0,
                        "thumbs_down": 0
                    }
                }
            
            logger.info(f"Created A/B test for {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            return False
    
    def get_variant(self, agent_name: str, user_id: str) -> str:
        """
        Get which variant to use for a user (A or B).
        Uses consistent hashing to ensure same user always gets same variant.
        
        Args:
            agent_name: Name of the agent
            user_id: User identifier
            
        Returns:
            "variant_a" or "variant_b"
        """
        if agent_name not in self.active_tests:
            return "variant_a"  # Default to A if no test active
        
        # Use consistent hashing based on user_id
        # This ensures same user always gets same variant
        hash_value = hash(f"{agent_name}_{user_id}") % 2
        
        if hash_value == 0:
            return "variant_a"
        else:
            return "variant_b"
    
    def record_metrics(
        self,
        agent_name: str,
        variant: str,
        satisfaction_score: Optional[float] = None,
        response_time: Optional[float] = None,
        escalated: bool = False,
        resolved: bool = False,
        thumbs_up: bool = False,
        thumbs_down: bool = False
    ) -> None:
        """
        Record metrics for a variant.
        
        Args:
            agent_name: Name of the agent
            variant: "variant_a" or "variant_b"
            satisfaction_score: Optional satisfaction score (0.0-1.0)
            response_time: Optional response time in seconds
            escalated: Whether conversation was escalated
            resolved: Whether issue was resolved
            thumbs_up: Whether user gave thumbs up
            thumbs_down: Whether user gave thumbs down
        """
        if agent_name not in self.variant_metrics:
            return
        
        if agent_name not in self.variant_metrics:
            self.variant_metrics[agent_name] = {
                "variant_a": {
                    "conversations": 0,
                    "satisfaction_scores": [],
                    "response_times": [],
                    "escalations": 0,
                    "resolutions": 0,
                    "thumbs_up": 0,
                    "thumbs_down": 0
                },
                "variant_b": {
                    "conversations": 0,
                    "satisfaction_scores": [],
                    "response_times": [],
                    "escalations": 0,
                    "resolutions": 0,
                    "thumbs_up": 0,
                    "thumbs_down": 0
                }
            }
        
        metrics = self.variant_metrics[agent_name][variant]
        
        metrics["conversations"] = metrics["conversations"] + 1
        
        if satisfaction_score is not None:
            metrics["satisfaction_scores"].append(satisfaction_score)
        
        if response_time is not None:
            metrics["response_times"].append(response_time)
        
        if escalated:
            metrics["escalations"] = metrics["escalations"] + 1
        
        if resolved:
            metrics["resolutions"] = metrics["resolutions"] + 1
        
        if thumbs_up:
            metrics["thumbs_up"] = metrics["thumbs_up"] + 1
        
        if thumbs_down:
            metrics["thumbs_down"] = metrics["thumbs_down"] + 1
    
    def get_test_results(self, agent_name: str) -> Dict:
        """
        Get A/B test results for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dict with test results and statistical analysis
        """
        if agent_name not in self.active_tests:
            return {
                "status": "no_test",
                "message": f"No active A/B test for {agent_name}"
            }
        
        if agent_name not in self.variant_metrics:
            return {
                "status": "no_data",
                "message": "No metrics collected yet"
            }
        
        metrics = self.variant_metrics[agent_name]
        variant_a = metrics.get("variant_a", {})
        variant_b = metrics.get("variant_b", {})
        
        # Calculate statistics
        a_stats = self._calculate_stats(variant_a)
        b_stats = self._calculate_stats(variant_b)
        
        # Determine winner
        winner = self._determine_winner(a_stats, b_stats)
        
        # Statistical significance
        significance = self._calculate_significance(variant_a, variant_b)
        
        return {
            "status": "active",
            "agent_name": agent_name,
            "description": self.active_tests[agent_name].get("description"),
            "variant_a": {
                "conversations": variant_a.get("conversations", 0),
                "stats": a_stats,
                "instruction_preview": self.active_tests[agent_name].get("variant_a_instruction", "")[:100] + "..."
            },
            "variant_b": {
                "conversations": variant_b.get("conversations", 0),
                "stats": b_stats,
                "instruction_preview": self.active_tests[agent_name].get("variant_b_instruction", "")[:100] + "..."
            },
            "winner": winner,
            "significance": significance,
            "recommendation": self._get_recommendation(winner, significance)
        }
    
    def _calculate_stats(self, variant_metrics: Dict) -> Dict:
        """Calculate statistics for a variant."""
        stats = {
            "avg_satisfaction": 0.0,
            "avg_response_time": 0.0,
            "escalation_rate": 0.0,
            "resolution_rate": 0.0,
            "thumbs_up_rate": 0.0,
            "thumbs_down_rate": 0.0
        }
        
        conversations = variant_metrics.get("conversations", 0)
        if conversations == 0:
            return stats
        
        satisfaction_scores = variant_metrics.get("satisfaction_scores", [])
        if satisfaction_scores:
            stats["avg_satisfaction"] = statistics.mean(satisfaction_scores)
        
        response_times = variant_metrics.get("response_times", [])
        if response_times:
            stats["avg_response_time"] = statistics.mean(response_times)
        
        stats["escalation_rate"] = variant_metrics.get("escalations", 0) / conversations
        stats["resolution_rate"] = variant_metrics.get("resolutions", 0) / conversations
        stats["thumbs_up_rate"] = variant_metrics.get("thumbs_up", 0) / conversations
        stats["thumbs_down_rate"] = variant_metrics.get("thumbs_down", 0) / conversations
        
        return stats
    
    def _determine_winner(self, a_stats: Dict, b_stats: Dict) -> Optional[str]:
        """
        Determine which variant is winning.
        
        Criteria (in order of importance):
        1. Average satisfaction (higher is better)
        2. Resolution rate (higher is better)
        3. Escalation rate (lower is better)
        4. Response time (lower is better)
        """
        # Compare satisfaction
        if b_stats["avg_satisfaction"] > a_stats["avg_satisfaction"] + 0.05:  # 5% threshold
            return "variant_b"
        elif a_stats["avg_satisfaction"] > b_stats["avg_satisfaction"] + 0.05:
            return "variant_a"
        
        # Compare resolution rate
        if b_stats["resolution_rate"] > a_stats["resolution_rate"] + 0.1:  # 10% threshold
            return "variant_b"
        elif a_stats["resolution_rate"] > b_stats["resolution_rate"] + 0.1:
            return "variant_a"
        
        # Compare escalation rate (lower is better)
        if b_stats["escalation_rate"] < a_stats["escalation_rate"] - 0.1:
            return "variant_b"
        elif a_stats["escalation_rate"] < b_stats["escalation_rate"] - 0.1:
            return "variant_a"
        
        # Compare response time (lower is better)
        if b_stats["avg_response_time"] < a_stats["avg_response_time"] - 0.5:  # 0.5s threshold
            return "variant_b"
        elif a_stats["avg_response_time"] < b_stats["avg_response_time"] - 0.5:
            return "variant_a"
        
        return None  # Tie or not enough difference
    
    def _calculate_significance(self, variant_a: Dict, variant_b: Dict) -> Dict:
        """
        Calculate statistical significance using simple t-test approximation.
        
        Returns:
            Dict with significance level and confidence
        """
        a_scores = variant_a.get("satisfaction_scores", [])
        b_scores = variant_b.get("satisfaction_scores", [])
        
        if len(a_scores) < 10 or len(b_scores) < 10:
            return {
                "significant": False,
                "confidence": "low",
                "message": "Need at least 10 samples per variant"
            }
        
        # Simple statistical test (t-test approximation)
        a_mean = statistics.mean(a_scores)
        b_mean = statistics.mean(b_scores)
        a_std = statistics.stdev(a_scores) if len(a_scores) > 1 else 0
        b_std = statistics.stdev(b_scores) if len(b_scores) > 1 else 0
        
        # Calculate difference
        diff = abs(b_mean - a_mean)
        pooled_std = ((a_std ** 2 + b_std ** 2) / 2) ** 0.5
        
        # Simple significance test (if difference > 2 standard deviations)
        if pooled_std > 0:
            z_score = diff / pooled_std
            significant = z_score > 1.96  # 95% confidence
        else:
            significant = diff > 0.1  # Fallback threshold
        
        return {
            "significant": significant,
            "confidence": "high" if significant else "medium",
            "difference": diff,
            "message": "Statistically significant" if significant else "Not statistically significant yet"
        }
    
    def _get_recommendation(self, winner: Optional[str], significance: Dict) -> str:
        """Get recommendation based on test results."""
        if not winner:
            return "Continue testing - variants are performing similarly"
        
        if significance.get("significant"):
            return f"Switch to {winner} - statistically significant improvement"
        else:
            return f"{winner} is performing better, but need more data for statistical significance"
    
    def get_all_tests(self) -> Dict:
        """Get all active A/B tests."""
        results = {}
        for agent_name in self.active_tests:
            results[agent_name] = self.get_test_results(agent_name)
        return results


# Singleton instance
_ab_testing: Optional[ABTesting] = None


def get_ab_testing() -> ABTesting:
    """Get singleton instance of ABTesting."""
    global _ab_testing
    if _ab_testing is None:
        _ab_testing = ABTesting()
    return _ab_testing

