"""
Tests for Google Speech utilities (with mocks).
Tests audio transcription and text-to-speech with mocked Google Cloud APIs.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.google_speech import transcribe_audio, text_to_speech, _convert_webm_to_wav


def test_transcribe_audio_not_available():
    """Test transcribe_audio when Google Cloud is not available."""
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', False):
        result = transcribe_audio(b"fake audio data")
        assert result is None


def test_transcribe_audio_success():
    """Test successful audio transcription."""
    mock_response = Mock()
    mock_response.results = [
        Mock(alternatives=[Mock(transcript="Hello world")])
    ]
    
    mock_client = Mock()
    mock_client.recognize.return_value = mock_response
    
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', True):
        with patch('utils.google_speech.speech.SpeechClient', return_value=mock_client):
            result = transcribe_audio(b"RIFF" + b"fake wav data")
            assert result == "Hello world"


def test_transcribe_audio_empty_result():
    """Test transcription with empty result."""
    mock_response = Mock()
    mock_response.results = []
    
    mock_client = Mock()
    mock_client.recognize.return_value = mock_response
    
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', True):
        with patch('utils.google_speech.speech.SpeechClient', return_value=mock_client):
            result = transcribe_audio(b"fake audio data")
            assert result is None


def test_transcribe_audio_exception():
    """Test transcription with exception."""
    mock_client = Mock()
    mock_client.recognize.side_effect = Exception("API error")
    
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', True):
        with patch('utils.google_speech.speech.SpeechClient', return_value=mock_client):
            result = transcribe_audio(b"fake audio data")
            assert result is None


def test_text_to_speech_not_available():
    """Test text_to_speech when Google Cloud is not available."""
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', False):
        result = text_to_speech("Hello world")
        assert result is None


def test_text_to_speech_success():
    """Test successful text-to-speech conversion."""
    mock_response = Mock()
    mock_response.audio_content = b"fake mp3 audio"
    
    mock_client = Mock()
    mock_client.synthesize_speech.return_value = mock_response
    
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', True):
        with patch('utils.google_speech.texttospeech.TextToSpeechClient', return_value=mock_client):
            result = text_to_speech("Hello world")
            assert result == b"fake mp3 audio"


def test_text_to_speech_exception():
    """Test text_to_speech with exception."""
    mock_client = Mock()
    mock_client.synthesize_speech.side_effect = Exception("API error")
    
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', True):
        with patch('utils.google_speech.texttospeech.TextToSpeechClient', return_value=mock_client):
            result = text_to_speech("Hello world")
            assert result is None


def test_text_to_speech_with_voice_name():
    """Test text_to_speech with specific voice name."""
    mock_response = Mock()
    mock_response.audio_content = b"fake mp3 audio"
    
    mock_client = Mock()
    mock_client.synthesize_speech.return_value = mock_response
    
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', True):
        with patch('utils.google_speech.texttospeech.TextToSpeechClient', return_value=mock_client):
            result = text_to_speech("Hello world", voice_name="en-US-Standard-B")
            assert result == b"fake mp3 audio"
            # Verify voice was used
            call_args = mock_client.synthesize_speech.call_args
            assert call_args is not None


def test_convert_webm_to_wav_not_available():
    """Test _convert_webm_to_wav when pydub is not available."""
    with patch('utils.google_speech.PYDUB_AVAILABLE', False):
        result = _convert_webm_to_wav(b"fake webm data")
        assert result is None


@pytest.mark.skipif(True, reason="pydub requires audioop/pyaudioop which is not available in Python 3.13")
def test_convert_webm_to_wav_exception():
    """Test _convert_webm_to_wav with exception."""
    with patch('utils.google_speech.PYDUB_AVAILABLE', True):
        with patch('pydub.AudioSegment') as mock_audio:
            mock_audio.from_file.side_effect = Exception("Conversion error")
            result = _convert_webm_to_wav(b"fake webm data")
            assert result is None


def test_transcribe_audio_wav_format():
    """Test transcription with WAV format detection."""
    wav_data = b"RIFF" + b"fake wav data" * 100
    
    mock_response = Mock()
    mock_response.results = [
        Mock(alternatives=[Mock(transcript="Test transcription")])
    ]
    
    mock_client = Mock()
    mock_client.recognize.return_value = mock_response
    
    with patch('utils.google_speech.GOOGLE_CLOUD_AVAILABLE', True):
        with patch('utils.google_speech.speech.SpeechClient', return_value=mock_client):
            result = transcribe_audio(wav_data)
            # Should detect WAV format and use LINEAR16
            assert result == "Test transcription"

