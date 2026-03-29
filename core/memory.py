"""
Система памяти CorePilot AI
Отслеживает действия, отказы и предпочтения пользователя
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from utils import data_file_path

LEGACY_STATE_FILE = data_file_path("user_state.json")


def _get_state_path() -> str:
    """Возвращает путь к user_state.json в AppData/Local/CorePilot"""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "CorePilot", "user_state.json")


USER_STATE_FILE = _get_state_path()


class Memory:
    def __init__(self):
        self._migrate_legacy()
        self.state = self.load_state()
        self._cleanup_invalid_ids()

    def _cleanup_invalid_ids(self):
        """Удаляет из completed_actions id которых нет в actions.json. Перезаписывает файл если были удалены."""
        try:
            from core.prompt_builder import load_actions
            valid_ids = {a["id"] for a in load_actions()}
            if not valid_ids:
                return
            completed = self.state.get("completed_actions", {})
            cleaned = {k: v for k, v in completed.items() if k in valid_ids}
            if len(cleaned) != len(completed):
                self.state["completed_actions"] = cleaned
                self.save_state()
        except Exception:
            pass

    def _migrate_legacy(self):
        """Переносит старый user_state.json из data/ в AppData если он там есть"""
        if not os.path.exists(LEGACY_STATE_FILE):
            return
        if os.path.exists(USER_STATE_FILE):
            return
        # Мигрируем только чистую структуру — без completed_actions
        try:
            os.makedirs(os.path.dirname(USER_STATE_FILE), exist_ok=True)
            with open(LEGACY_STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Не переносим completed_actions — они могут быть из старой архитектуры
            data["completed_actions"] = {}
            with open(USER_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def load_state(self) -> Dict:
        """Загружает состояние пользователя из файла"""
        if os.path.exists(USER_STATE_FILE):
            try:
                with open(USER_STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "suggested_actions": {},
            "refused_actions": {},
            "completed_actions": {},
            "preferences": {},
            "last_analysis": None
        }

    def save_state(self):
        """Сохраняет состояние в файл"""
        try:
            os.makedirs(os.path.dirname(USER_STATE_FILE), exist_ok=True)
            with open(USER_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def mark_suggested(self, action_id: str):
        """Отмечает что действие было предложено"""
        if action_id not in self.state["suggested_actions"]:
            self.state["suggested_actions"][action_id] = {
                "count": 0,
                "first_suggested": datetime.now().isoformat(),
                "last_suggested": None
            }
        
        self.state["suggested_actions"][action_id]["count"] += 1
        self.state["suggested_actions"][action_id]["last_suggested"] = datetime.now().isoformat()
        self.save_state()
    
    def mark_refused(self, action_id: str, reason: Optional[str] = None):
        """Отмечает что пользователь отказался от действия"""
        if action_id not in self.state["refused_actions"]:
            self.state["refused_actions"][action_id] = {
                "count": 0,
                "first_refused": datetime.now().isoformat(),
                "last_refused": None,
                "reasons": []
            }
        
        self.state["refused_actions"][action_id]["count"] += 1
        self.state["refused_actions"][action_id]["last_refused"] = datetime.now().isoformat()
        
        if reason:
            self.state["refused_actions"][action_id]["reasons"].append(reason)
        
        self.save_state()
    
    def mark_completed(self, action_id: str):
        """Отмечает что действие было выполнено"""
        self.state["completed_actions"][action_id] = {
            "completed_at": datetime.now().isoformat()
        }
        self.save_state()

    def unmark_completed(self, action_id: str):
        """Убирает действие из выполненных (после отката)"""
        self.state["completed_actions"].pop(action_id, None)
        self.save_state()
    
    def is_refused(self, action_id: str) -> bool:
        """Проверяет отказывался ли пользователь от действия"""
        return action_id in self.state["refused_actions"]
    
    def is_completed(self, action_id: str) -> bool:
        """Проверяет было ли действие выполнено"""
        return action_id in self.state["completed_actions"]
    
    def get_refusal_count(self, action_id: str) -> int:
        """Возвращает количество отказов от действия"""
        if action_id in self.state["refused_actions"]:
            return self.state["refused_actions"][action_id]["count"]
        return 0
    
    def should_suggest(self, action_id: str) -> bool:
        """Определяет стоит ли предлагать действие"""
        # Если уже выполнено — не предлагать
        if self.is_completed(action_id):
            return False
        
        # Если отказывался больше 2 раз — не предлагать
        if self.get_refusal_count(action_id) >= 2:
            return False
        
        return True
    
    def set_preference(self, key: str, value):
        """Сохраняет предпочтение пользователя"""
        self.state["preferences"][key] = value
        self.save_state()
    
    def get_preference(self, key: str, default=None):
        """Получает предпочтение пользователя"""
        return self.state["preferences"].get(key, default)
    
    def update_last_analysis(self, system_data: Dict):
        """Обновляет данные последнего анализа"""
        self.state["last_analysis"] = {
            "timestamp": datetime.now().isoformat(),
            "system_data": system_data
        }
        self.save_state()
    
    def get_last_analysis(self) -> Optional[Dict]:
        """Возвращает данные последнего анализа"""
        return self.state.get("last_analysis")
    
    @property
    def refused_actions(self) -> List[str]:
        """Возвращает список отклонённых действий"""
        return list(self.state.get("refused_actions", {}).keys())
    
    @property
    def completed_actions(self) -> List[str]:
        """Возвращает список выполненных действий"""
        return list(self.state.get("completed_actions", {}).keys())
    
    @property
    def suggested_actions(self) -> List[str]:
        """Возвращает список предложенных действий"""
        return list(self.state.get("suggested_actions", {}).keys())
    
    def reset(self):
        """Сбрасывает всю память (для тестирования)"""
        self.state = {
            "suggested_actions": {},
            "refused_actions": {},
            "completed_actions": {},
            "preferences": {},
            "last_analysis": None
        }
        self.save_state()
