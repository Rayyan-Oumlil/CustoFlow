"""
Knowledge Base Auto-Updater

Automatically applies KB updates from feedback to the FAQ knowledge base.
"""
from typing import Dict, List, Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    from utils.supabase_client import (
        SUPABASE_ENABLED,
        get_kb_updates,
        update_kb_update_status
    )
except ImportError:
    SUPABASE_ENABLED = False


class KBUpdater:
    """
    System that automatically updates the knowledge base from feedback.
    """
    
    def __init__(self, kb_file: Optional[Path] = None):
        if kb_file is None:
            kb_file = Path(__file__).parent.parent / "data" / "faq_knowledge_base.json"
        self.kb_file = kb_file
    
    def get_pending_updates(self) -> List[Dict]:
        """
        Get pending KB update suggestions.
        
        Returns:
            List of pending KB updates
        """
        if not SUPABASE_ENABLED:
            return []
        
        try:
            updates = get_kb_updates(status="pending")
            return updates
        except Exception as e:
            logger.error(f"Error getting pending KB updates: {e}")
            return []
    
    def apply_kb_update(self, update: Dict) -> bool:
        """
        Apply a KB update to the knowledge base.
        
        Args:
            update: KB update data from Supabase
            
        Returns:
            True if applied successfully
        """
        try:
            # Load current KB
            if not self.kb_file.exists():
                logger.error(f"KB file not found: {self.kb_file}")
                return False
            
            with open(self.kb_file, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
            
            content = update.get("content", {})
            update_type = update.get("update_type", "add")
            customer_comment = content.get("customer_comment", "")
            reason = content.get("reason", "")
            
            # Create new FAQ entry from feedback
            if update_type == "add" and customer_comment:
                new_faq = {
                    "id": f"faq_{len(kb_data.get('faqs', [])) + 1}",
                    "question": self._extract_question(customer_comment),
                    "answer": self._generate_answer(customer_comment, reason),
                    "category": "General",
                    "tags": ["feedback", "auto-generated"],
                    "source": "feedback",
                    "created_from_feedback": True
                }
                
                # Add to KB
                if "faqs" not in kb_data:
                    kb_data["faqs"] = []
                kb_data["faqs"].append(new_faq)
                
                # Save KB
                with open(self.kb_file, "w", encoding="utf-8") as f:
                    json.dump(kb_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Applied KB update {update.get('update_id')}: Added new FAQ")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying KB update: {e}")
            return False
    
    def _extract_question(self, comment: str) -> str:
        """Extract a question from customer comment."""
        # Simple extraction - take first sentence or first 100 chars
        sentences = comment.split('.')
        if sentences:
            question = sentences[0].strip()
            if len(question) > 100:
                question = question[:100] + "..."
            return question
        return comment[:100] if len(comment) > 100 else comment
    
    def _generate_answer(self, comment: str, reason: str) -> str:
        """Generate an answer based on customer comment and reason."""
        # This is a simple implementation - in production, you'd use AI to generate better answers
        base_answer = "Based on customer feedback, we understand this is an important topic. "
        
        if reason == "missing_info":
            base_answer += "Here is the information you need: "
        elif reason == "incorrect":
            base_answer += "Here is the correct information: "
        else:
            base_answer += "Here is helpful information: "
        
        # Use part of the comment as context
        if comment:
            base_answer += comment[:200] + "..."
        
        return base_answer
    
    def auto_apply_updates(self, limit: int = 10) -> int:
        """
        Automatically apply pending KB updates.
        
        Args:
            limit: Maximum number of updates to apply
            
        Returns:
            Number of updates applied
        """
        if not SUPABASE_ENABLED:
            return 0
        
        updates = self.get_pending_updates()[:limit]
        applied_count = 0
        
        for update in updates:
            if self.apply_kb_update(update):
                # Mark as applied
                update_id = update.get("update_id")
                if update_id:
                    update_kb_update_status(update_id, "applied")
                    applied_count += 1
        
        if applied_count > 0:
            logger.info(f"Applied {applied_count} KB updates")
        
        return applied_count

