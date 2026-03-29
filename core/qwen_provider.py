"""
Qwen Provider - интеграция с Ollama API для CorePilot AI
"""

from __future__ import annotations

import json
import threading
from typing import Literal, Optional, Tuple

import requests

from core.ai_stack_constants import COREPILOT_LLM_MODEL
from utils import cli_error, cli_traceback


class QwenProvider:
    def __init__(self, base_url: str = "http://localhost:11434", model: str | None = None):
        self.base_url = base_url
        self.model = model if model is not None else COREPILOT_LLM_MODEL
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Проверяет доступность Ollama и модели"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)

            if response.status_code != 200:
                cli_error(f"[Qwen] Ollama недоступен: HTTP {response.status_code}")
                return False

            data = response.json()
            models = data.get("models", [])

            for m in models:
                model_name = m.get("name", "")
                if model_name == self.model or self.model in model_name:
                    return True

            cli_error(f"[Qwen] Модель не найдена в Ollama: {self.model}")
            return False

        except requests.exceptions.RequestException as e:
            cli_error(f"[Qwen] Ошибка соединения с Ollama: {e}")
            return False
        except Exception as e:
            cli_error(f"[Qwen] Ошибка проверки Ollama: {e}")
            cli_traceback()
            return False

    def is_available(self) -> bool:
        """Публичный метод проверки доступности"""
        return self.available

    def _chat_payload(self, prompt: str, system_prompt: str, stream: bool) -> dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": stream,
            "format": "json",
            "think": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 20,
                "presence_penalty": 1.5,
                "num_predict": 1024,
                "num_ctx": 8192,
            },
        }

    def generate_response(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Один запрос без стрима (вспомогательно, тесты)."""
        outcome, text = self.generate_response_chat_stream(
            prompt, system_prompt, threading.Event()
        )
        return text if outcome == "ok" else None

    def generate_response_chat_stream(
        self,
        prompt: str,
        system_prompt: str,
        cancel_event: threading.Event,
    ) -> Tuple[Literal["ok", "cancelled", "error"], str]:
        """
        Стрим /api/chat с проверкой cancel_event между чанками.
        Возвращает (ok|cancelled|error, накопленный текст message.content).
        """
        if not self.available:
            return "error", ""

        payload = self._chat_payload(prompt, system_prompt, stream=True)
        accumulated = ""

        try:
            with requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=(30, 600),
            ) as response:
                if response.status_code != 200:
                    cli_error(f"[Qwen] HTTP {response.status_code}: {response.text[:500]}")
                    return "error", ""

                for line in response.iter_lines(decode_unicode=True):
                    if cancel_event.is_set():
                        return "cancelled", accumulated
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = data.get("message") or {}
                    piece = msg.get("content") or ""
                    if piece:
                        accumulated += piece
                    if data.get("done"):
                        break

            if cancel_event.is_set():
                return "cancelled", accumulated
            return "ok", accumulated

        except requests.exceptions.RequestException as e:
            if cancel_event.is_set():
                return "cancelled", accumulated
            cli_error(f"[Qwen] Ошибка streaming: {e}")
            return "error", accumulated
        except Exception as e:
            cli_error(f"[Qwen] Ошибка генерации: {e}")
            cli_traceback()
            return "error", accumulated
