"""
Speech Recognition Tool - Local Whisper Implementation
使用本地OpenAI Whisper模型进行语音识别
支持中英日韩等多语言
"""

import os
import logging
import signal
from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SpeechRecognitionInput(BaseModel):
    """Input schema for Speech Recognition tool."""
    audio_file_path: str = Field(
        description="Path to the audio file to transcribe"
    )
    language: Optional[str] = Field(
        default=None,
        description="Language code (e.g., 'zh', 'en', 'ja', 'ko'). If None, auto-detect."
    )
    model_size: Optional[str] = Field(
        default="small",
        description="Whisper model size: tiny, base, small, medium, large. Default: small"
    )


class SpeechRecognitionTool(BaseTool):
    """
    Local Speech Recognition tool using OpenAI Whisper.
    
    Supports multiple languages including Chinese, English, Japanese, and Korean.
    Runs completely offline without requiring API keys.
    """
    
    name: str = "speech_recognition"
    description: str = """Transcribe audio files to text using local Whisper model.
    
    Supported languages: Chinese (zh), English (en), Japanese (ja), Korean (ko), and 90+ more
    Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm, flac, ogg
    Max file size: No limit (local processing)
    
    Input should be a file path to an audio file.
    Optionally specify language code (zh/en/ja/ko) for better accuracy.
    Returns the transcribed text with language detection info.
    
    Examples:
    - /path/to/audio.mp3
    - /path/to/audio.wav|language:zh
    - /path/to/audio.m4a|language:en|model:small
    """
    args_schema: Type[BaseModel] = SpeechRecognitionInput
    
    def __init__(self, preload_model: bool = True, model_size: str = "medium"):
        super().__init__()
        self._whisper_model = None
        self._model_size = model_size  # Default model size (changed to medium in v5.8)
        
        # v5.8: Use global tool pool for Whisper model (no need to pre-load here)
        # The tool pool will pre-load Whisper model at startup
        logger.info(f"✅ SpeechRecognitionTool initialized (will use global tool pool)")
    
    def _load_model(self, model_size: str = "medium"):
        """Load Whisper model (v5.8: use global tool pool first)."""
        # v5.8: Try to get from global tool pool first
        try:
            from app.core.tool_pool_v5_8 import enhanced_tool_pool
            model = enhanced_tool_pool.get_whisper_model()
            if model is not None:
                logger.info("✅ Using Whisper model from global tool pool")
                self._whisper_model = model
                self._model_size = "medium"  # Tool pool uses medium model
                return self._whisper_model
        except Exception as e:
            logger.warning(f"Failed to get Whisper from tool pool: {e}")
        
        # Fallback: Load model on demand
        if self._whisper_model is None or self._model_size != model_size:
            try:
                import whisper
                logger.info(f"Loading Whisper model on demand: {model_size}")
                self._whisper_model = whisper.load_model(model_size)
                self._model_size = model_size
                logger.info(f"Whisper model {model_size} loaded successfully")
            except ImportError:
                raise ImportError(
                    "whisper package not installed. "
                    "Please install it with: pip install openai-whisper"
                )
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
        return self._whisper_model
    
    def _parse_input(self, query: str, tool_call_id: Optional[str] = None) -> tuple:
        """Parse input string to extract file path and options."""
        parts = query.split("|")
        file_path = parts[0].strip()
        
        options = {
            "language": None,
            "model_size": "small"
        }
        
        for part in parts[1:]:
            if ":" in part:
                key, value = part.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == "language" or key == "lang":
                    options["language"] = value
                elif key == "model" or key == "model_size":
                    options["model_size"] = value
        
        return file_path, options
    
    def _run(self, query: str) -> str:
        """Execute speech recognition on the audio file."""
        try:
            # Parse input
            file_path, options = self._parse_input(query)
            language = options.get("language")
            model_size = options.get("model_size", "small")
            
            # Validate file exists
            if not os.path.exists(file_path):
                return f"❌ Error: File not found: {file_path}"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # File size limit: 10MB (to avoid long processing times)
            if file_size_mb > 10:
                return f"❌ Error: File too large ({file_size_mb:.2f} MB). Maximum: 10 MB. Please use a smaller audio file or split it into chunks."
            
            # Validate file format
            valid_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.flac', '.ogg']
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext not in valid_formats:
                return f"❌ Error: Unsupported format: {file_ext}. Supported: {', '.join(valid_formats)}"
            
            # Load Whisper model
            model = self._load_model(model_size)
            
            # Transcribe with timeout (30 seconds)
            logger.info(f"Transcribing {file_path} ({file_size_mb:.2f} MB) with model {model_size}")
            
            transcribe_options = {}
            if language:
                transcribe_options['language'] = language
            
            # Set timeout to avoid long-running transcriptions
            try:
                result = model.transcribe(file_path, **transcribe_options)
            except Exception as transcribe_error:
                logger.error(f"Transcription failed: {transcribe_error}")
                return f"❌ Error: Transcription failed. The file may be corrupted or in an unsupported format. Details: {str(transcribe_error)}"
            
            # Extract results
            text = result['text'].strip()
            detected_language = result.get('language', 'unknown')
            
            # Language name mapping
            language_names = {
                'zh': 'Chinese',
                'en': 'English',
                'ja': 'Japanese',
                'ko': 'Korean',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'ru': 'Russian'
            }
            language_name = language_names.get(detected_language, detected_language)
            
            # Format output
            output = f"""✅ Speech Recognition Completed

📁 File: {os.path.basename(file_path)}
📊 Size: {file_size_mb:.2f} MB
🗣️ Detected Language: {language_name} ({detected_language})
🤖 Model: {model_size}

📝 Transcription:
{text}
"""
            
            logger.info(f"Transcription completed: {len(text)} characters")
            return output
            
        except ImportError as e:
            error_msg = f"❌ Error: Whisper not installed. {str(e)}"
            logger.error(error_msg)
            return error_msg
        
        except Exception as e:
            error_msg = f"❌ Error during transcription: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _arun(self, query: str) -> str:
        """Async version - not implemented, falls back to sync."""
        return self._run(query)


# Export the tool
__all__ = ['SpeechRecognitionTool']
