"""
Google Cloud Speech-to-Text and Text-to-Speech utilities.
"""
import os
from typing import Optional
import logging
import io

logger = logging.getLogger(__name__)

# Try to import pydub for audio conversion
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not installed. Audio conversion will be limited. Install with: pip install pydub")

try:
    from google.cloud import speech
    from google.cloud import texttospeech
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logger.warning("Google Cloud Speech libraries not installed. Install with: pip install google-cloud-speech google-cloud-texttospeech")


def _convert_webm_to_wav(audio_data: bytes) -> Optional[bytes]:
    """
    Convert WebM Opus audio to WAV format for better compatibility.
    
    Args:
        audio_data: WebM Opus audio bytes
    
    Returns:
        WAV audio bytes or None if conversion fails
    """
    if not PYDUB_AVAILABLE:
        logger.warning("pydub not available, cannot convert audio")
        return None
    
    try:
        # Load WebM audio
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        
        # Convert to WAV (16-bit PCM, mono, 16kHz - optimal for Speech-to-Text)
        wav_audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # Export to WAV bytes
        wav_buffer = io.BytesIO()
        wav_audio.export(wav_buffer, format="wav")
        wav_bytes = wav_buffer.getvalue()
        
        logger.info(f"Converted WebM to WAV: {len(audio_data)} bytes -> {len(wav_bytes)} bytes")
        return wav_bytes
    except Exception as e:
        logger.error(f"Error converting WebM to WAV: {e}")
        return None


def transcribe_audio(audio_data: bytes, language_code: str = "en-US") -> Optional[str]:
    """
    Transcribe audio to text using Google Cloud Speech-to-Text.
    
    Args:
        audio_data: Audio bytes (WebM, WAV, FLAC, or LINEAR16 format)
        language_code: Language code (default: "en-US")
    
    Returns:
        Transcribed text or None if error
    """
    if not GOOGLE_CLOUD_AVAILABLE:
        logger.error("Google Cloud Speech not available")
        return None
    
    # Detect format: WAV files start with "RIFF"
    is_wav = audio_data[:4] == b'RIFF'
    
    # Try to convert WebM to WAV only if not already WAV
    if not is_wav:
        converted_audio = _convert_webm_to_wav(audio_data)
        if converted_audio:
            audio_data = converted_audio
            is_wav = True
            logger.info("Converted WebM to WAV")
    
    try:
        # Initialize client with credentials if provided
        # Priority order:
        # 1. GOOGLE_APPLICATION_CREDENTIALS_JSON (env var - for Railway/deployment)
        # 2. GOOGLE_APPLICATION_CREDENTIALS (file path - env var)
        # 3. credentials.json in project root (local development)
        # 4. Application Default Credentials (ADC)
        
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if credentials_json:
            # Option 1: JSON from environment variable (Railway/deployment)
            import json
            from google.oauth2 import service_account
            credentials_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            client = speech.SpeechClient(credentials=credentials)
        elif credentials_path and os.path.exists(credentials_path):
            # Option 2: File path from environment variable
            client = speech.SpeechClient()
        else:
            # Option 3: Try credentials.json in project root (local development)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_credentials = os.path.join(project_root, "credentials.json")
            if os.path.exists(local_credentials):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_credentials
                logger.info(f"Using credentials.json from project root: {local_credentials}")
            # Option 4: Use default credentials (ADC or GOOGLE_APPLICATION_CREDENTIALS)
            client = speech.SpeechClient()
        
        # If WAV, use LINEAR16 directly (most reliable)
        if is_wav:
            try:
                logger.info(f"Using LINEAR16 encoding for WAV format (size: {len(audio_data)} bytes)...")
                
                # Try different sample rates (16kHz is most common, but try others)
                sample_rates = [16000, 44100, 48000]
                
                for sample_rate in sample_rates:
                    try:
                        logger.info(f"Trying LINEAR16 with {sample_rate}Hz...")
                        config = speech.RecognitionConfig(
                            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                            sample_rate_hertz=sample_rate,
                            language_code=language_code,
                            model="long",  # Use 'long' model for better accuracy
                            enable_automatic_punctuation=True,
                        )
                        
                        audio = speech.RecognitionAudio(content=audio_data)
                        response = client.recognize(config=config, audio=audio)
                        
                        if response.results:
                            transcript = " ".join([result.alternatives[0].transcript for result in response.results])
                            if transcript.strip():
                                logger.info(f"Transcription successful with LINEAR16 ({sample_rate}Hz): {transcript[:100]}...")
                                return transcript
                    except Exception as rate_error:
                        logger.debug(f"LINEAR16 with {sample_rate}Hz failed: {rate_error}")
                        continue
                
                logger.warning("All LINEAR16 sample rates failed, trying auto-detect...")
            except Exception as wav_error:
                logger.warning(f"LINEAR16 processing failed: {wav_error}, trying auto-detect...")
        
        # Fallback to auto-detect
        try:
            logger.info("Trying with ENCODING_UNSPECIFIED (automatic format detection)...")
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,  # Auto-detect format
                language_code=language_code,
                model="long",  # Use 'long' model for better accuracy (if available)
                enable_automatic_punctuation=True,
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            response = client.recognize(config=config, audio=audio)
            
            logger.info(f"Auto-detect response: {len(response.results) if response.results else 0} results")
            
            if response.results:
                transcript = " ".join([result.alternatives[0].transcript for result in response.results])
                if transcript.strip():
                    logger.info(f"Transcription successful with auto-detect: {transcript[:100]}...")
                    return transcript
                else:
                    logger.warning("Auto-detect returned empty transcript")
            else:
                logger.warning("Auto-detect returned no results - audio might be too short or silent")
        except Exception as auto_error:
            logger.error(f"Auto-detect failed: {auto_error}", exc_info=True)
        
        # Fallback to manual encoding strategies
        if is_wav:
            # If we converted to WAV, use LINEAR16 encoding
            encoding_strategies = [
                {
                    "name": "LINEAR16 (WAV converted)",
                    "config": speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz=16000,
                        language_code=language_code,
                        enable_automatic_punctuation=True,
                        model="default",
                    )
                },
                {
                    "name": "ENCODING_UNSPECIFIED (auto-detect)",
                    "config": speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                        language_code=language_code,
                        enable_automatic_punctuation=True,
                        model="default",
                    )
                },
            ]
        else:
            # Original WebM format
            encoding_strategies = [
                {
                    "name": "ENCODING_UNSPECIFIED (auto-detect)",
                    "config": speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                        language_code=language_code,
                        enable_automatic_punctuation=True,
                        model="default",
                    )
                },
                {
                    "name": "WEBM_OPUS",
                    "config": speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                        language_code=language_code,
                        enable_automatic_punctuation=True,
                        model="default",
                    )
                },
            ]
        
        audio = speech.RecognitionAudio(content=audio_data)
        
        # Try each encoding strategy
        for strategy in encoding_strategies:
            try:
                logger.info(f"Trying encoding: {strategy['name']}")
                response = client.recognize(config=strategy['config'], audio=audio)
                
                # Check for results
                if response.results:
                    transcript = " ".join([result.alternatives[0].transcript for result in response.results])
                    if transcript.strip():  # Make sure it's not empty
                        logger.info(f"Transcription successful with {strategy['name']}: {transcript[:100]}...")
                        return transcript
                    else:
                        logger.warning(f"Empty transcript with {strategy['name']}")
                else:
                    logger.warning(f"No results with {strategy['name']}")
                    
            except Exception as strategy_error:
                logger.warning(f"Strategy {strategy['name']} failed: {strategy_error}")
                continue
        
        # If all strategies failed, log detailed error
        logger.error("All encoding strategies failed. Audio might be too short, silent, or in unsupported format.")
        logger.error(f"Audio data size: {len(audio_data)} bytes")
        
        # Try one more time with long_running_recognize for potentially better error messages
        try:
            logger.info("Attempting long_running_recognize for better error details...")
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            operation = client.long_running_recognize(config=config, audio=audio)
            response = operation.result(timeout=10)  # 10 second timeout
            
            if response.results:
                transcript = " ".join([result.alternatives[0].transcript for result in response.results])
                if transcript.strip():
                    logger.info(f"Long-running transcription successful: {transcript[:100]}...")
                    return transcript
        except Exception as lro_error:
            logger.error(f"Long-running recognize also failed: {lro_error}")
        
        # Log detailed error info
        logger.error("All transcription attempts failed. Audio might be too short, silent, or corrupted.")
        logger.error(f"Audio data size: {len(audio_data)} bytes, Format: {'WAV' if is_wav else 'Unknown'}")
        
        # Try to get more info about the WAV file if it's WAV
        if is_wav and len(audio_data) > 44:
            try:
                # Read WAV header info
                sample_rate = int.from_bytes(audio_data[24:28], byteorder='little')
                channels = int.from_bytes(audio_data[22:24], byteorder='little')
                data_size = int.from_bytes(audio_data[40:44], byteorder='little')
                duration = data_size / (sample_rate * channels * 2)  # 2 bytes per sample
                logger.error(f"WAV info: {sample_rate}Hz, {channels} channels, ~{duration:.2f}s duration")
            except Exception as header_error:
                logger.debug(f"Could not parse WAV header: {header_error}")
        
        return None
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        return None


def text_to_speech(text: str, language_code: str = "en-US", voice_name: Optional[str] = None) -> Optional[bytes]:
    """
    Convert text to speech using Google Cloud Text-to-Speech.
    
    Args:
        text: Text to convert to speech
        language_code: Language code (default: "en-US")
        voice_name: Optional specific voice name (e.g., "en-US-Standard-B")
    
    Returns:
        Audio bytes (MP3 format) or None if error
    """
    if not GOOGLE_CLOUD_AVAILABLE:
        logger.error("Google Cloud Text-to-Speech not available")
        return None
    
    try:
        # Initialize client with credentials if provided
        # Priority order:
        # 1. GOOGLE_APPLICATION_CREDENTIALS_JSON (env var - for Railway/deployment)
        # 2. GOOGLE_APPLICATION_CREDENTIALS (file path - env var)
        # 3. credentials.json in project root (local development)
        # 4. Application Default Credentials (ADC)
        
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if credentials_json:
            # Option 1: JSON from environment variable (Railway/deployment)
            import json
            from google.oauth2 import service_account
            credentials_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            client = texttospeech.TextToSpeechClient(credentials=credentials)
        elif credentials_path and os.path.exists(credentials_path):
            # Option 2: File path from environment variable
            client = texttospeech.TextToSpeechClient()
        else:
            # Option 3: Try credentials.json in project root (local development)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_credentials = os.path.join(project_root, "credentials.json")
            if os.path.exists(local_credentials):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_credentials
                logger.info(f"Using credentials.json from project root: {local_credentials}")
            # Option 4: Use default credentials (ADC or GOOGLE_APPLICATION_CREDENTIALS)
            client = texttospeech.TextToSpeechClient()
        
        # Configure synthesis
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Voice selection
        if voice_name:
            voice = texttospeech.VoiceSelectionParams(
                name=voice_name,
                language_code=language_code,
            )
        else:
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            )
        
        # Audio config
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )
        
        # Perform synthesis
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        return response.audio_content
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        return None

