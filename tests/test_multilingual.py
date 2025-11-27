"""
Comprehensive tests for multilingual support utilities.
Tests language detection, greetings, and error messages.
"""
import pytest
from utils.multilingual import detect_language, get_greeting, get_error_message


def test_detect_language_english():
    """Test language detection for English."""
    text = "Hello, how can I help you today?"
    lang = detect_language(text)
    assert lang == "en"  # Default language


def test_detect_language_french():
    """Test language detection for French."""
    text = "Bonjour, comment puis-je vous aider?"
    lang = detect_language(text)
    assert lang == "fr"


def test_detect_language_spanish():
    """Test language detection for Spanish."""
    text = "Hola, gracias por contactarnos"
    lang = detect_language(text)
    assert lang == "es"


def test_detect_language_german():
    """Test language detection for German."""
    text = "Hallo, danke schön"
    lang = detect_language(text)
    assert lang == "de"


def test_detect_language_italian():
    """Test language detection for Italian."""
    text = "Ciao, grazie mille"
    lang = detect_language(text)
    assert lang == "it"


def test_detect_language_portuguese():
    """Test language detection for Portuguese."""
    text = "Olá, obrigado"
    lang = detect_language(text)
    assert lang == "pt"


def test_detect_language_mixed():
    """Test language detection with mixed languages."""
    text = "Hello bonjour hola"
    lang = detect_language(text)
    # Should return the language with most matches
    assert lang in ["en", "fr", "es"]


def test_detect_language_empty():
    """Test language detection with empty text."""
    lang = detect_language("")
    assert lang == "en"  # Default


def test_detect_language_numbers_only():
    """Test language detection with numbers only."""
    lang = detect_language("12345")
    assert lang == "en"  # Default


def test_get_greeting_english():
    """Test get_greeting for English."""
    greeting = get_greeting("en")
    assert "hello" in greeting.lower() or "help" in greeting.lower()


def test_get_greeting_french():
    """Test get_greeting for French."""
    greeting = get_greeting("fr")
    assert "bonjour" in greeting.lower()


def test_get_greeting_spanish():
    """Test get_greeting for Spanish."""
    greeting = get_greeting("es")
    assert "hola" in greeting.lower()


def test_get_greeting_unknown_language():
    """Test get_greeting for unknown language (should default to English)."""
    greeting = get_greeting("xx")
    assert "hello" in greeting.lower() or "help" in greeting.lower()


def test_get_error_message_english():
    """Test get_error_message for English."""
    message = get_error_message("en")
    assert "error" in message.lower() or "apologize" in message.lower()


def test_get_error_message_french():
    """Test get_error_message for French."""
    message = get_error_message("fr")
    assert "erreur" in message.lower() or "excuse" in message.lower()


def test_get_error_message_spanish():
    """Test get_error_message for Spanish."""
    message = get_error_message("es")
    assert "error" in message.lower() or "siento" in message.lower()


def test_get_error_message_unknown_language():
    """Test get_error_message for unknown language (should default to English)."""
    message = get_error_message("xx")
    assert "error" in message.lower() or "apologize" in message.lower()


def test_get_greeting_all_languages():
    """Test get_greeting for all supported languages."""
    languages = ["en", "fr", "es", "de", "it", "pt"]
    for lang in languages:
        greeting = get_greeting(lang)
        assert len(greeting) > 0
        assert isinstance(greeting, str)


def test_get_error_message_all_languages():
    """Test get_error_message for all supported languages."""
    languages = ["en", "fr", "es", "de", "it", "pt"]
    for lang in languages:
        message = get_error_message(lang)
        assert len(message) > 0
        assert isinstance(message, str)

