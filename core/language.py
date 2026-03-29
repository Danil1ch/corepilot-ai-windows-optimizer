"""
Language helpers for CorePilot AI
Определение и хранение языка интерфейса / ответа модели
"""

from __future__ import annotations

from PyQt6.QtCore import QLocale
from typing import Optional

from core.memory import Memory


SUPPORTED_LANGUAGES = {"ru", "en"}


def detect_system_language() -> str:
    try:
        locale_name = QLocale.system().name().lower()
        if locale_name.startswith("ru"):
            return "ru"
    except Exception:
        pass
    return "en"


def get_language() -> str:
    try:
        saved = Memory().get_preference("language", None)
        if isinstance(saved, str) and saved in SUPPORTED_LANGUAGES:
            return saved
    except Exception:
        pass
    return detect_system_language()


def set_language(lang: str) -> str:
    normalized = (lang or "").strip().lower()
    if normalized not in SUPPORTED_LANGUAGES:
        normalized = "en"
    try:
        Memory().set_preference("language", normalized)
    except Exception:
        pass
    return normalized


def detect_message_language(user_message: Optional[str]) -> Optional[str]:
    if not user_message or not isinstance(user_message, str):
        return None
    cyrillic = sum(1 for ch in user_message if 0x0400 <= ord(ch) <= 0x04FF)
    latin = sum(1 for ch in user_message if "a" <= ch.lower() <= "z")
    if cyrillic >= 3 and cyrillic > latin:
        return "ru"
    if latin >= 3 and latin > cyrillic:
        return "en"
    return None


def resolve_response_language(user_message: Optional[str] = None) -> str:
    msg_lang = detect_message_language(user_message)
    if msg_lang in SUPPORTED_LANGUAGES:
        return msg_lang
    return get_language()


def language_name(lang: str) -> str:
    return "Russian" if lang == "ru" else "English"


from PyQt6.QtCore import QObject, pyqtSignal

class LanguageManager(QObject):
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def set_language(self, lang: str):
        normalized = set_language(lang)
        self.language_changed.emit(normalized)

    def current_language(self) -> str:
        return get_language()

lang_manager = LanguageManager()
