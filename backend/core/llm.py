"""Local LLM interface via Ollama"""
import json
import logging
import httpx
from typing import Optional
from core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for local Ollama LLM"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.embed_model = settings.OLLAMA_EMBED_MODEL
    
    async def generate(self, prompt: str, system: Optional[str] = None, 
                       temperature: float = 0.1) -> str:
        """Generate text using local Ollama"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            return self._fallback_response(prompt)
    
    async def chat(self, messages: list, system: Optional[str] = None) -> str:
        """Chat completion via Ollama"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return self._fallback_response(str(messages))
    
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings using local model"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Ollama has used both /api/embeddings (older) and /api/embed (newer).
                # Try embeddings first for backwards compatibility, then fall back.
                try:
                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.embed_model, "prompt": text}
                    )
                    response.raise_for_status()
                    return response.json()["embedding"]
                except Exception:
                    response = await client.post(
                        f"{self.base_url}/api/embed",
                        json={"model": self.embed_model, "input": text}
                    )
                    response.raise_for_status()
                    data = response.json()
                    # /api/embed may return {"embeddings":[...]} or {"embedding":[...]} depending on version
                    if "embedding" in data:
                        return data["embedding"]
                    if "embeddings" in data and data["embeddings"]:
                        return data["embeddings"][0]
                    raise ValueError("Unexpected embed response shape")
        except Exception as e:
            logger.error(f"Ollama embed error: {e}")
            # Return a simple deterministic embedding as fallback
            import hashlib
            h = hashlib.md5(text.encode()).digest()
            return [float(b) / 255.0 for b in h] * 24  # 384 dims
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback when Ollama is unavailable"""
        return json.dumps({
            "agent_name": "Task Automation Agent",
            "department": "General",
            "role": "Assistant",
            "steps": ["Analyze input", "Process task", "Generate output"],
            "tools": ["text_processor"],
            "triggers": ["manual"],
            "memory": True,
            "note": "Ollama offline - using fallback blueprint"
        })
    
    async def check_availability(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except:
            return False


# Singleton
llm_client = OllamaClient()
