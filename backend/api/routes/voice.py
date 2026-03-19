"""Voice transcription API routes"""
import os
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio using local Whisper model"""
    Path(settings.VOICE_UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
    
    suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    with tempfile.NamedTemporaryFile(
        suffix=suffix, 
        dir=settings.VOICE_UPLOADS_DIR, 
        delete=False
    ) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        try:
            import whisper
            model = whisper.load_model(settings.WHISPER_MODEL)
            result = model.transcribe(tmp_path)
            transcript = result["text"].strip()
            language = result.get("language", "en")
            confidence = 0.95
        except ImportError:
            try:
                import vosk
                import wave
                import json as jsonlib
                model_path = Path(settings.BASE_DIR if hasattr(settings, 'BASE_DIR') else '.') / "models" / "vosk-model"
                if model_path.exists():
                    model = vosk.Model(str(model_path))
                    with wave.open(tmp_path) as wf:
                        rec = vosk.KaldiRecognizer(model, wf.getframerate())
                        data = wf.readframes(wf.getnframes())
                        rec.AcceptWaveform(data)
                        result = jsonlib.loads(rec.FinalResult())
                    transcript = result.get("text", "")
                    language = "en"
                    confidence = 0.85
                else:
                    raise FileNotFoundError("Vosk model not found")
            except Exception:
                transcript = "Voice transcription requires Whisper or Vosk. Please install: pip install openai-whisper"
                language = "en"
                confidence = 0.0
        
        return {"transcript": transcript, "confidence": confidence, "language": language}
    
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


@router.get("/status")
async def voice_status():
    """Check voice transcription availability"""
    try:
        import whisper
        return {"available": True, "engine": "whisper", "model": settings.WHISPER_MODEL}
    except ImportError:
        pass
    try:
        import vosk
        return {"available": True, "engine": "vosk"}
    except ImportError:
        pass
    return {"available": False, "message": "Install whisper or vosk for voice input"}
