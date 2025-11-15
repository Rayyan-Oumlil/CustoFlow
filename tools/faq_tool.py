"""FAQ search tool for customer support."""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


def _load_faq_data() -> List[Dict]:
    """
    Load FAQ data from JSON file.
    
    Returns:
        List of FAQ dictionaries
    """
    # Get the path to the data directory
    current_dir = Path(__file__).parent.parent
    faq_file = current_dir / "data" / "faq_knowledge_base.json"
    
    if not faq_file.exists():
        return []
    
    with open(faq_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("faqs", [])


def search_faq(query: str) -> Dict[str, any]:
    """
    Search FAQ knowledge base for relevant answers.
    
    This tool searches through the FAQ database to find the best matching
    answer for a customer query. It uses keyword matching to find relevant FAQs.
    
    Args:
        query: Customer's question or search query
        
    Returns:
        Dictionary with status and FAQ information:
        - Success: {"status": "success", "question": "...", "answer": "...", "category": "..."}
        - Error: {"status": "error", "error_message": "..."}
    """
    try:
        query_lower = query.lower().strip()
        faqs = _load_faq_data()
        
        if not faqs:
            return {
                "status": "error",
                "error_message": "FAQ database is empty or not found"
            }
        
        # Score FAQs based on keyword matches
        scored_faqs = []
        for faq in faqs:
            score = 0
            keywords = faq.get("keywords", [])
            question = faq.get("question", "").lower()
            answer = faq.get("answer", "").lower()
            
            # Check if query contains any keywords
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 2  # Keyword match is worth more
            
            # Check if query words appear in question or answer
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 3:  # Ignore short words
                    if word in question:
                        score += 1
                    if word in answer:
                        score += 0.5
            
            if score > 0:
                scored_faqs.append((score, faq))
        
        # Sort by score (highest first)
        scored_faqs.sort(key=lambda x: x[0], reverse=True)
        
        if scored_faqs:
            # Return the best match
            best_match = scored_faqs[0][1]
            best_score = scored_faqs[0][0]
            
            # If score is high enough, return as success
            if best_score >= 3:
                return {
                    "status": "success",
                    "question": best_match.get("question", ""),
                    "answer": best_match.get("answer", ""),
                    "category": best_match.get("category", "general"),
                    "match_score": best_score
                }
            else:
                # Low score - return as partial match
                return {
                    "status": "partial",
                    "question": best_match.get("question", ""),
                    "answer": best_match.get("answer", ""),
                    "category": best_match.get("category", "general"),
                    "note": "This is a related answer. If this doesn't fully address your question, please provide more details."
                }
        else:
            # No matches found - provide general helpful answer based on query topic
            general_answer = _generate_general_answer(query_lower, faqs)
            return {
                "status": "partial",
                "answer": general_answer,
                "note": "I couldn't find an exact match, but here's general information. Please contact support for specific details."
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error searching FAQ: {str(e)}"
        }

