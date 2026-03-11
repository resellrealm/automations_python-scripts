"""
Kimi AI Client
Connects to Kimi AI (or any OpenAI-compatible API) running on your VPS.
Configured via AI_API_URL and AI_API_KEY in your .env file.
"""

import os
import json
import requests
from typing import Optional


class KimiClient:
    def __init__(self, api_url: str = None, api_key: str = None, model: str = None):
        self.api_url = api_url or os.getenv("AI_API_URL", "https://api.moonshot.cn/v1/chat/completions")
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.model = model or os.getenv("AI_MODEL", "moonshot-v1-8k")
        self.timeout = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 600,  # conservative default — callers override when needed
    ) -> str:
        """
        Send a message to Kimi AI and return the response text.
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            raise RuntimeError(f"Kimi AI request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Kimi AI HTTP error: {e.response.status_code} — {e.response.text}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Kimi AI response format: {e}")

    def chat_json(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 400,  # JSON responses are compact
    ) -> dict:
        """
        Send a message and parse the response as JSON.
        The system prompt should instruct the model to respond with valid JSON only.
        """
        raw = self.chat(user_message, system_prompt, temperature, max_tokens)

        # Strip markdown code fences if present
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            clean = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Kimi AI returned invalid JSON: {e}\nRaw response:\n{raw}")
