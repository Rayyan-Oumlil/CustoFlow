"""
Multilingual Support Utilities

Provides basic language detection and translation capabilities.
"""
from typing import Optional, Dict
import re


# Language detection patterns (simple keyword-based)
LANGUAGE_PATTERNS = {
    "fr": ["bonjour", "salut", "merci", "aurevoir", "français", "france"],
    "es": ["hola", "gracias", "adiós", "español", "españa"],
    "de": ["hallo", "danke", "auf wiedersehen", "deutsch", "deutschland"],
    "it": ["ciao", "grazie", "arrivederci", "italiano", "italia"],
    "pt": ["olá", "obrigado", "tchau", "português", "portugal"],
}


def detect_language(text: str) -> str:
    """
    Detect language from text (simple keyword-based).
    
    In production, use a proper language detection library like langdetect.
    
    Args:
        text: Input text
        
    Returns:
        Language code (default: "en")
    """
    text_lower = text.lower()
    
    # Count matches for each language
    scores = {}
    for lang, keywords in LANGUAGE_PATTERNS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            scores[lang] = score
    
    # Return language with highest score, or "en" as default
    if scores:
        return max(scores, key=scores.get)
    return "en"


def get_greeting(language: str = "en") -> str:
    """
    Get greeting in specified language.
    
    Args:
        language: Language code
        
    Returns:
        Greeting message
    """
    greetings = {
        "en": "Hello! How can I help you today?",
        "fr": "Bonjour! Comment puis-je vous aider aujourd'hui?",
        "es": "¡Hola! ¿Cómo puedo ayudarte hoy?",
        "de": "Hallo! Wie kann ich Ihnen heute helfen?",
        "it": "Ciao! Come posso aiutarti oggi?",
        "pt": "Olá! Como posso ajudá-lo hoje?",
    }
    return greetings.get(language, greetings["en"])


def get_error_message(language: str = "en") -> str:
    """
    Get error message in specified language.
    
    Args:
        language: Language code
        
    Returns:
        Error message
    """
    messages = {
        "en": "I apologize, but I encountered an error. Please try again.",
        "fr": "Je m'excuse, mais j'ai rencontré une erreur. Veuillez réessayer.",
        "es": "Lo siento, pero encontré un error. Por favor, inténtalo de nuevo.",
        "de": "Es tut mir leid, aber ich habe einen Fehler festgestellt. Bitte versuchen Sie es erneut.",
        "it": "Mi dispiace, ma ho riscontrato un errore. Per favore riprova.",
        "pt": "Desculpe, mas encontrei um erro. Por favor, tente novamente.",
    }
    return messages.get(language, messages["en"])


# Note: For production, integrate with a translation API like Google Translate API
# or use a library like googletrans (unofficial) or deep-translator

