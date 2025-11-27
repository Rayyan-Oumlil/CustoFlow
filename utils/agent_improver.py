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
    
    def apply_refinement_to_agent(self, refinement: Dict, agent_module) -> bool:
        """
        Apply a refinement to an agent's instructions.
        
        Args:
            refinement: Refinement data from Supabase
            agent_module: The agent module to update
            
        Returns:
            True if applied successfully
        """
        try:
            changes = refinement.get("changes", {})
            suggested_improvement = changes.get("suggested_improvement", "")
            
            if not suggested_improvement:
                return False
            
            # Get current instructions
            if hasattr(agent_module, 'instructions'):
                current_instructions = agent_module.instructions
                
                # Append improvement suggestion to instructions
                improvement_note = f"\n\n[IMPROVEMENT BASED ON FEEDBACK]: {suggested_improvement}"
                agent_module.instructions = current_instructions + improvement_note
                
                logger.info(f"Applied refinement {refinement.get('refinement_key')} to agent {refinement.get('agent_name')}")
                return True
            else:
                logger.warning(f"Agent module {agent_module} does not have 'instructions' attribute")
                return False
                
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

