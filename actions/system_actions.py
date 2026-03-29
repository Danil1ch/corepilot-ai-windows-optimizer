"""
Actions - Модуль выполнения действий по оптимизации
"""

import subprocess
import os
import shutil
import json
from typing import Dict, Tuple, Any

from utils import data_file_path, cli_error


def is_tweak_action(action: dict[str, Any] | None) -> bool:
    """Твик: PowerShell-команда без repeatable (обычно окно администратора). Остальные клики во время ответа ИИ не блокируем."""
    if not action:
        return False
    if action.get("action_type", "powershell") != "powershell":
        return False
    return not action.get("repeatable", False)


def load_actions_db() -> Dict:
    """Загружает базу действий из actions.json"""
    try:
        with open(data_file_path("actions.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            return {action["id"]: action for action in data.get("actions", [])}
    except Exception as e:
        cli_error(f"[Actions] Ошибка загрузки actions.json: {e}")
        return {}


def execute_powershell_command(command: str, action_title: str = "Действие") -> Tuple[bool, str]:
    """
    Универсальное выполнение PowerShell команды
    
    Args:
        command: PowerShell команда для выполнения
        action_title: Название действия для сообщения
    
    Returns:
        (success: bool, message: str)
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, f"✅ {action_title} выполнено успешно"
        else:
            err = (result.stderr or "").strip()
            if err:
                cli_error(f"[Actions] {action_title} (код {result.returncode}): {err[:400]}")
            # Проверяем типичные ошибки
            if "Access is denied" in result.stderr or "отказано в доступе" in result.stderr.lower():
                return False, f"❌ Требуются права администратора для выполнения '{action_title}'"
            elif result.stderr:
                return False, f"❌ Ошибка: {result.stderr[:200]}"
            else:
                return True, f"✅ {action_title} выполнено (с предупреждениями)"
    
    except subprocess.TimeoutExpired:
        cli_error(f"[Actions] Таймаут: {action_title}")
        return False, f"❌ Таймаут выполнения '{action_title}' (>60 сек)"
    except Exception as e:
        cli_error(f"[Actions] Ошибка выполнения '{action_title}': {e}")
        return False, f"❌ Ошибка выполнения: {str(e)}"


class SystemActions:
    """Класс для выполнения действий по оптимизации системы"""
    
    @staticmethod
    def open_startup_manager() -> Tuple[bool, str]:
        """Открывает диспетчер задач на вкладке автозагрузки"""
        try:
            subprocess.Popen(["taskmgr", "/0", "/startup"])
            return True, "Открыт Диспетчер задач → Автозагрузка"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def set_high_performance_plan() -> Tuple[bool, str]:
        """Переключает на план максимальной производительности (Ultimate Performance)"""
        try:
            # Сначала активируем скрытую схему Ultimate Performance
            subprocess.run(
                ["powercfg", "-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"],
                capture_output=True, text=True
            )
            result = subprocess.run(
                ["powercfg", "/setactive", "e9a42b02-d5df-448d-aa00-03f14749eb61"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return True, "✅ План питания изменён на 'Максимальная производительность'"
            else:
                return False, "❌ Не удалось изменить план питания"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def set_balanced_plan() -> Tuple[bool, str]:
        """Переключает на сбалансированный план"""
        try:
            # GUID сбалансированного плана
            result = subprocess.run(
                ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, "План питания изменён на 'Сбалансированный'"
            else:
                return False, "Не удалось изменить план питания"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def open_disk_cleanup() -> Tuple[bool, str]:
        """Открывает утилиту очистки диска"""
        try:
            subprocess.Popen(["cleanmgr", "/d", "C:"])
            return True, "Открыта утилита очистки диска"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def clean_temp_files() -> Tuple[bool, str]:
        """Очищает временные файлы Windows"""
        try:
            temp_paths = [
                os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp')),
                "C:\\Windows\\Temp"
            ]
            
            deleted_count = 0
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    for item in os.listdir(temp_path):
                        item_path = os.path.join(temp_path, item)
                        try:
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                                deleted_count += 1
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                                deleted_count += 1
                        except:
                            pass  # Пропускаем файлы которые используются
            
            return True, f"Очищено временных файлов: {deleted_count}"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def empty_recycle_bin() -> Tuple[bool, str]:
        """Очищает корзину"""
        try:
            # Используем PowerShell для очистки корзины
            subprocess.run(
                ["powershell", "-Command", "Clear-RecycleBin -Force"],
                capture_output=True,
                text=True
            )
            return True, "Корзина очищена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def open_power_settings() -> Tuple[bool, str]:
        """Открывает настройки электропитания"""
        try:
            subprocess.Popen(["control", "powercfg.cpl"])
            return True, "Открыты настройки электропитания"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def open_game_mode_settings() -> Tuple[bool, str]:
        """Открывает настройки игрового режима Windows"""
        try:
            subprocess.Popen(["start", "ms-settings:gaming-gamemode"], shell=True)
            return True, "Открыты настройки игрового режима"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def run_dism_cleanup() -> Tuple[bool, str]:
        """Запускает DISM cleanup (требует прав администратора)"""
        try:
            result = subprocess.run(
                ["dism", "/online", "/cleanup-image", "/startcomponentcleanup"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, "DISM cleanup выполнен успешно"
            else:
                return False, "Требуются права администратора"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def compress_system() -> Tuple[bool, str]:
        """Включает CompactOS (сжатие системных файлов)"""
        try:
            result = subprocess.run(
                ["compact.exe", "/compactos:always"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, "CompactOS включен. Освобождено 2-3GB места"
            else:
                return False, "Требуются права администратора"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def clean_old_drivers() -> Tuple[bool, str]:
        """Очищает старые драйвера через pnputil"""
        try:
            # Получаем список сторонних драйверов
            result = subprocess.run(
                ["pnputil", "/enum-drivers"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Открываем Device Manager для ручной очистки
                subprocess.Popen(["devmgmt.msc"])
                return True, "Открыт Диспетчер устройств. Используй Display Driver Uninstaller для полной очистки"
            else:
                return False, "Не удалось получить список драйверов"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def disable_telemetry_deep() -> Tuple[bool, str]:
        """Отключает телеметрию Windows"""
        try:
            # Отключаем службу телеметрии
            subprocess.run(
                ["sc", "stop", "DiagTrack"],
                capture_output=True
            )
            subprocess.run(
                ["sc", "config", "DiagTrack", "start=disabled"],
                capture_output=True
            )
            
            # Отключаем задачи телеметрии через PowerShell
            subprocess.run(
                ["powershell", "-Command", 
                 "Get-ScheduledTask -TaskPath '\\Microsoft\\Windows\\Customer Experience Improvement Program\\' | Disable-ScheduledTask"],
                capture_output=True
            )
            
            return True, "Телеметрия Windows отключена. Требуется перезагрузка"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def limit_startup_high() -> Tuple[bool, str]:
        """Открывает автозагрузку с рекомендациями"""
        try:
            subprocess.Popen(["taskmgr", "/0", "/startup"])
            return True, "Открыт Диспетчер задач → Автозагрузка. Отключи Discord, Steam, Spotify для экономии RAM"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    @staticmethod
    def recommend_driver_update() -> Tuple[bool, str]:
        """Открывает ссылку на обновление драйверов"""
        try:
            # Открываем Device Manager
            subprocess.Popen(["devmgmt.msc"])
            return True, "Открыт Диспетчер устройств. Обнови драйвера видеокарты через сайт NVIDIA/AMD"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"


# Маппинг action_id -> функция
ACTION_HANDLERS = {
    "open_startup_manager": SystemActions.open_startup_manager,
    "recommend_startup_cleanup": SystemActions.open_startup_manager,
    "show_startup_apps": SystemActions.open_startup_manager,
    
    "switch_to_high_performance": SystemActions.set_high_performance_plan,
    "recommend_high_performance_plan": SystemActions.set_high_performance_plan,
    "power_max": SystemActions.set_high_performance_plan,
    
    "switch_to_balanced": SystemActions.set_balanced_plan,
    "recommend_balanced_plan": SystemActions.set_balanced_plan,
    "power_balanced": SystemActions.set_balanced_plan,
    
    "open_disk_cleanup": SystemActions.open_disk_cleanup,
    "recommend_disk_cleanup": SystemActions.open_disk_cleanup,
    
    "clean_temp_files": SystemActions.clean_temp_files,
    "empty_recycle_bin": SystemActions.empty_recycle_bin,
    
    "explain_power_plan": SystemActions.open_power_settings,
    "recommend_game_mode_check": SystemActions.open_game_mode_settings,
    
    "deep_cleanup_winsxs": SystemActions.run_dism_cleanup,
    
    # Новые действия
    "compress_system": SystemActions.compress_system,
    "clean_old_drivers": SystemActions.clean_old_drivers,
    "disable_telemetry_deep": SystemActions.disable_telemetry_deep,
    "limit_startup_high": SystemActions.limit_startup_high,
    "recommend_driver_update": SystemActions.recommend_driver_update,
}


def execute_action(action_id: str) -> Tuple[bool, str]:
    """
    Выполняет действие по его ID
    
    Returns:
        (success: bool, message: str)
    """
    # Сначала проверяем хардкодные функции
    handler = ACTION_HANDLERS.get(action_id)
    if handler:
        return handler()
    
    # Если нет хардкодной функции → ищем в actions.json
    actions_db = load_actions_db()
    action = actions_db.get(action_id)
    
    if not action:
        return False, f"❌ Действие '{action_id}' не найдено"
    
    # Проверяем, есть ли команда
    command = action.get("command")
    if not command:
        # Это recommendation без команды (например, recommend_startup_cleanup)
        return True, f"ℹ️ {action.get('title_ru', action_id)}: {action.get('desc_ru', 'Смотри рекомендацию выше')}"
    
    # Выполняем команду через PowerShell
    title = action.get("title_ru", action_id)
    return execute_powershell_command(command, title)
