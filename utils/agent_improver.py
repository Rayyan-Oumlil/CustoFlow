"""
Agent Improvement System

Automatically applies refinements to agents based on feedback.
This system reads agent_refinements from Supabase and applies them to agent instructions.
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from utils.supabase_client import (
        SUPABASE_ENABLED,
        get_agent_refinements,
        update_agent_refinement_status
    )
    from utils.feedback_manager import FeedbackManager
except ImportError:
    SUPABASE_ENABLED = False


class AgentImprover:
    """
    System that automatically improves agents based on feedback refinements.
    """
    
    def __init__(self):
        self.feedback_manager = FeedbackManager() if SUPABASE_ENABLED else None
    
    def get_pending_refinements(self, agent_name: Optional[str] = None) -> List[Dict]:
        """
        Get pending refinements for agents.
        
        Args:
            agent_name: Optional agent name to filter
            
        Returns:
            List of pending refinements
        """
        if not SUPABASE_ENABLED:
            return []
        
        try:
            refinements = get_agent_refinements(agent_name=agent_name, status="pending")
            return refinements
        except Exception as e:
            logger.error(f"Error getting pending refinements: {e}")
            return []
    
    def get_active_refinements_for_agent(self, agent_name: str, minimal: bool = True) -> str:
        """
        Get all active refinements for an agent and format them MINIMALLY.
        
        Args:
            agent_name: Name of the agent
            minimal: If True, return very short format (default: True)
            
        Returns:
            Minimal formatted string with refinements (empty if none)
        """
        if not SUPABASE_ENABLED:
            return ""
        
        try:
            # Get all applied refinements (status="applied" or "active")
            refinements = get_agent_refinements(agent_name=agent_name, status="applied")
            if not refinements:
                # Also check for "active" status
                all_refinements = get_agent_refinements(agent_name=agent_name)
                refinements = [r for r in all_refinements if r.get("status") in ["applied", "active"]]
            
            if not refinements:
                return ""
            
            if minimal:
                # MINIMAL format: just the key improvements, very short
                improvements = []
                for ref in refinements[:3]:  # Only 3 most recent
                    changes = ref.get("changes", {})
                    suggested = changes.get("suggested_improvement", "")
                    if suggested:
                        # Extract key phrase (first sentence or 50 chars max)
                        key_phrase = suggested.split('.')[0][:50]
                        improvements.append(key_phrase)
                
                if improvements:
                    # Ultra-minimal: just a short note
                    return f"\n[Note: {', '.join(improvements[:2])}]"
                return ""
            else:
                # Full format (for manual injection if needed)
                improvements = []
                for ref in refinements[:5]:
                    changes = ref.get("changes", {})
                    suggested = changes.get("suggested_improvement", "")
                    if suggested:
                        improvements.append(suggested)
                
                if improvements:
                    return "\n\n" + "IMPROVEMENTS:\n" + "\n".join(improvements)
                return ""
            
        except Exception as e:
            logger.error(f"Error getting active refinements: {e}")
            return ""
    
    def apply_refinement_to_agent(self, refinement: Dict, agent_module) -> bool:
        """
        Mark a refinement as applied (status update only, no code modification).
        
        WARNING: This does NOT modify the agent code. Refinements are injected dynamically
        via get_active_refinements_for_agent() at runtime.
        
        Args:
            refinement: Refinement data from Supabase
            agent_module: The agent module (not used, kept for compatibility)
            
        Returns:
            True if status updated successfully
        """
        try:
            refinement_key = refinement.get("refinement_key")
            if not refinement_key:
                return False
            
            # Mark as applied in database (safe - just status update)
            update_agent_refinement_status(refinement_key, "applied")
            
            logger.info(f"Marked refinement {refinement_key} as applied for agent {refinement.get('agent_name')}")
            logger.info("NOTE: Refinements are injected dynamically at runtime, not by modifying agent code.")
            return True
                
        except Exception as e:
            logger.error(f"Error applying refinement: {e}")
            return False
    
    def auto_apply_refinements(self, agent_name: str, agent_module) -> int:
        """
        Automatically apply all pending refinements for an agent.
        
        Args:
            agent_name: Name of the agent
            agent_module: The agent module to update
            
        Returns:
            Number of refinements applied
        """
        if not SUPABASE_ENABLED:
            return 0
        
        refinements = self.get_pending_refinements(agent_name=agent_name)
        applied_count = 0
        
        for refinement in refinements:
            if self.apply_refinement_to_agent(refinement, agent_module):
                # Mark as applied
                refinement_key = refinement.get("refinement_key")
                if refinement_key:
                    update_agent_refinement_status(refinement_key, "applied")
                    applied_count += 1
        
        if applied_count > 0:
            logger.info(f"Applied {applied_count} refinements to agent {agent_name}")
        
        return applied_count
    
    def get_improvement_summary(self, agent_name: str) -> Dict:
        """
        Get a summary of improvements for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dict with improvement summary
        """
        if not SUPABASE_ENABLED:
            return {}
        
        try:
            all_refinements = get_agent_refinements(agent_name=agent_name)
            
            pending = [r for r in all_refinements if r.get("status") == "pending"]
            applied = [r for r in all_refinements if r.get("status") == "applied"]
            rejected = [r for r in all_refinements if r.get("status") == "rejected"]
            
            return {
                "agent_name": agent_name,
                "total_refinements": len(all_refinements),
                "pending": len(pending),
                "applied": len(applied),
                "rejected": len(rejected),
                "latest_refinements": all_refinements[:5]  # Last 5
            }
        except Exception as e:
            logger.error(f"Error getting improvement summary: {e}")
            return {}

