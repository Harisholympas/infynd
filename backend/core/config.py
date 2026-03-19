from pydantic import field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "AutoFlow - Workflow Automation Platform"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "autoflow-local-secret-key-change-in-prod"
    
    # Database
    SQLITE_PATH: str = str(BASE_DIR / "data" / "platform.db")
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    
    # RAG
    VECTOR_DB_PATH: str = str(BASE_DIR / "data" / "embeddings")
    KNOWLEDGE_BASE_PATH: str = str(BASE_DIR / "data" / "knowledge_base")
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Webhooks
    WEBHOOK_BASE_URL: str = "http://localhost:8000"
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True
    
    # Voice
    WHISPER_MODEL: str = "base"
    VOICE_UPLOADS_DIR: str = str(BASE_DIR / "data" / "voice_uploads")
    
    # Email (local SMTP for testing)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # Default Gmail background connection
    DEFAULT_GMAIL_EMAIL: str = ""
    DEFAULT_GMAIL_APP_PASSWORD: str = ""

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return True

        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "development", "dev", "local"}:
          return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
          return False
        return bool(value)
    
    class Config:
        env_file = str(BASE_DIR / "backend" / ".env")
        extra = "ignore"

settings = Settings()
