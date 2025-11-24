"""
Conversation Summarization Module

Automatically generates conversation summaries for human agents when escalation occurs.
This saves time and improves handoff quality by providing key context.

Features:
- Auto-generate summaries after each conversation or when tickets are created
- Key points extraction (customer issue, attempted solutions, current status)
- Sentiment summary
- Action items and next steps
- Configurable summary length
- Export summaries for training/analysis

Technical Implementation:
- Uses LLM summarization (Gemini)
- Template-based summaries
- Configurable summary length
- Stores summaries in conversation history and ticket metadata
"""
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from google.genai import types
from google.genai import Client

from config.settings import settings
from memory.conversation_history import conversation_history

# Set API key for Gemini
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Summary storage file
SUMMARY_FILE = Path(__file__).parent.parent / "data" / "conversation_summaries.json"


def _load_summaries() -> Dict[str, Dict]:
    """Load conversation summaries from file."""
    if SUMMARY_FILE.exists():
        try:
            with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_summaries(summaries: Dict[str, Dict]) -> None:
    """Save conversation summaries to file."""
    try:
        SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # Silently fail if save fails


class ConversationSummarizer:
    """
    Generates intelligent conversation summaries for ticket handoffs.
    
    Uses LLM to extract key information, sentiment, and action items
    from conversation history to help human agents quickly understand context.
    """
    
    def __init__(self):
        """Initialize the summarizer."""
        self._summaries: Dict[str, Dict] = _load_summaries()
        # Initialize Gemini client
        self.client = Client(api_key=settings.google_api_key)
    
    def generate_summary(
        self,
        user_id: str,
        session_id: str,
        summary_length: str = "medium",
        include_sentiment: bool = True,
        ticket_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive conversation summary.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            summary_length: "short", "medium", or "long"
            include_sentiment: Whether to include sentiment analysis
            ticket_id: Optional ticket ID if summary is for a ticket
            
        Returns:
            Dictionary with summary information:
            {
                "summary": "...",
                "key_points": {...},
                "sentiment": {...},
                "action_items": [...],
                "next_steps": [...],
                "timestamp": "...",
                "ticket_id": "..."
            }
        """
        try:
            # Get conversation history for this session
            history = conversation_history.get_history(
                user_id=user_id,
                session_id=session_id
            )
            
            if not history:
                return {
                    "status": "error",
                    "error_message": "No conversation history found for this session"
                }
            
            # Format conversation for summarization
            conversation_text = self._format_conversation(history)
            
            # Generate sentiment analysis if requested
            sentiment_info = None
            if include_sentiment:
                sentiment_info = self._analyze_sentiment(conversation_text)
            
            # Generate summary using LLM
            summary_prompt = self._build_summary_prompt(
                conversation_text,
                summary_length,
                sentiment_info,
                ticket_id
            )
            
            # Generate summary using Gemini
            # Use generate_content directly on the models object
            # The API expects: models.generate_content(model=..., contents=..., config=...)
            try:
                response = self.client.models.generate_content(
                    model=settings.model_name,
                    contents=[types.Part(text=summary_prompt)],
                    config=types.GenerateContentConfig(
                        temperature=0.3,  # Lower temperature for more consistent summaries
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=self._get_max_tokens(summary_length)
                    )
                )
            except AttributeError:
                # Fallback: try using the model name directly
                # Some versions of the API might use a different syntax
                model = getattr(self.client.models, settings.model_name.replace("-", "_"), None)
                if model:
                    response = model.generate_content(
                        contents=[types.Part(text=summary_prompt)],
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                            top_p=0.8,
                            top_k=40,
                            max_output_tokens=self._get_max_tokens(summary_length)
                        )
                    )
                else:
                    raise ValueError(f"Unable to access model {settings.model_name}. API may have changed.")
            
            # Extract text from response
            if hasattr(response, 'text'):
                summary_text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                if hasattr(response.candidates[0], 'content'):
                    summary_text = response.candidates[0].content.parts[0].text.strip()
                else:
                    summary_text = str(response.candidates[0]).strip()
            else:
                summary_text = str(response).strip()
            
            # Parse structured summary
            structured_summary = self._parse_summary(summary_text, sentiment_info, ticket_id)
            
            # Store summary
            summary_key = f"{user_id}_{session_id}"
            if ticket_id:
                summary_key = f"{summary_key}_{ticket_id}"
            
            # Essayer Supabase d'abord
            try:
                from utils.supabase_client import SUPABASE_ENABLED, save_conversation_summary
                if SUPABASE_ENABLED:
                    save_conversation_summary(
                        summary_key=summary_key,
                        user_id=user_id,
                        session_id=session_id,
                        summary=structured_summary.get("summary", ""),
                        key_points=structured_summary.get("key_points", {}),
                        sentiment=structured_summary.get("sentiment", {}),
                        action_items=structured_summary.get("action_items", []),
                        next_steps=structured_summary.get("next_steps", []),
                        summary_length=summary_length,
                        ticket_id=ticket_id
                    )
                else:
                    # Fallback vers JSON
                    self._summaries[summary_key] = structured_summary
                    _save_summaries(self._summaries)
            except Exception:
                # Fallback vers JSON si Supabase échoue
                self._summaries[summary_key] = structured_summary
                _save_summaries(self._summaries)
            
            return {
                "status": "success",
                **structured_summary
            }
            
        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n{traceback.format_exc()}"
            return {
                "status": "error",
                "error_message": f"Error generating summary: {str(e)}",
                "error_details": error_details
            }
    
    def _format_conversation(self, history: List[Dict]) -> str:
        """Format conversation history into text for summarization."""
        formatted = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "user":
                formatted.append(f"Customer ({timestamp}): {content}")
            elif role == "assistant":
                formatted.append(f"Agent ({timestamp}): {content}")
        
        return "\n".join(formatted)
    
    def _analyze_sentiment(self, conversation_text: str) -> Optional[Dict]:
        """Analyze sentiment of the conversation using simple keyword-based detection."""
        try:
            # Simple sentiment detection based on keywords
            text_lower = conversation_text.lower()
            
            # Negative indicators
            negative_words = ["frustrated", "angry", "upset", "disappointed", "terrible", 
                            "awful", "horrible", "hate", "worst", "problem", "issue", "broken"]
            # Positive indicators
            positive_words = ["happy", "great", "thank", "appreciate", "excellent", 
                            "wonderful", "amazing", "love", "best", "perfect", "satisfied"]
            
            negative_count = sum(1 for word in negative_words if word in text_lower)
            positive_count = sum(1 for word in positive_words if word in text_lower)
            
            # Determine sentiment
            if negative_count > positive_count and negative_count > 0:
                return {
                    "sentiment": "negative",
                    "emotion": "frustrated" if "frustrated" in text_lower else "upset",
                    "urgency": "high" if negative_count > 2 else "medium",
                    "escalation_recommended": negative_count > 1
                }
            elif positive_count > negative_count and positive_count > 0:
                return {
                    "sentiment": "positive",
                    "emotion": "satisfied",
                    "urgency": "low",
                    "escalation_recommended": False
                }
            else:
                return {
                    "sentiment": "neutral",
                    "emotion": "neutral",
                    "urgency": "medium",
                    "escalation_recommended": False
                }
        except Exception:
            return None
    
    def _build_summary_prompt(
        self,
        conversation_text: str,
        summary_length: str,
        sentiment_info: Optional[Dict],
        ticket_id: Optional[str]
    ) -> str:
        """Build the prompt for LLM summarization."""
        
        length_instructions = {
            "short": "2-3 sentences",
            "medium": "1 paragraph (4-6 sentences)",
            "long": "2-3 paragraphs (8-12 sentences)"
        }
        
        length_desc = length_instructions.get(summary_length, "1 paragraph")
        
        prompt = f"""You are a customer support specialist creating a conversation summary for a human agent handoff.

Conversation History:
{conversation_text}

"""
        
        if ticket_id:
            prompt += f"Ticket ID: {ticket_id}\n\n"
        
        if sentiment_info:
            prompt += f"Sentiment Analysis: {json.dumps(sentiment_info, indent=2)}\n\n"
        
        prompt += f"""Please create a comprehensive summary ({length_desc}) that includes:

1. **Customer Issue**: What is the main problem or question the customer has?
2. **Attempted Solutions**: What solutions or information were provided by the agent?
3. **Current Status**: What is the current state of the issue? Is it resolved, pending, or escalated?
4. **Key Details**: Important information like order IDs, dates, amounts, etc.
5. **Sentiment Summary**: Brief summary of customer sentiment and emotion
6. **Action Items**: What needs to be done next? (list 2-4 items)
7. **Next Steps**: Recommended next steps for the human agent

Format your response as a structured summary with clear sections. Be concise but comprehensive.

Summary:"""
        
        return prompt
    
    def _get_max_tokens(self, summary_length: str) -> int:
        """Get max output tokens based on summary length."""
        return {
            "short": 200,
            "medium": 500,
            "long": 1000
        }.get(summary_length, 500)
    
    def _parse_summary(
        self,
        summary_text: str,
        sentiment_info: Optional[Dict],
        ticket_id: Optional[str]
    ) -> Dict[str, Any]:
        """Parse LLM summary into structured format."""
        
        # Extract key sections from summary
        key_points = {
            "customer_issue": self._extract_section(summary_text, ["customer issue", "main problem", "question"]),
            "attempted_solutions": self._extract_section(summary_text, ["attempted solutions", "solutions provided", "information provided"]),
            "current_status": self._extract_section(summary_text, ["current status", "current state", "status"])
        }
        
        # Extract action items and next steps
        action_items = self._extract_list_items(summary_text, ["action items", "action item", "needs to be done"])
        next_steps = self._extract_list_items(summary_text, ["next steps", "recommended next steps", "next step"])
        
        return {
            "summary": summary_text,
            "key_points": key_points,
            "sentiment": sentiment_info or {},
            "action_items": action_items,
            "next_steps": next_steps,
            "timestamp": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "summary_length": len(summary_text)
        }
    
    def _extract_section(self, text: str, keywords: List[str]) -> str:
        """Extract a section from summary text based on keywords."""
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                # Find the section after the keyword
                idx = text_lower.find(keyword)
                if idx != -1:
                    # Get text after keyword (up to next section or end)
                    section_start = idx + len(keyword)
                    section_text = text[section_start:].strip()
                    # Remove markdown formatting like :** at the start
                    section_text = section_text.lstrip(':*').strip()
                    # Take text until next section marker (** or ##) or end of paragraph
                    import re
                    # Find next section or double newline
                    next_section = re.search(r'\n\n|\*\*[A-Z]', section_text)
                    if next_section:
                        section_text = section_text[:next_section.start()].strip()
                    # Take first 2 sentences or up to 200 chars
                    sentences = re.split(r'\.(\s+[A-Z]|\s*$)', section_text)
                    if len(sentences) >= 3:
                        return (sentences[0] + '.' + sentences[1]).strip()
                    return section_text[:200].strip()
        return ""
    
    def _extract_list_items(self, text: str, keywords: List[str]) -> List[str]:
        """Extract list items from summary text."""
        items = []
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword in text_lower:
                idx = text_lower.find(keyword)
                if idx != -1:
                    # Get text after keyword
                    section = text[idx + len(keyword):].strip()
                    # Look for numbered or bulleted items
                    import re
                    # Match bullet points (* or -) or numbered lists (1. 2. etc.)
                    # Extract full lines that start with these markers
                    lines = section.split('\n')
                    for line in lines[:10]:  # Check first 10 lines
                        line = line.strip()
                        # Match lines starting with *, -, •, or numbers followed by . or )
                        if re.match(r'^[\*\-•]|\d+[\.\)]', line):
                            # Remove the bullet/number prefix
                            cleaned = re.sub(r'^[\*\-•]\s*|\d+[\.\)]\s*', '', line).strip()
                            if cleaned and len(cleaned) > 3:  # At least 3 characters
                                items.append(cleaned)
                    if items:
                        break
        
        return items[:5] if items else []
    
    def get_summary(
        self,
        user_id: str,
        session_id: str,
        ticket_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a stored summary."""
        summary_key = f"{user_id}_{session_id}"
        if ticket_id:
            summary_key = f"{summary_key}_{ticket_id}"
        
        return self._summaries.get(summary_key)
    
    def get_summaries_by_ticket(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Get all summaries for a specific ticket."""
        return [
            summary for key, summary in self._summaries.items()
            if summary.get("ticket_id") == ticket_id
        ]
    
    def export_summaries(
        self,
        format: str = "json",
        ticket_id: Optional[str] = None
    ) -> str:
        """
        Export summaries in various formats.
        
        Args:
            format: "json", "csv", or "text"
            ticket_id: Optional filter by ticket ID
            
        Returns:
            Exported summaries as string
        """
        summaries_to_export = self._summaries
        
        if ticket_id:
            summaries_to_export = {
                k: v for k, v in summaries_to_export.items()
                if v.get("ticket_id") == ticket_id
            }
        
        if format == "json":
            return json.dumps(summaries_to_export, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "Summary Key", "Ticket ID", "Timestamp", "Summary Length",
                "Customer Issue", "Current Status", "Sentiment", "Action Items"
            ])
            
            # Rows
            for key, summary in summaries_to_export.items():
                writer.writerow([
                    key,
                    summary.get("ticket_id", ""),
                    summary.get("timestamp", ""),
                    summary.get("summary_length", 0),
                    summary.get("key_points", {}).get("customer_issue", "")[:100],
                    summary.get("key_points", {}).get("current_status", "")[:100],
                    summary.get("sentiment", {}).get("sentiment", ""),
                    "; ".join(summary.get("action_items", []))[:200]
                ])
            
            return output.getvalue()
        
        elif format == "text":
            lines = []
            for key, summary in summaries_to_export.items():
                lines.append(f"Summary Key: {key}")
                lines.append(f"Ticket ID: {summary.get('ticket_id', 'N/A')}")
                lines.append(f"Timestamp: {summary.get('timestamp', 'N/A')}")
                lines.append(f"\nSummary:\n{summary.get('summary', 'N/A')}")
                lines.append(f"\nKey Points:")
                for point_key, point_value in summary.get("key_points", {}).items():
                    lines.append(f"  - {point_key}: {point_value}")
                lines.append(f"\nAction Items:")
                for item in summary.get("action_items", []):
                    lines.append(f"  - {item}")
                lines.append("\n" + "="*80 + "\n")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global summarizer instance
conversation_summarizer = ConversationSummarizer()

