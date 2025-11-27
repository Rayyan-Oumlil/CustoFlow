"""
Auto-Improver Scheduler

Automatically applies agent refinements and KB updates on a schedule.
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not available. Install with: pip install apscheduler")

try:
    from utils.agent_improver import AgentImprover
    from utils.kb_updater import KBUpdater
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    AgentImprover = None
    KBUpdater = None

# Import agents dynamically to avoid circular imports
def get_agent_modules():
    """Get agent modules dynamically."""
    try:
        from agents import orchestrator_agent, faq_agent, order_agent, escalation_agent
        return {
            "orchestrator": orchestrator_agent,
            "faq_agent": faq_agent,
            "order_agent": order_agent,
            "escalation_agent": escalation_agent
        }
    except ImportError as e:
        logger.error(f"Error importing agents: {e}")
        return {}


class AutoImprover:
    """
    Automatically applies agent refinements and KB updates.
    """
    
    def __init__(self):
        self.scheduler = None
        self.improver = AgentImprover() if AgentImprover else None
        self.kb_updater = KBUpdater() if KBUpdater else None
        self.agent_modules = get_agent_modules()
    
    def apply_all_refinements(self):
        """Apply all pending refinements for all agents."""
        if not self.improver:
            logger.error("AgentImprover not available")
            return
        
        total_applied = 0
        for agent_name, agent_module in self.agent_modules.items():
            if agent_module:
                try:
                    count = self.improver.auto_apply_refinements(agent_name, agent_module)
                    total_applied += count
                    if count > 0:
                        logger.info(f"Applied {count} refinements to {agent_name}")
                except Exception as e:
                    logger.error(f"Error applying refinements to {agent_name}: {e}")
        
        if total_applied > 0:
            logger.info(f"Total refinements applied: {total_applied}")
        return total_applied
    
    def apply_all_kb_updates(self, limit: int = 10):
        """Apply all pending KB updates."""
        if not self.kb_updater:
            logger.error("KBUpdater not available")
            return 0
        
        try:
            count = self.kb_updater.auto_apply_updates(limit=limit)
            if count > 0:
                logger.info(f"Applied {count} KB updates")
            return count
        except Exception as e:
            logger.error(f"Error applying KB updates: {e}")
            return 0
    
    def run_improvements(self):
        """Run all improvements (refinements only - KB updates require manual approval)."""
        logger.info("Starting automatic improvements...")
        refinements_applied = self.apply_all_refinements()
        # KB updates are NOT applied automatically - they require manual approval
        # kb_updates_applied = self.apply_all_kb_updates(limit=20)
        logger.info(f"Improvements complete: {refinements_applied} refinements applied. KB updates require manual approval.")
        return {
            "refinements_applied": refinements_applied,
            "kb_updates_applied": 0,  # KB updates require manual approval
            "kb_updates_pending": len(self.kb_updater.get_pending_updates()) if self.kb_updater else 0,
            "message": "KB updates require manual approval via API",
            "timestamp": datetime.now().isoformat()
        }
    
    def start_scheduler(self, hour: int = 2, minute: int = 0):
        """
        Start the scheduler to run improvements automatically.
        
        Args:
            hour: Hour of day to run (0-23), default 2 AM
            minute: Minute of hour to run (0-59), default 0
        """
        if not APSCHEDULER_AVAILABLE:
            logger.error("APScheduler not available. Cannot start scheduler.")
            return False
        
        if self.scheduler and self.scheduler.running:
            logger.warning("Scheduler already running")
            return False
        
        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(
                self.run_improvements,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='auto_improve',
                name='Auto-improve agents and KB',
                replace_existing=True
            )
            self.scheduler.start()
            logger.info(f"Scheduler started. Will run improvements daily at {hour:02d}:{minute:02d}")
            return True
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            return False
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
            return True
        return False


# Global instance
_auto_improver: Optional[AutoImprover] = None


def get_auto_improver() -> AutoImprover:
    """Get or create the global AutoImprover instance."""
    global _auto_improver
    if _auto_improver is None:
        _auto_improver = AutoImprover()
    return _auto_improver


def start_auto_improvements(hour: int = 2, minute: int = 0) -> bool:
    """Start automatic improvements scheduler."""
    improver = get_auto_improver()
    return improver.start_scheduler(hour=hour, minute=minute)


def stop_auto_improvements() -> bool:
    """Stop automatic improvements scheduler."""
    improver = get_auto_improver()
    return improver.stop_scheduler()


def run_improvements_now() -> dict:
    """Run improvements immediately (manual trigger)."""
    improver = get_auto_improver()
    return improver.run_improvements()

