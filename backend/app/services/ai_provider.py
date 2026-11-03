from typing import Any, Optional
import httpx
from sqlalchemy.orm import Session
from app.models import SystemSettingsConfig
from app.security import decrypt_secret


class AIProviderOrchestrator:
    """Provider-independent AI abstraction supporting Gemini, Claude, OpenAI-compatible, Ollama, and deterministic fallback."""

    def __init__(self, db: Session):
        self.db = db
        self.config = db.query(SystemSettingsConfig).first()

    def get_active_provider_info(self) -> dict[str, Any]:
        if not self.config:
            return {"provider": "deterministic", "model": "rule-engine-v1", "live_api_configured": False}
        provider = self.config.ai_provider or "deterministic"
        has_key = False
        if provider == "gemini":
            has_key = bool(decrypt_secret(self.config.encrypted_gemini_key))
        elif provider == "claude":
            has_key = bool(decrypt_secret(self.config.encrypted_anthropic_key))
        elif provider == "openai":
            has_key = bool(decrypt_secret(self.config.encrypted_openai_key))
        elif provider == "ollama":
            has_key = True
        return {
            "provider": provider,
            "model": self.config.ai_model if provider != "ollama" else self.config.ollama_model,
            "live_api_configured": has_key,
        }

    def generate_text(self, system_prompt: str, user_prompt: str, fallback_text: str) -> str:
        """Attempts configured AI provider; falls back cleanly to verified deterministic engine if offline or unconfigured."""
        if not self.config or self.config.ai_provider == "deterministic":
            return fallback_text

        provider = self.config.ai_provider.lower()
        try:
            if provider == "ollama":
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(
                        f"{self.config.ollama_base_url.rstrip('/')}/api/generate",
                        json={
                            "model": self.config.ollama_model or "llama3.2",
                            "prompt": f"{system_prompt}\n\n{user_prompt}",
                            "stream": False,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("response"):
                            return str(data["response"]).strip()

            elif provider == "gemini":
                api_key = decrypt_secret(self.config.encrypted_gemini_key)
                if api_key:
                    model = self.config.ai_model or "gemini-2.5-flash"
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    with httpx.Client(timeout=12.0) as client:
                        resp = client.post(
                            url,
                            json={
                                "system_instruction": {"parts": [{"text": system_prompt}]},
                                "contents": [{"parts": [{"text": user_prompt}]}],
                            },
                        )
                        if resp.status_code == 200:
                            candidates = resp.json().get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts and parts[0].get("text"):
                                    return str(parts[0]["text"]).strip()

            elif provider == "openai":
                api_key = decrypt_secret(self.config.encrypted_openai_key)
                if api_key:
                    base_url = (self.config.openai_base_url or "https://api.openai.com/v1").rstrip("/")
                    with httpx.Client(timeout=12.0) as client:
                        resp = client.post(
                            f"{base_url}/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json={
                                "model": self.config.ai_model or "gpt-4o-mini",
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt},
                                ],
                            },
                        )
                        if resp.status_code == 200:
                            choices = resp.json().get("choices", [])
                            if choices:
                                return str(choices[0]["message"]["content"]).strip()

            elif provider == "claude":
                api_key = decrypt_secret(self.config.encrypted_anthropic_key)
                if api_key:
                    with httpx.Client(timeout=12.0) as client:
                        resp = client.post(
                            "https://api.anthropic.com/v1/messages",
                            headers={
                                "x-api-key": api_key,
                                "anthropic-version": "2023-06-01",
                                "content-type": "application/json",
                            },
                            json={
                                "model": self.config.ai_model or "claude-3-5-sonnet-latest",
                                "max_tokens": self.config.token_limit or 2048,
                                "system": system_prompt,
                                "messages": [{"role": "user", "content": user_prompt}],
                            },
                        )
                        if resp.status_code == 200:
                            content = resp.json().get("content", [])
                            if content and content[0].get("text"):
                                return str(content[0]["text"]).strip()
        except Exception:
            pass

        return fallback_text
