"""
Проверка доступности Ollama и наличия модели — без UI.
"""

from __future__ import annotations

from typing import Any

import requests

from core.ai_stack_constants import COREPILOT_LLM_MODEL, OLLAMA_DEFAULT_BASE, ollama_tags_endpoint


def fetch_ollama_tags(base_url: str | None = None, timeout: float = 3.0) -> tuple[bool, list[dict[str, Any]] | None, str | None]:
    """
    Запрашивает список моделей у Ollama.
    Возвращает (ok, models_list, error_short).
    """
    url = ollama_tags_endpoint(base_url or OLLAMA_DEFAULT_BASE)
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return False, None, f"HTTP {r.status_code}"
        data = r.json()
        models = data.get("models")
        if not isinstance(models, list):
            return False, None, "bad_response"
        return True, models, None
    except requests.exceptions.Timeout:
        return False, None, "timeout"
    except requests.exceptions.ConnectionError:
        return False, None, "connection"
    except Exception as e:
        return False, None, str(e)[:80]


def is_model_present(models: list[dict[str, Any]] | None, model_name: str | None = None) -> bool:
    """True, если нужная модель есть в ответе /api/tags."""
    if not models:
        return False
    want = model_name or COREPILOT_LLM_MODEL
    for m in models:
        name = (m.get("name") or "").strip()
        if name == want or want in name:
            return True
    return False


def check_ollama_and_model(base_url: str | None = None, timeout: float = 3.0) -> tuple[bool, bool, str | None]:
    """
    Удобная сводка для старта приложения.
    Возвращает (ollama_reachable, model_ready, error_code_or_none).
    """
    ok, models, err = fetch_ollama_tags(base_url=base_url, timeout=timeout)
    if not ok:
        return False, False, err
    return True, is_model_present(models), None
