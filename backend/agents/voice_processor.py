"""
Voice Input Processing using OpenAI Whisper (runs 100% locally)
"""
import io
import tempfile
import os
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Offline speech-to-text using Whisper"""
    
    def __init__(self):
        self.model = None
        self.model_size = None
    
    def load_model(self, model_size: str = "base"):
        """Load Whisper model (downloads once, runs offline after)"""
        try:
            import whisper
            if self.model is None or self.model_size != model_size:
                logger.info(f"Loading Whisper model: {model_size}")
                self.model = whisper.load_model(model_size)
                self.model_size = model_size
                logger.info(f"✅ Whisper {model_size} model loaded")
        except ImportError:
            logger.error("Whisper not installed. Run: pip install openai-whisper")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
    
    async def transcribe_audio(self, audio_bytes: bytes, language: str = "en", audio_format: str = "webm") -> Dict:
        """Transcribe audio bytes to text.
        
        Notes:
        - Browser MediaRecorder commonly produces WebM/Opus; writing those bytes to a `.wav` file will fail.
        - Whisper relies on an ffmpeg binary to decode most formats. If you see decode errors, install ffmpeg.
        """
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            return {
                "text": "",
                "error": "Whisper model not available. Install with: pip install openai-whisper",
                "success": False
            }
        
        try:
            # Save audio to temp file with correct extension
            ext = (audio_format or "webm").lower().strip(".")
            if ext not in ("webm", "wav", "mp3", "m4a", "ogg"):
                ext = "webm"
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            # Transcribe
            result = self.model.transcribe(
                tmp_path,
                language=language,
                fp16=False  # Use fp32 for compatibility
            )
            
            os.unlink(tmp_path)
            
            return {
                "text": result["text"].strip(),
                "language": result.get("language", language),
                "segments": len(result.get("segments", [])),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                "text": "",
                "error": str(e),
                "success": False
            }
    
    async def clean_transcript(self, text: str) -> str:
        """Clean and normalize transcribed text"""
        # Remove filler words
        fillers = ["um", "uh", "er", "ah", "like", "you know", "so basically"]
        words = text.split()
        cleaned = [w for w in words if w.lower() not in fillers]
        return " ".join(cleaned).strip()


# Singleton
voice_processor = VoiceProcessor()
