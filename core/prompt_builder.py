"""
Prompt Builder - загрузка actions и формирование user prompt
"""

import json
from typing import Dict, List, Optional

from utils import data_file_path, cli_error


def load_actions(file_path: Optional[str] = None) -> List[Dict]:
    """Загружает список действий из JSON с защитой от битого файла"""
    path = file_path or data_file_path("actions.json")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            actions = data.get("actions", [])
            if not isinstance(actions, list):
                cli_error("[Actions] actions.json: поле 'actions' не является списком")
                return []
            return actions
    except json.JSONDecodeError as e:
        cli_error(f"[Actions] Битый JSON в actions.json: {e}")
        return []
    except FileNotFoundError:
        cli_error("[Actions] actions.json не найден")
        return []
    except Exception as e:
        cli_error(f"[Actions] Ошибка загрузки actions.json: {e}")
        return []


def get_available_actions_compact(refused_actions: List[str] = None, applied_actions: List[str] = None) -> List[Dict]:
    """Возвращает список действий, фильтруя отказанные и применённые"""
    actions = load_actions()
    refused = set(refused_actions or [])
    applied = set(applied_actions or [])

    return [
        a for a in actions
        if a.get("id") not in refused and a.get("id") not in applied
    ]


def build_user_prompt(user_message: str, system_data: Dict, conversation_history=None, applied_actions=None) -> str:
    """Формирует user prompt — оставлен для совместимости"""
    from core.persona import build_question_prompt
    from core.language import resolve_response_language
    lang = resolve_response_language(user_message)
    return build_question_prompt(user_message, system_data, response_language=lang)
