"""
Customer Feedback Management System

Comprehensive feedback collection, analysis, and continuous learning system.
Features:
- Feedback collection and storage
- Sentiment analysis on feedback
- Pattern detection and insights
- Automatic knowledge base updates
- Agent instruction refinement
- Feedback aggregation and reporting
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import re

from config.settings import settings

# Try to import Supabase functions
try:
    from utils.supabase_client import (
        SUPABASE_ENABLED,
        save_agent_refinement,
        get_agent_refinements as supabase_get_agent_refinements,
        save_feedback_insight,
        get_feedback_insights as supabase_get_feedback_insights,
        save_kb_update,
        get_kb_updates as supabase_get_kb_updates,
        update_kb_update_status
    )
except ImportError:
    SUPABASE_ENABLED = False


class FeedbackManager:
    """
    Comprehensive feedback management system with analysis and learning capabilities.
    
    Features:
    - Stores detailed feedback with metadata
    - Analyzes feedback sentiment and patterns
    - Generates insights and recommendations
    - Automatically updates knowledge base from feedback
    - Refines agent instructions based on feedback patterns
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize feedback manager.
        
        Args:
            data_dir: Directory for storing feedback data (default: data/)
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.feedback_file = self.data_dir / "feedback.json"
        self.insights_file = self.data_dir / "feedback_insights.json"
        self.kb_updates_file = self.data_dir / "kb_updates_from_feedback.json"
        self.agent_refinements_file = self.data_dir / "agent_refinements.json"
        
        self._feedback: List[Dict] = []
        self._insights: Dict = {}
        self._kb_updates: List[Dict] = []
        self._agent_refinements: Dict = {}
        self._lock = threading.Lock()
        
        # Load existing data
        self._load_data()
    
    def _load_data(self) -> None:
        """Load feedback data from disk."""
        with self._lock:
            # Load feedback
            if self.feedback_file.exists():
                try:
                    with open(self.feedback_file, "r", encoding="utf-8") as f:
                        self._feedback = json.load(f)
                except Exception:
                    self._feedback = []
            
            # Load insights
            if self.insights_file.exists():
                try:
                    with open(self.insights_file, "r", encoding="utf-8") as f:
                        self._insights = json.load(f)
                except Exception:
                    self._insights = {}
            
            # Load KB updates
            if self.kb_updates_file.exists():
                try:
                    with open(self.kb_updates_file, "r", encoding="utf-8") as f:
                        self._kb_updates = json.load(f)
                except Exception:
                    self._kb_updates = []
            
            # Load agent refinements
            if self.agent_refinements_file.exists():
                try:
                    with open(self.agent_refinements_file, "r", encoding="utf-8") as f:
                        self._agent_refinements = json.load(f)
                except Exception:
                    self._agent_refinements = {}
    
    def _save_data(self) -> None:
        """Save feedback data to disk."""
        try:
            with open(self.feedback_file, "w", encoding="utf-8") as f:
                json.dump(self._feedback, f, indent=2, ensure_ascii=False)
            
            with open(self.insights_file, "w", encoding="utf-8") as f:
                json.dump(self._insights, f, indent=2, ensure_ascii=False)
            
            with open(self.kb_updates_file, "w", encoding="utf-8") as f:
                json.dump(self._kb_updates, f, indent=2, ensure_ascii=False)
            
            with open(self.agent_refinements_file, "w", encoding="utf-8") as f:
                json.dump(self._agent_refinements, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Silently fail if save fails
    
    def submit_feedback(
        self,
        session_id: str,
        user_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        reason: Optional[str] = None,
        category: Optional[str] = None,
        conversation_context: Optional[Dict] = None,
        agent_used: Optional[str] = None
    ) -> Dict:
        """
        Submit detailed feedback.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            feedback_type: "thumbs_up", "thumbs_down", "rating", or "survey"
            rating: Numeric rating (1-5) if applicable
            comment: Optional comment text
            reason: Reason for feedback (e.g., "helpful", "incorrect", "unclear")
            category: Feedback category (e.g., "accuracy", "speed", "helpfulness")
            conversation_context: Optional conversation context
            agent_used: Agent that handled the conversation
            
        Returns:
            Dict with feedback submission status
        """
        # Essayer Supabase d'abord
        try:
            from utils.supabase_client import SUPABASE_ENABLED, create_feedback
            if SUPABASE_ENABLED:
                result = create_feedback(
                    session_id=session_id,
                    user_id=user_id,
                    feedback_type=feedback_type,
                    rating=rating,
                    comment=comment,
                    reason=reason,
                    category=category,
                    agent_used=agent_used
                )
                if result.get("status") == "success":
                    feedback_entry = {
                        "id": result.get("feedback_id"),
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id,
                        "user_id": user_id,
                        "feedback_type": feedback_type,
                        "rating": rating,
                        "comment": comment,
                        "reason": reason,
                        "category": category,
                        "conversation_context": conversation_context or {},
                        "agent_used": agent_used,
                        "analyzed": False
                    }
                    # Trigger analysis asynchronously
                    self._analyze_feedback_async(feedback_entry)
                    return {
                        "status": "success",
                        "feedback_id": result.get("feedback_id"),
                        "message": "Feedback recorded successfully"
                    }
        except Exception:
            pass  # Fallback vers JSON
        
        # Fallback vers JSON
        with self._lock:
            feedback_entry = {
                "id": f"feedback_{len(self._feedback) + 1}_{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "user_id": user_id,
                "feedback_type": feedback_type,
                "rating": rating,
                "comment": comment,
                "reason": reason,
                "category": category,
                "conversation_context": conversation_context or {},
                "agent_used": agent_used,
                "analyzed": False
            }
            
            self._feedback.append(feedback_entry)
            self._save_data()
            
            # Trigger analysis asynchronously
            self._analyze_feedback_async(feedback_entry)
            
            return {
                "status": "success",
                "feedback_id": feedback_entry["id"],
                "message": "Feedback recorded successfully"
            }
    
    def _analyze_feedback_async(self, feedback: Dict) -> None:
        """Analyze feedback asynchronously (non-blocking)."""
        import threading
        thread = threading.Thread(target=self._analyze_feedback, args=(feedback,), daemon=True)
        thread.start()
    
    def _analyze_feedback(self, feedback: Dict) -> None:
        """
        Analyze feedback for sentiment, patterns, and insights.
        
        Args:
            feedback: Feedback entry to analyze
        """
        try:
            # Sentiment analysis
            sentiment = self._analyze_sentiment(feedback)
            
            # Pattern detection
            patterns = self._detect_patterns(feedback)
            
            # Update feedback entry
            with self._lock:
                for idx, f in enumerate(self._feedback):
                    if f["id"] == feedback["id"]:
                        self._feedback[idx]["sentiment"] = sentiment
                        self._feedback[idx]["patterns"] = patterns
                        self._feedback[idx]["analyzed"] = True
                        break
                self._save_data()
            
            # Generate insights periodically
            self._generate_insights()
            
            # Check for KB updates
            if feedback.get("feedback_type") in ["thumbs_down", "rating"] and (
                feedback.get("rating", 5) < 3 or feedback.get("reason") in ["incorrect", "missing_info"]
            ):
                self._suggest_kb_update(feedback)
            
            # Check for agent refinements (negative feedback)
            if feedback.get("rating", 5) < 3:
                self._suggest_agent_refinement(feedback)
            
            # Also analyze positive feedback for insights (what works well)
            if feedback.get("feedback_type") == "thumbs_up" or feedback.get("rating", 5) >= 4:
                self._record_positive_feedback_insight(feedback)
                
        except Exception:
            pass  # Silently fail analysis
    
    def _analyze_sentiment(self, feedback: Dict) -> Dict:
        """
        Analyze sentiment of feedback.
        
        Args:
            feedback: Feedback entry
            
        Returns:
            Dict with sentiment analysis
        """
        comment = feedback.get("comment", "").lower()
        rating = feedback.get("rating", 5)
        feedback_type = feedback.get("feedback_type", "")
        reason = feedback.get("reason", "").lower()
        
        # Determine sentiment from multiple signals
        positive_words = ["good", "great", "excellent", "helpful", "accurate", "fast", "satisfied", "thanks", "thank you"]
        negative_words = ["bad", "wrong", "incorrect", "slow", "unhelpful", "confusing", "frustrated", "disappointed"]
        
        positive_score = sum(1 for word in positive_words if word in comment)
        negative_score = sum(1 for word in negative_words if word in comment)
        
        # Rating-based sentiment
        if rating >= 4:
            sentiment_score = 0.7
        elif rating == 3:
            sentiment_score = 0.5
        else:
            sentiment_score = 0.2
        
        # Feedback type sentiment
        if feedback_type == "thumbs_up":
            sentiment_score = max(sentiment_score, 0.8)
        elif feedback_type == "thumbs_down":
            sentiment_score = min(sentiment_score, 0.3)
        
        # Reason-based sentiment
        if reason in ["helpful", "accurate", "fast"]:
            sentiment_score = max(sentiment_score, 0.7)
        elif reason in ["incorrect", "unclear", "slow"]:
            sentiment_score = min(sentiment_score, 0.3)
        
        # Word-based adjustment
        if positive_score > negative_score:
            sentiment_score = min(sentiment_score + 0.1, 1.0)
        elif negative_score > positive_score:
            sentiment_score = max(sentiment_score - 0.1, 0.0)
        
        # Classify sentiment
        if sentiment_score >= 0.7:
            sentiment_label = "positive"
        elif sentiment_score >= 0.4:
            sentiment_label = "neutral"
        else:
            sentiment_label = "negative"
        
        return {
            "label": sentiment_label,
            "score": round(sentiment_score, 2),
            "confidence": 0.8,
            "positive_words": positive_score,
            "negative_words": negative_score
        }
    
    def _detect_patterns(self, feedback: Dict) -> Dict:
        """
        Detect patterns in feedback.
        
        Args:
            feedback: Feedback entry
            
        Returns:
            Dict with detected patterns
        """
        comment = feedback.get("comment", "").lower()
        reason = feedback.get("reason", "").lower()
        category = feedback.get("category", "")
        agent_used = feedback.get("agent_used", "")
        
        patterns = {
            "common_issues": [],
            "topics": [],
            "agent_specific": agent_used if agent_used else None,
            "category_patterns": []
        }
        
        # Detect common issues
        issue_keywords = {
            "accuracy": ["wrong", "incorrect", "inaccurate", "error", "mistake"],
            "speed": ["slow", "fast", "quick", "delay", "waiting"],
            "clarity": ["unclear", "confusing", "vague", "understand", "explain"],
            "completeness": ["missing", "incomplete", "more info", "details"],
            "helpfulness": ["helpful", "useful", "not helpful", "unhelpful"]
        }
        
        for issue, keywords in issue_keywords.items():
            if any(keyword in comment for keyword in keywords):
                patterns["common_issues"].append(issue)
        
        # Detect topics
        topic_keywords = {
            "refund": ["refund", "return", "money back"],
            "shipping": ["shipping", "delivery", "tracking", "ship"],
            "order": ["order", "purchase", "buy"],
            "account": ["account", "login", "password"],
            "product": ["product", "item", "quality"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in comment for keyword in keywords):
                patterns["topics"].append(topic)
        
        # Category patterns
        if category:
            patterns["category_patterns"].append(category)
        
        return patterns
    
    def _generate_insights(self) -> None:
        """Generate insights from all feedback."""
        with self._lock:
            if len(self._feedback) < 5:  # Need minimum feedback for insights
                return
            
            analyzed_feedback = [f for f in self._feedback if f.get("analyzed", False)]
            if len(analyzed_feedback) < 3:
                return
            
            # Calculate metrics
            total_feedback = len(analyzed_feedback)
            positive_count = sum(1 for f in analyzed_feedback if f.get("sentiment", {}).get("label") == "positive")
            negative_count = sum(1 for f in analyzed_feedback if f.get("sentiment", {}).get("label") == "negative")
            
            avg_rating = sum(f.get("rating", 0) for f in analyzed_feedback if f.get("rating")) / max(
                sum(1 for f in analyzed_feedback if f.get("rating")), 1
            )
            
            # Common issues
            all_issues = []
            for f in analyzed_feedback:
                all_issues.extend(f.get("patterns", {}).get("common_issues", []))
            common_issues = defaultdict(int)
            for issue in all_issues:
                common_issues[issue] += 1
            
            # Agent performance
            agent_performance = defaultdict(lambda: {"positive": 0, "negative": 0, "total": 0})
            for f in analyzed_feedback:
                agent = f.get("agent_used", "unknown")
                sentiment = f.get("sentiment", {}).get("label", "neutral")
                agent_performance[agent]["total"] += 1
                if sentiment == "positive":
                    agent_performance[agent]["positive"] += 1
                elif sentiment == "negative":
                    agent_performance[agent]["negative"] += 1
            
            # Topics
            all_topics = []
            for f in analyzed_feedback:
                all_topics.extend(f.get("patterns", {}).get("topics", []))
            topic_frequency = defaultdict(int)
            for topic in all_topics:
                topic_frequency[topic] += 1
            
            self._insights = {
                "generated_at": datetime.now().isoformat(),
                "total_feedback": total_feedback,
                "satisfaction_rate": round((positive_count / total_feedback) * 100, 2) if total_feedback > 0 else 0,
                "avg_rating": round(avg_rating, 2),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "common_issues": dict(sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:5]),
                "agent_performance": {
                    agent: {
                        "total": stats["total"],
                        "positive_rate": round((stats["positive"] / max(stats["total"], 1)) * 100, 2),
                        "negative_rate": round((stats["negative"] / max(stats["total"], 1)) * 100, 2)
                    }
                    for agent, stats in agent_performance.items()
                },
                "top_topics": dict(sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)[:5]),
                "trends": self._calculate_trends(analyzed_feedback)
            }
            
            # Try Supabase first
            if SUPABASE_ENABLED:
                try:
                    insight_key = f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    save_feedback_insight(
                        insight_key=insight_key,
                        insight_type="aggregated",
                        insight_data=self._insights
                    )
                except Exception as e:
                    print(f"Error saving feedback insight to Supabase: {e}")
                    # Fallback to JSON
                    self._save_data()
            else:
                self._save_data()
    
    def _calculate_trends(self, feedback: List[Dict]) -> Dict:
        """Calculate trends over time."""
        if len(feedback) < 2:
            return {}
        
        # Group by date
        daily_feedback = defaultdict(list)
        for f in feedback:
            try:
                date = datetime.fromisoformat(f["timestamp"]).date()
                daily_feedback[date.isoformat()].append(f)
            except Exception:
                pass
        
        if len(daily_feedback) < 2:
            return {}
        
        # Calculate daily averages
        daily_ratings = {}
        for date, feedbacks in daily_feedback.items():
            ratings = [f.get("rating") for f in feedbacks if f.get("rating")]
            if ratings:
                daily_ratings[date] = sum(ratings) / len(ratings)
        
        if len(daily_ratings) < 2:
            return {}
        
        # Calculate trend
        sorted_dates = sorted(daily_ratings.keys())
        recent_avg = sum(daily_ratings[d] for d in sorted_dates[-3:]) / min(3, len(sorted_dates))
        older_avg = sum(daily_ratings[d] for d in sorted_dates[:-3]) / max(1, len(sorted_dates) - 3) if len(sorted_dates) > 3 else recent_avg
        
        trend_direction = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
        
        return {
            "direction": trend_direction,
            "recent_avg": round(recent_avg, 2),
            "older_avg": round(older_avg, 2),
            "change": round(recent_avg - older_avg, 2)
        }
    
    def _suggest_kb_update(self, feedback: Dict) -> None:
        """
        Suggest knowledge base update from negative feedback.
        
        Args:
            feedback: Feedback entry
        """
        comment = feedback.get("comment", "")
        reason = feedback.get("reason", "")
        conversation_context = feedback.get("conversation_context", {})
        
        # Extract potential FAQ from feedback
        if comment and len(comment) > 10:
            kb_suggestion = {
                "id": f"kb_suggestion_{len(self._kb_updates) + 1}_{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().isoformat(),
                "source_feedback_id": feedback["id"],
                "suggestion_type": "add" if reason == "missing_info" else "update",
                "reason": reason,
                "customer_comment": comment,
                "conversation_context": conversation_context,
                "status": "pending",
                "priority": "high" if feedback.get("rating", 5) == 1 else "medium"
            }
            
            with self._lock:
                # Try Supabase first
                if SUPABASE_ENABLED:
                    try:
                        save_kb_update(
                            update_id=kb_suggestion["id"],
                            feedback_id=kb_suggestion.get("source_feedback_id"),
                            update_type=kb_suggestion["suggestion_type"],
                            content={
                                "reason": kb_suggestion.get("reason"),
                                "customer_comment": kb_suggestion.get("customer_comment"),
                                "conversation_context": kb_suggestion.get("conversation_context", {}),
                                "priority": kb_suggestion.get("priority", "medium")
                            },
                            status=kb_suggestion["status"]
                        )
                    except Exception as e:
                        print(f"Error saving KB update to Supabase: {e}")
                        # Fallback to JSON
                        self._kb_updates.append(kb_suggestion)
                        self._save_data()
                else:
                    # Fallback to JSON
                    self._kb_updates.append(kb_suggestion)
                    self._save_data()
    
    def _suggest_agent_refinement(self, feedback: Dict) -> None:
        """
        Suggest agent instruction refinement from feedback.
        
        Args:
            feedback: Feedback entry
        """
        agent_used = feedback.get("agent_used", "unknown")
        comment = feedback.get("comment", "")
        reason = feedback.get("reason", "")
        rating = feedback.get("rating", 5)
        
        if agent_used == "unknown":
            return
        
        if agent_used not in self._agent_refinements:
            self._agent_refinements[agent_used] = {
                "refinements": [],
                "last_updated": None
            }
        
        refinement = {
            "id": f"refinement_{len(self._agent_refinements[agent_used]['refinements']) + 1}",
            "timestamp": datetime.now().isoformat(),
            "source_feedback_id": feedback["id"],
            "issue": reason or "low_rating",
            "customer_feedback": comment,
            "rating": rating,
            "suggested_improvement": self._generate_improvement_suggestion(agent_used, reason, comment),
            "status": "pending"
        }
        
        with self._lock:
            # Try Supabase first
            if SUPABASE_ENABLED:
                try:
                    refinement_key = f"{agent_used}_{refinement['id']}"
                    save_agent_refinement(
                        refinement_key=refinement_key,
                        agent_name=agent_used,
                        refinement_type=refinement["issue"],
                        changes={
                            "suggested_improvement": refinement["suggested_improvement"],
                            "customer_feedback": refinement["customer_feedback"],
                            "rating": refinement["rating"]
                        },
                        feedback_sources=[refinement["source_feedback_id"]],
                        status=refinement["status"]
                    )
                except Exception as e:
                    print(f"Error saving agent refinement to Supabase: {e}")
                    # Fallback to JSON
                    if agent_used not in self._agent_refinements:
                        self._agent_refinements[agent_used] = {
                            "refinements": [],
                            "last_updated": None
                        }
                    self._agent_refinements[agent_used]["refinements"].append(refinement)
                    self._agent_refinements[agent_used]["last_updated"] = datetime.now().isoformat()
                    self._save_data()
            else:
                # Fallback to JSON
                if agent_used not in self._agent_refinements:
                    self._agent_refinements[agent_used] = {
                        "refinements": [],
                        "last_updated": None
                    }
                self._agent_refinements[agent_used]["refinements"].append(refinement)
                self._agent_refinements[agent_used]["last_updated"] = datetime.now().isoformat()
                self._save_data()
    
    def _record_positive_feedback_insight(self, feedback: Dict) -> None:
        """
        Record positive feedback as an insight (what works well).
        
        Args:
            feedback: Feedback entry with thumbs_up or high rating
        """
        agent_used = feedback.get("agent_used", "unknown")
        comment = feedback.get("comment", "")
        
        if agent_used == "unknown":
            return
        
        # Save positive feedback insight to Supabase
        if SUPABASE_ENABLED:
            try:
                from utils.supabase_client import save_feedback_insight
                import uuid
                insight_key = f"POSITIVE-{uuid.uuid4().hex[:8].upper()}"
                
                # Analyze sentiment for positive feedback
                sentiment = self._analyze_sentiment(feedback)
                
                save_feedback_insight(
                    insight_key=insight_key,
                    agent_name=agent_used,
                    insight_type="positive_feedback",
                    description=f"Positive feedback for {agent_used}: {comment[:100] if comment else 'No comment'}",
                    sentiment=sentiment,
                    feedback_sources=[feedback.get("id")] if feedback.get("id") else [],
                    insight_data={
                        "feedback_id": feedback.get("id"),
                        "comment": comment,
                        "rating": feedback.get("rating", 5),
                        "feedback_type": feedback.get("feedback_type", "thumbs_up")
                    },
                    summary=f"Positive feedback for {agent_used}: {comment[:100] if comment else 'No comment'}"
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error saving positive feedback insight: {e}")
                import traceback
                traceback.print_exc()
    
    def _generate_improvement_suggestion(self, agent: str, reason: str, comment: str) -> str:
        """Generate improvement suggestion based on feedback."""
        suggestions = {
            "incorrect": "Review and verify the accuracy of responses. Double-check facts before providing answers.",
            "unclear": "Improve clarity and use simpler language. Break down complex explanations into smaller parts.",
            "slow": "Optimize response time. Consider caching common responses.",
            "missing_info": "Provide more comprehensive answers. Include relevant details and context.",
            "unhelpful": "Focus on being more helpful and proactive. Anticipate follow-up questions."
        }
        
        return suggestions.get(reason, "Review feedback and improve response quality.")
    
    def get_feedback_stats(self) -> Dict:
        """
        Get comprehensive feedback statistics.
        
        Returns:
            Dict with feedback statistics
        """
        with self._lock:
            total = len(self._feedback)
            if total == 0:
                return {
                    "total_feedback": 0,
                    "insights": self._insights,
                    "kb_suggestions": len(self._kb_updates),
                    "agent_refinements": sum(len(r["refinements"]) for r in self._agent_refinements.values())
                }
            
            analyzed = [f for f in self._feedback if f.get("analyzed", False)]
            ratings = [f.get("rating") for f in self._feedback if f.get("rating")]
            
            feedback_by_type = defaultdict(int)
            for f in self._feedback:
                feedback_by_type[f.get("feedback_type", "unknown")] += 1
            
            return {
                "total_feedback": total,
                "analyzed_feedback": len(analyzed),
                "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
                "feedback_by_type": dict(feedback_by_type),
                "insights": self._insights,
                "kb_suggestions": len(self._kb_updates),
                "pending_kb_updates": len([u for u in self._kb_updates if u.get("status") == "pending"]),
                "agent_refinements": sum(len(r["refinements"]) for r in self._agent_refinements.values()),
                "pending_refinements": sum(
                    len([r for r in r_data["refinements"] if r.get("status") == "pending"])
                    for r_data in self._agent_refinements.values()
                )
            }
    
    def get_feedback_list(self, limit: Optional[int] = None, agent: Optional[str] = None) -> List[Dict]:
        """
        Get list of feedback entries.
        
        Args:
            limit: Maximum number of entries to return
            agent: Filter by agent
            
        Returns:
            List of feedback entries
        """
        with self._lock:
            feedback = self._feedback.copy()
            
            if agent:
                feedback = [f for f in feedback if f.get("agent_used") == agent]
            
            feedback.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            if limit:
                feedback = feedback[:limit]
            
            return feedback
    
    def get_kb_suggestions(self, status: Optional[str] = None) -> List[Dict]:
        """
        Get knowledge base update suggestions.
        
        Args:
            status: Filter by status ("pending", "applied", "rejected")
            
        Returns:
            List of KB suggestions
        """
        with self._lock:
            suggestions = self._kb_updates.copy()
            
            if status:
                suggestions = [s for s in suggestions if s.get("status") == status]
            
            suggestions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return suggestions
    
    def get_agent_refinements(self, agent: Optional[str] = None) -> Dict:
        """
        Get agent instruction refinements.
        
        Args:
            agent: Filter by specific agent
            
        Returns:
            Dict with agent refinements
        """
        # Try Supabase first
        if SUPABASE_ENABLED:
            try:
                supabase_refinements = supabase_get_agent_refinements(agent_name=agent, status="pending")
                # Convert Supabase format to expected format
                result = {}
                for r in supabase_refinements:
                    agent_name = r.get("agent_name")
                    if agent_name not in result:
                        result[agent_name] = {
                            "refinements": [],
                            "last_updated": r.get("updated_at")
                        }
                    
                    changes = r.get("changes", {})
                    result[agent_name]["refinements"].append({
                        "id": r.get("refinement_key"),
                        "timestamp": r.get("created_at", ""),
                        "source_feedback_id": r.get("feedback_sources", [""])[0] if r.get("feedback_sources") else "",
                        "issue": r.get("refinement_type"),
                        "customer_feedback": changes.get("customer_feedback", ""),
                        "rating": changes.get("rating", 5),
                        "suggested_improvement": changes.get("suggested_improvement", ""),
                        "status": r.get("status")
                    })
                
                if agent:
                    return result.get(agent, {"refinements": [], "last_updated": None})
                return result
            except Exception as e:
                print(f"Error getting agent refinements from Supabase: {e}")
                # Fallback to JSON
                pass
        
        # Fallback to JSON
        with self._lock:
            if agent:
                return self._agent_refinements.get(agent, {"refinements": [], "last_updated": None})
            return self._agent_refinements.copy()
    
    def apply_kb_update(self, suggestion_id: str) -> Dict:
        """
        Apply a knowledge base update suggestion.
        
        This integrates with the knowledge base manager to actually update the FAQ.
        
        Args:
            suggestion_id: ID of the suggestion to apply
            
        Returns:
            Dict with application status
        """
        with self._lock:
            suggestion = None
            for s in self._kb_updates:
                if s["id"] == suggestion_id:
                    suggestion = s
                    break
            
            if not suggestion:
                return {"status": "error", "message": "Suggestion not found"}
            
            if suggestion.get("status") == "applied":
                return {"status": "success", "message": "KB update already applied"}
            
            # Try to integrate with knowledge base manager
            try:
                # Import here to avoid circular dependencies
                from tools.knowledge_base_manager import get_kb_manager
                from tools.faq_tool import _load_faq_data
                
                kb_manager = get_kb_manager()
                if kb_manager:
                    # Load current FAQs
                    current_faqs = _load_faq_data()
                    
                    # Extract FAQ information from suggestion
                    customer_comment = suggestion.get("customer_comment", "")
                    conversation_context = suggestion.get("conversation_context", {})
                    
                    # Try to extract question and answer from context
                    # This is a simple extraction - in production, you'd use LLM to generate proper FAQ
                    if customer_comment and len(customer_comment) > 20:
                        # Create a new FAQ entry based on feedback
                        new_faq = {
                            "id": f"faq_feedback_{int(datetime.now().timestamp())}",
                            "question": self._extract_question_from_feedback(suggestion),
                            "answer": self._generate_answer_from_feedback(suggestion),
                            "category": self._extract_category_from_feedback(suggestion),
                            "tags": ["feedback_generated", "auto_added"],
                            "created_at": datetime.now().isoformat(),
                            "source": "customer_feedback",
                            "feedback_id": suggestion.get("source_feedback_id")
                        }
                        
                        # Add to current FAQs
                        current_faqs.append(new_faq)
                        
                        # Create new version with updated FAQs
                        version_id = kb_manager.create_version(
                            faqs=current_faqs,
                            version_name=f"feedback_update_{suggestion_id}",
                            description=f"KB update from feedback: {customer_comment[:100]}",
                            tags=["feedback", "auto_update"]
                        )
                        
                        # Activate the new version
                        kb_manager.activate_version(version_id)
                        
                        suggestion["status"] = "applied"
                        suggestion["applied_at"] = datetime.now().isoformat()
                        suggestion["version_id"] = version_id
                        suggestion["new_faq_id"] = new_faq["id"]
                        self._save_data()
                        
                        return {
                            "status": "success",
                            "message": "KB update applied successfully",
                            "version_id": version_id,
                            "new_faq_id": new_faq["id"]
                        }
                    else:
                        # Mark as applied even if we can't extract FAQ
                        suggestion["status"] = "applied"
                        suggestion["applied_at"] = datetime.now().isoformat()
                        suggestion["note"] = "Applied but no FAQ extracted (insufficient data)"
                        self._save_data()
                        return {"status": "success", "message": "KB update marked as applied"}
                else:
                    # KB manager not available, just mark as applied
                    suggestion["status"] = "applied"
                    suggestion["applied_at"] = datetime.now().isoformat()
                    self._save_data()
                    return {"status": "success", "message": "KB update marked as applied (KB manager not available)"}
            except Exception as e:
                # Mark as applied with error note
                suggestion["status"] = "applied"
                suggestion["applied_at"] = datetime.now().isoformat()
                suggestion["error"] = str(e)
                self._save_data()
                return {"status": "partial", "message": f"KB update applied with errors: {str(e)}"}
    
    def _extract_question_from_feedback(self, suggestion: Dict) -> str:
        """Extract question from feedback suggestion."""
        comment = suggestion.get("customer_comment", "")
        context = suggestion.get("conversation_context", {})
        last_messages = context.get("last_messages", [])
        
        # Try to find the user's question from conversation context
        for msg in reversed(last_messages):
            if msg.get("role") == "user":
                return msg.get("content", "")[:200]
        
        # Fallback: generate question from comment
        if comment:
            # Simple extraction - in production, use LLM
            if "?" in comment:
                return comment.split("?")[0] + "?"
            return f"Question about: {comment[:100]}"
        
        return "Customer question (extracted from feedback)"
    
    def _generate_answer_from_feedback(self, suggestion: Dict) -> str:
        """Generate answer from feedback suggestion."""
        comment = suggestion.get("customer_comment", "")
        reason = suggestion.get("reason", "")
        
        # In production, this would use LLM to generate a proper answer
        # For now, create a placeholder
        if reason == "missing_info":
            return f"Based on customer feedback, additional information is needed. {comment[:200] if comment else 'Please provide more details.'}"
        elif reason == "incorrect":
            return f"Previous answer was incorrect. Corrected information: {comment[:200] if comment else 'Please verify the information.'}"
        else:
            return f"Information based on customer feedback: {comment[:200] if comment else 'Please review and update.'}"
    
    def _extract_category_from_feedback(self, suggestion: Dict) -> str:
        """Extract category from feedback."""
        comment = suggestion.get("customer_comment", "").lower()
        context = suggestion.get("conversation_context", {})
        
        # Simple category detection
        if any(word in comment for word in ["refund", "return", "money"]):
            return "Refunds & Returns"
        elif any(word in comment for word in ["shipping", "delivery", "tracking"]):
            return "Shipping & Delivery"
        elif any(word in comment for word in ["order", "purchase"]):
            return "Orders"
        elif any(word in comment for word in ["account", "login", "password"]):
            return "Account"
        else:
            return "General"


# Global feedback manager instance
feedback_manager = FeedbackManager()

