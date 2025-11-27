"""
FAQ Search Tool for Customer Support

This tool provides intelligent FAQ search capabilities with:
- Flexible keyword matching
- Partial match support
- General answer generation for unknown queries
- Category-based fallback
- Response caching for performance

Design:
- Uses scoring algorithm to rank FAQ matches
- Provides partial matches when exact match not found
- Generates helpful general answers based on query topics
- Caches responses to reduce computation
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Add utils to path for cache import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.cache import faq_cache, generate_cache_key


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


def _generate_general_answer(query: str, faqs: List[Dict]) -> str:
    """
    Generate a general answer when no exact FAQ match is found.
    Provides helpful context based on common topics.
    
    Args:
        query: The customer's query (lowercase)
        faqs: List of all FAQs for context
        
    Returns:
        A helpful general answer string
    """
    # Common topics and general responses
    if any(word in query for word in ["refund", "return", "money back", "reimburse"]):
        return "We offer a 30-day return policy. Items must be in original condition with tags attached. Refunds are processed within 5-7 business days after we receive the returned item. For specific refund questions, please contact our support team with your order details."
    
    elif any(word in query for word in ["shipping", "delivery", "track", "ship", "shipment", "transit"]):
        return "Shipping times vary by location and shipping method. Standard shipping typically takes 5-7 business days. Express shipping (2-3 business days) and overnight shipping are also available. You can track your order using the tracking number provided in your confirmation email. For specific shipping questions, please provide your order number."
    
    elif any(word in query for word in ["payment", "pay", "charge", "billing", "credit card", "invoice"]):
        return "We accept major credit cards, PayPal, and other secure payment methods. All transactions are encrypted and secure. For billing questions or payment issues, please contact our support team with your order number or transaction ID. We're here to help resolve any payment concerns."
    
    elif any(word in query for word in ["cancel", "change", "modify", "edit order"]):
        return "Order modifications depend on the order status. If your order hasn't shipped yet, you may be able to cancel or modify it. Once an order has shipped, changes may not be possible. Please contact support with your order number for assistance with cancellations or modifications."
    
    elif any(word in query for word in ["warranty", "guarantee", "defect", "broken", "damaged", "faulty"]):
        return "We stand behind our products with a warranty. If you received a defective or damaged item, please contact support immediately with photos and your order number. We'll help resolve this quickly, whether through replacement, repair, or refund."
    
    elif any(word in query for word in ["product", "item", "feature", "specification", "size", "color"]):
        return "For product information, specifications, availability, or questions about specific items, please provide the product name or SKU. You can also check our website for detailed product descriptions, reviews, and specifications. If you need more specific information, our support team can help."
    
    elif any(word in query for word in ["account", "login", "password", "profile", "settings"]):
        return "For account-related questions, you can manage your account settings, view order history, and update your information through your account dashboard. If you're having trouble logging in or need to reset your password, please contact our support team for assistance."
    
    else:
        # Extract categories from FAQs to provide context
        categories = set(faq.get("category", "general") for faq in faqs)
        category_list = ", ".join(sorted(categories))
        return f"I'm here to help! Our support covers various topics including: {category_list}. Could you provide more details about what you need help with? You can also contact our support team directly for personalized assistance with any questions or concerns."


def search_faq(query: str, use_semantic: bool = True) -> Dict[str, any]:
    """
    Search FAQ knowledge base for relevant answers.
    
    This tool implements a flexible FAQ search algorithm that:
    1. Checks cache first for performance
    2. Tries semantic search first (if available and enabled)
    3. Falls back to keyword-based scoring if semantic search fails
    4. Returns best match if score is high enough (>= 3)
    5. Returns partial match for lower scores
    6. Generates general answer if no matches found
    7. Caches result for future queries
    
    Search Methods:
    - Semantic Search (if available): Uses vector embeddings to find similar questions by meaning
    - Keyword Search (fallback): Scores FAQs based on keyword matches
    
    Scoring Algorithm (Keyword Search):
    - Keyword match: +2 points per matching keyword
    - Question word match: +1 point per matching word
    - Answer word match: +0.5 points per matching word
    - Only words > 3 characters are considered (filters out "the", "is", etc.)
    
    Args:
        query: Customer's question or search query
        use_semantic: Whether to try semantic search first (default: True)
        
    Returns:
        Dictionary with status and FAQ information:
        - Success: {"status": "success", "question": "...", "answer": "...", "category": "...", "match_type": "semantic"|"keyword", "similarity"|"match_score": N}
        - Partial: {"status": "partial", "answer": "...", "note": "..."}
        - Error: {"status": "error", "error_message": "..."}
    """
    try:
        # Validate input
        if not query or not query.strip():
            return {
                "status": "error",
                "error_message": "Query cannot be empty"
            }
        
        query_lower = query.lower().strip()
        
        # Check cache first
        cache_key = generate_cache_key("faq", query_lower)
        cached_result = faq_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        faqs = _load_faq_data()
        
        if not faqs:
            return {
                "status": "error",
                "error_message": "FAQ database is empty or not found"
            }
        
        # Try semantic search first if enabled and available
        if use_semantic:
            try:
                from tools.semantic_search import get_semantic_engine, SEMANTIC_SEARCH_AVAILABLE
                
                if SEMANTIC_SEARCH_AVAILABLE:
                    engine = get_semantic_engine()
                    if engine:
                        # Try to load index if not already loaded
                        if not engine.is_index_loaded():
                            engine.load_index()
                        
                        # If index is loaded, use semantic search
                        if engine.is_index_loaded():
                            results = engine.search(query, top_k=3)
                            
                            if results:
                                best_match, similarity = results[0]
                                
                                # Use similarity threshold to determine if it's a good match
                                # Higher similarity = better match
                                if similarity >= 0.6:  # Good match threshold
                                    result = {
                                        "status": "success",
                                        "question": best_match.get("question", ""),
                                        "answer": best_match.get("answer", ""),
                                        "category": best_match.get("category", "general"),
                                        "match_type": "semantic",
                                        "similarity": round(similarity, 3)
                                    }
                                else:  # Lower similarity, still useful but mark as partial
                                    result = {
                                        "status": "partial",
                                        "question": best_match.get("question", ""),
                                        "answer": best_match.get("answer", ""),
                                        "category": best_match.get("category", "general"),
                                        "match_type": "semantic",
                                        "similarity": round(similarity, 3),
                                        "note": "This is a related answer found using semantic search. If this doesn't fully address your question, please provide more details."
                                    }
                                
                                # Cache and return semantic result
                                faq_cache.set(cache_key, result)
                                return result
            except Exception as e:
                # Semantic search failed, fall back to keyword search
                # Don't print error in production, just silently fall back
                pass
        
        # Fallback to keyword-based search (original algorithm)
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
                result = {
                    "status": "success",
                    "question": best_match.get("question", ""),
                    "answer": best_match.get("answer", ""),
                    "category": best_match.get("category", "general"),
                    "match_type": "keyword",
                    "match_score": best_score
                }
            else:
                # Low score - return as partial match
                result = {
                    "status": "partial",
                    "question": best_match.get("question", ""),
                    "answer": best_match.get("answer", ""),
                    "category": best_match.get("category", "general"),
                    "match_type": "keyword",
                    "match_score": best_score,
                    "note": "This is a related answer. If this doesn't fully address your question, please provide more details."
                }
        else:
            # No matches found - provide general helpful answer based on query topic
            general_answer = _generate_general_answer(query_lower, faqs)
            result = {
                "status": "partial",
                "answer": general_answer,
                "match_type": "keyword",
                "note": "I couldn't find an exact match, but here's general information. Please contact support for specific details."
            }
        
        # Cache the result before returning
        faq_cache.set(cache_key, result)
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error searching FAQ: {str(e)}"
        }

