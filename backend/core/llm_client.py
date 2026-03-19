"""
Local LLM client - talks to Ollama running locally
NO external API calls
"""
import httpx
import json
from typing import AsyncGenerator
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for local Ollama LLM server"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = httpx.Timeout(120.0)
    
    async def generate(self, prompt: str, system: str = None, temperature: float = 0.7) -> str:
        """Generate text using local Ollama model"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2048,
            }
        }
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama. Make sure it's running: ollama serve")
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._fallback_response(prompt)
    
    async def generate_json(self, prompt: str, system: str = None) -> dict:
        """Generate structured JSON response"""
        json_system = (system or "") + "\nYou MUST respond with valid JSON only. No markdown, no explanation, just JSON."
        response = await self.generate(prompt, system=json_system, temperature=0.3)
        
        # Clean up response
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            logger.warning(f"Could not parse JSON, using fallback")
            return {"error": "parse_failed", "raw": response}
    
    async def stream_generate(self, prompt: str, system: str = None) -> AsyncGenerator[str, None]:
        """Stream generation token by token"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": 0.7}
        }
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if token := data.get("response"):
                                yield token
                            if data.get("done"):
                                break
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield "Error generating response. Make sure Ollama is running."
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback when Ollama is not available"""
        return json.dumps({
            "error": "ollama_unavailable",
            "message": "Ollama is not running. Start it with: ollama serve",
            "fallback": True
        })
    
    async def check_health(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> list:
        """List available local models"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except:
            return []


# Singleton client
ollama_client = OllamaClient()
