"""
Константы для локального ИИ: Ollama + модель CorePilot.
Один источник правды для ссылок, имени модели и команд в интерфейсе.
"""

from __future__ import annotations

# База по умолчанию (Ollama слушает 11434)
OLLAMA_DEFAULT_BASE = "http://127.0.0.1:11434"

# Прямая загрузка установщика Ollama для Windows
OLLAMA_DOWNLOAD_WINDOWS_URL = "https://ollama.com/download/OllamaSetup.exe"

# Домашняя страница (доп. справка)
OLLAMA_WEB_URL = "https://ollama.com/"

# Модель, которую ожидает CorePilot (совпадает с QwenProvider / деинсталлятором)
COREPILOT_LLM_MODEL = "qwen3.5:4b"


def ollama_tags_endpoint(base: str | None = None) -> str:
    b = (base or OLLAMA_DEFAULT_BASE).rstrip("/")
    return f"{b}/api/tags"


def pull_model_command(model: str | None = None) -> str:
    m = model or COREPILOT_LLM_MODEL
    return f"ollama pull {m}"
