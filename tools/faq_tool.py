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
    import logging
    logger = logging.getLogger(__name__)
    
    # Get the path to the data directory
    current_dir = Path(__file__).parent.parent
    faq_file = current_dir / "data" / "faq_knowledge_base.json"
    
    print(f"[FAQ_TOOL] Looking for FAQ file at: {faq_file}")
    print(f"[FAQ_TOOL] Current directory: {current_dir}")
    print(f"[FAQ_TOOL] File exists: {faq_file.exists()}")
    logger.info(f"[FAQ_TOOL] Looking for FAQ file at: {faq_file}")
    logger.info(f"[FAQ_TOOL] Current directory: {current_dir}")
    logger.info(f"[FAQ_TOOL] File exists: {faq_file.exists()}")
    
    if not faq_file.exists():
        print(f"[FAQ_TOOL] ⚠️ ERROR: FAQ file not found at {faq_file}")
        logger.error(f"[FAQ_TOOL] ⚠️ ERROR: FAQ file not found at {faq_file}")
        # Try to list what's in the data directory
        data_dir = current_dir / "data"
        if data_dir.exists():
            files = list(data_dir.glob("*.json"))
            print(f"[FAQ_TOOL] Files in data directory: {[f.name for f in files]}")
            logger.info(f"[FAQ_TOOL] Files in data directory: {[f.name for f in files]}")
        return []
    
    try:
        with open(faq_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            faqs = data.get("faqs", [])
            print(f"[FAQ_TOOL] ✅ Successfully loaded {len(faqs)} FAQs from {faq_file}")
            logger.info(f"[FAQ_TOOL] ✅ Successfully loaded {len(faqs)} FAQs from {faq_file}")
            
            # Log first few FAQ questions for debugging
            if faqs:
                first_questions = [faq.get("question", "")[:50] for faq in faqs[:3]]
                print(f"[FAQ_TOOL] First 3 FAQ questions: {first_questions}")
                logger.info(f"[FAQ_TOOL] First 3 FAQ questions: {first_questions}")
            
            return faqs
    except Exception as e:
        print(f"[FAQ_TOOL] ⚠️ ERROR loading FAQ file: {e}")
        logger.error(f"[FAQ_TOOL] ⚠️ ERROR loading FAQ file: {e}")
        import traceback
        traceback.print_exc()
        return []


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
        import logging
        logger = logging.getLogger(__name__)
        
        # Log function entry immediately
        print(f"[FAQ_TOOL] ====== search_faq called with query: '{query}' ======")
        logger.info(f"[FAQ_TOOL] ====== search_faq called with query: '{query}' ======")
        
        # Validate input
        if not query or not query.strip():
            print(f"[FAQ_TOOL] ERROR: Empty query")
            logger.warning(f"[FAQ_TOOL] ERROR: Empty query")
            return {
                "status": "error",
                "error_message": "Query cannot be empty"
            }
        
        query_lower = query.lower().strip()
        print(f"[FAQ_TOOL] Normalized query: '{query_lower}'")
        logger.info(f"[FAQ_TOOL] Normalized query: '{query_lower}'")
        
        # Check cache first (but allow cache invalidation for common queries)
        cache_key = generate_cache_key("faq", query_lower)
        cached_result = faq_cache.get(cache_key)
        
        # For refund policy queries, ALWAYS invalidate cache and do fresh search
        if "refund" in query_lower or "policy" in query_lower:
            if cached_result:
                print(f"[FAQ_TOOL] ⚠️ Cache invalidated for refund/policy query, doing fresh search")
                logger.info(f"[FAQ_TOOL] ⚠️ Cache invalidated for refund/policy query, doing fresh search")
                # Delete from cache to force fresh search
                if hasattr(faq_cache, 'delete'):
                    faq_cache.delete(cache_key)
                cached_result = None
        elif cached_result:
            print(f"[FAQ_TOOL] Using cached result for query: '{query_lower}'")
            logger.info(f"[FAQ_TOOL] Using cached result for query: '{query_lower}'")
            return cached_result
        
        faqs = _load_faq_data()
        print(f"[FAQ_TOOL] Loaded {len(faqs)} FAQs from database")
        logger.info(f"[FAQ_TOOL] Loaded {len(faqs)} FAQs from database")
        
        if not faqs:
            print(f"[FAQ_TOOL] ERROR: FAQ database is empty or not found")
            logger.error(f"[FAQ_TOOL] ERROR: FAQ database is empty or not found")
            return {
                "status": "error",
                "error_message": "FAQ database is empty or not found"
            }
        
        # Try semantic search first if enabled and available
        semantic_search_used = False
        semantic_search_failed = False
        if use_semantic:
            try:
                from tools.semantic_search import get_semantic_engine, SEMANTIC_SEARCH_AVAILABLE
                
                if SEMANTIC_SEARCH_AVAILABLE:
                    engine = get_semantic_engine()
                    if engine:
                        # Try to load index if not already loaded
                        if not engine.is_index_loaded():
                            load_success = engine.load_index()
                            # If loading failed, skip semantic search and use keyword search
                            if not load_success:
                                print(f"[FAQ_TOOL] Semantic search index not loaded, falling back to keyword search")
                                semantic_search_failed = True
                        
                        # If index is loaded, use semantic search
                        if not semantic_search_failed and engine.is_index_loaded():
                            print(f"[FAQ_TOOL] ✅ Semantic search index is loaded, performing semantic search")
                            logger.info(f"[FAQ_TOOL] ✅ Semantic search index is loaded, performing semantic search")
                            results = engine.search(query, top_k=3)
                            
                            print(f"[FAQ_TOOL] Semantic search returned {len(results) if results else 0} results")
                            logger.info(f"[FAQ_TOOL] Semantic search returned {len(results) if results else 0} results")
                            
                            if results and len(results) > 0:
                                best_match, similarity = results[0]
                                best_question = best_match.get("question", "")
                                best_answer = best_match.get("answer", "")[:100]
                                print(f"[FAQ_TOOL] 🔍 Semantic search - Best match:")
                                print(f"[FAQ_TOOL]    Question: '{best_question}'")
                                print(f"[FAQ_TOOL]    Answer preview: '{best_answer}...'")
                                print(f"[FAQ_TOOL]    Similarity: {similarity:.3f}")
                                print(f"[FAQ_TOOL]    Category: {best_match.get('category', 'N/A')}")
                                logger.info(f"[FAQ_TOOL] 🔍 Semantic search - Best match: '{best_question[:50]}...' with similarity: {similarity:.3f}")
                                
                                # Log all results for debugging
                                print(f"[FAQ_TOOL] All semantic search results:")
                                for idx, (match, sim) in enumerate(results[:3], 1):
                                    print(f"[FAQ_TOOL]   {idx}. '{match.get('question', '')[:50]}...' (similarity: {sim:.3f})")
                                    logger.debug(f"[FAQ_TOOL]   {idx}. '{match.get('question', '')[:50]}...' (similarity: {sim:.3f})")
                                
                                # For refund/policy queries, lower the threshold (they should match well)
                                threshold = 0.5 if ("refund" in query_lower or "policy" in query_lower or "return" in query_lower) else 0.6
                                print(f"[FAQ_TOOL] Using similarity threshold: {threshold} (query contains refund/policy/return: {('refund' in query_lower or 'policy' in query_lower or 'return' in query_lower)})")
                                logger.info(f"[FAQ_TOOL] Using similarity threshold: {threshold}")
                                
                                # Use similarity threshold to determine if it's a good match
                                # Higher similarity = better match
                                if similarity >= threshold:  # Good match threshold (lowered for refund queries)
                                    result = {
                                        "status": "success",
                                        "question": best_match.get("question", ""),
                                        "answer": best_match.get("answer", ""),
                                        "category": best_match.get("category", "general"),
                                        "match_type": "semantic",
                                        "similarity": round(similarity, 3)
                                    }
                                    # Cache and return semantic result
                                    faq_cache.set(cache_key, result)
                                    print(f"[FAQ_TOOL] ✅ Returning SUCCESS from semantic search (similarity {similarity:.3f} >= {threshold})")
                                    logger.info(f"[FAQ_TOOL] ✅ Returning SUCCESS from semantic search (similarity {similarity:.3f} >= {threshold})")
                                    return result
                                elif similarity >= 0.3:  # Lower similarity, still useful but mark as partial (lowered from 0.4)
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
                                    print(f"[FAQ_TOOL] ⚠️ Returning PARTIAL from semantic search (similarity {similarity:.3f} >= 0.3 but < {threshold})")
                                    logger.info(f"[FAQ_TOOL] ⚠️ Returning PARTIAL from semantic search (similarity {similarity:.3f} >= 0.3 but < {threshold})")
                                    return result
                                else:
                                    print(f"[FAQ_TOOL] ⚠️ Semantic search similarity {similarity:.3f} < 0.3, falling back to keyword search")
                                    logger.info(f"[FAQ_TOOL] ⚠️ Semantic search similarity {similarity:.3f} < 0.3, falling back to keyword search")
                                # If similarity < 0.4, fall through to keyword search for better results
                            else:
                                print(f"[FAQ_TOOL] ⚠️ Semantic search returned no results, falling back to keyword search")
                                logger.warning(f"[FAQ_TOOL] ⚠️ Semantic search returned no results, falling back to keyword search")
                            # If no results from semantic search, fall through to keyword search
                    else:
                        print(f"[FAQ_TOOL] Semantic search engine not available, using keyword search")
                        semantic_search_failed = True
                else:
                    print(f"[FAQ_TOOL] Semantic search not available, using keyword search")
                    semantic_search_failed = True
            except Exception as e:
                # Semantic search failed, fall back to keyword search
                # Log error for debugging but don't break the flow
                import logging
                logger = logging.getLogger(__name__)
                print(f"[FAQ_TOOL] Semantic search failed with error: {e}, falling back to keyword search")
                logger.debug(f"Semantic search failed, using keyword search: {e}")
                semantic_search_failed = True
        
        # Fallback to keyword-based search (original algorithm)
        # Use print for immediate visibility in Cloud Run logs
        print(f"[FAQ_TOOL] ====== Starting KEYWORD search fallback ======")
        print(f"[FAQ_TOOL] Query: '{query_lower}'")
        print(f"[FAQ_TOOL] Number of FAQs available: {len(faqs)}")
        logger.info(f"[FAQ_TOOL] Starting keyword search for query: '{query_lower}' (fallback from semantic search)")
        
        scored_faqs = []
        for faq in faqs:
            score = 0
            keywords = faq.get("keywords", [])
            question = faq.get("question", "").lower()
            answer = faq.get("answer", "").lower()
            faq_id = faq.get("question", "")[:50]  # For logging
            
            # Check if query contains any keywords (higher weight for multi-word keywords)
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in query_lower:
                    # Multi-word keywords (like "refund policy") are worth more
                    if " " in keyword_lower:
                        score += 4  # Multi-word keyword match is worth even more
                        print(f"[FAQ_TOOL] FAQ '{faq_id}...': Multi-word keyword match '{keyword_lower}' (+4)")
                        logger.debug(f"[FAQ_TOOL] Multi-word keyword match: '{keyword_lower}' (+4)")
                    else:
                        score += 2  # Single keyword match
                        print(f"[FAQ_TOOL] FAQ '{faq_id}...': Single keyword match '{keyword_lower}' (+2)")
                        logger.debug(f"[FAQ_TOOL] Single keyword match: '{keyword_lower}' (+2)")
            
            # Check if query words appear in question or answer
            # Handle apostrophes and punctuation better
            import re
            query_words = re.findall(r"\b\w+\b", query_lower)  # Extract words, handling apostrophes
            for word in query_words:
                if len(word) > 3:  # Ignore short words
                    if word in question:
                        score += 1
                        logger.debug(f"[FAQ_TOOL] Word '{word}' found in question (+1)")
                    if word in answer:
                        score += 0.5
                        logger.debug(f"[FAQ_TOOL] Word '{word}' found in answer (+0.5)")
            
            # Bonus: if the question contains key phrases from the FAQ question
            # Normalize contractions (what's -> what is, etc.)
            normalized_query = query_lower.replace("what's", "what is").replace("what're", "what are")
            normalized_question = question.replace("what's", "what is").replace("what're", "what are")
            
            # Check if main words from FAQ question appear in query
            question_words = re.findall(r"\b\w+\b", normalized_question)
            query_words_set = set(re.findall(r"\b\w+\b", normalized_query))
            matching_words = [w for w in question_words if len(w) > 3 and w in query_words_set]
            if len(matching_words) >= 2:  # At least 2 significant words match
                score += 2  # Bonus for matching question structure
                print(f"[FAQ_TOOL] FAQ '{faq_id}...': Question structure match {matching_words} (+2)")
                logger.debug(f"[FAQ_TOOL] Question structure match: {matching_words} (+2)")
            
            if score > 0:
                scored_faqs.append((score, faq))
                print(f"[FAQ_TOOL] FAQ '{faq_id}...' scored {score} points total")
                logger.debug(f"[FAQ_TOOL] FAQ '{question[:50]}...' scored {score} points")
        
        # Sort by score (highest first)
        scored_faqs.sort(key=lambda x: x[0], reverse=True)
        
        print(f"[FAQ_TOOL] Found {len(scored_faqs)} FAQ(s) with score > 0")
        logger.info(f"[FAQ_TOOL] Found {len(scored_faqs)} FAQ(s) with score > 0")
        
        if scored_faqs:
            # Return the best match
            best_match = scored_faqs[0][1]
            best_score = scored_faqs[0][0]
            best_question = best_match.get("question", "")
            
            print(f"[FAQ_TOOL] Best match: '{best_question[:50]}...' with score {best_score}")
            logger.info(f"[FAQ_TOOL] Best match: '{best_question[:50]}...' with score {best_score}")
            
            # If score is high enough, return as success
            # Lowered threshold from 3 to 2 to catch more matches
            if best_score >= 2:
                result = {
                    "status": "success",
                    "question": best_match.get("question", ""),
                    "answer": best_match.get("answer", ""),
                    "category": best_match.get("category", "general"),
                    "match_type": "keyword",
                    "match_score": best_score
                }
                print(f"[FAQ_TOOL] Returning SUCCESS (score {best_score} >= 2)")
                logger.info(f"[FAQ_TOOL] Returning SUCCESS (score {best_score} >= 2)")
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
                print(f"[FAQ_TOOL] Returning PARTIAL (score {best_score} < 2)")
                logger.info(f"[FAQ_TOOL] Returning PARTIAL (score {best_score} < 2)")
        else:
            # No matches found - provide general helpful answer based on query topic
            print(f"[FAQ_TOOL] ⚠️ No FAQ matches found for query: '{query_lower}'")
            logger.warning(f"[FAQ_TOOL] No FAQ matches found for query: '{query_lower}'")
            general_answer = _generate_general_answer(query_lower, faqs)
            result = {
                "status": "partial",
                "answer": general_answer,
                "match_type": "keyword",
                "note": "I couldn't find an exact match, but here's general information. Please contact support for specific details."
            }
            print(f"[FAQ_TOOL] Returning PARTIAL with general answer")
            logger.info(f"[FAQ_TOOL] Returning PARTIAL with general answer")
        
        # Cache the result before returning
        faq_cache.set(cache_key, result)
        print(f"[FAQ_TOOL] Final result: status={result.get('status')}, match_type={result.get('match_type')}, match_score={result.get('match_score', 'N/A')}")
        logger.info(f"[FAQ_TOOL] Final result: status={result.get('status')}, match_type={result.get('match_type')}, match_score={result.get('match_score', 'N/A')}")
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error searching FAQ: {str(e)}"
        }

