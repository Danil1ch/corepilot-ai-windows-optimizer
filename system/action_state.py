"""
CorePilot Action State
Снимок того, что уже так в Windows (гибернация, службы, план питания).

Важно: раздел «Выполнено» в левой панели строится только из Memory (AppData) —
то, что пользователь отметил через CorePilot. Этот словарь для другого контекста
и не отключает кнопки «выполнено» автоматически.
"""

import re
import subprocess
import sys
import winreg
from typing import Dict


def _run_ps(command: str, timeout: int = 5) -> str:
    """Запускает PowerShell команду, возвращает stdout или пустую строку."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except Exception:
        return ""


def is_hibernate_enabled() -> bool:
    """Проверяет включена ли гибернация через реестр."""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Control\Power"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            val, _ = winreg.QueryValueEx(key, "HibernateEnabled")
            return bool(val)
    except Exception:
        return False


def is_sysmain_enabled() -> bool:
    """Проверяет запущена ли служба SysMain."""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\SysMain"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            start, _ = winreg.QueryValueEx(key, "Start")
            # 4 = disabled, 3 = manual, 2 = auto
            return start != 4
    except Exception:
        return True


def is_search_index_enabled() -> bool:
    """Проверяет запущена ли служба WSearch (индексация)."""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\WSearch"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            start, _ = winreg.QueryValueEx(key, "Start")
            return start != 4
    except Exception:
        return True


def get_active_power_plan() -> str:
    """Возвращает GUID активного плана из `powercfg /getactivescheme` (язык Windows не важен — ищем UUID в строке)."""
    try:
        kw: dict = {}
        if sys.platform == "win32":
            kw["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            timeout=8,
            **kw,
        )
        if result.returncode != 0 or not result.stdout:
            return ""
        m = re.search(
            r"([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})",
            result.stdout,
        )
        return m.group(1).lower() if m else ""
    except Exception:
        return ""


def _is_max_power_name_or_guid(power_name: str, power_guid: str) -> bool:
    """Как в recommendation_engine: стандартные GUID или типичные слова в имени (в т.ч. дубликат Ultimate)."""
    g = (power_guid or "").lower()
    n = (power_name or "").lower()
    _max_guids = (
        "e9a42b02-d5df-448d-aa00-03f14749eb61",
        "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
    )
    if g in _max_guids:
        return True
    return (
        "максимальная" in n
        or "ultimate" in n
        or "high performance" in n
        or "высокая производительность" in n
    )


def _is_balanced_name_or_guid(power_name: str, power_guid: str) -> bool:
    _bal = "381b4222-f694-41f0-9685-ff5bb260df2e"
    g = (power_guid or "").lower()
    n = (power_name or "").lower()
    if g == _bal:
        return True
    return "сбалансир" in n or "balanced" in n


def load_action_states() -> Dict[str, bool]:
    """
    True = в Windows это уже в таком состоянии (не путать с блоком «Выполнено» в UI).
    """
    states = {}

    # hibernate_off: применено если гибернация ВЫКЛЮЧЕНА
    states["hibernate_off"] = not is_hibernate_enabled()

    # disable_sysmain: применено если служба ОТКЛЮЧЕНА
    states["disable_sysmain"] = not is_sysmain_enabled()

    # disable_search_index: применено если служба ОТКЛЮЧЕНА
    states["disable_search_index"] = not is_search_index_enabled()

    power_name, power_guid = "", ""
    try:
        from system.system_info import get_power_plan_info
        power_name, power_guid = get_power_plan_info()
    except Exception:
        pass

    active_ps = get_active_power_plan()

    # Имя+GUID из WMI; если GUID нет — только powercfg (как раньше, плюс High performance GUID)
    states["power_max"] = _is_max_power_name_or_guid(power_name, power_guid) or (
        not (power_guid or "").strip()
        and (
            "e9a42b02-d5df-448d-aa00-03f14749eb61" in active_ps
            or "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" in active_ps
        )
    )

    states["power_balanced"] = _is_balanced_name_or_guid(power_name, power_guid) or (
        not (power_guid or "").strip()
        and "381b4222-f694-41f0-9685-ff5bb260df2e" in active_ps
    )

    return states
