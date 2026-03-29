"""
CorePilot Uninstaller
Порядок при полном наборе: ollama rm модель → остановка Ollama → деинсталлятор → папки Ollama → данные в AppData.

Copyright (c) Danil1ch — https://github.com/Danil1ch
Папка с .exe удаляется отложенным bat только если безопасно: маркер CorePilot.install_root и имя папки CorePilot.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import winreg
from dataclasses import dataclass

from core.ai_stack_constants import COREPILOT_LLM_MODEL


# Должен лежать рядом с CorePilot.exe в официальной zip / сборке (см. assets/CorePilot.install_root).
INSTALL_ROOT_MARKER = "CorePilot.install_root"


def is_exe() -> bool:
    """True, если запущен собранный PyInstaller-бандл (есть _MEIPASS)."""
    return getattr(sys, "_MEIPASS", None) is not None


def get_bundle_exe_directory() -> str | None:
    """Каталог, в котором лежит .exe пользователя (не временный _MEIPASS)."""
    if not is_exe():
        return None
    d = os.path.dirname(os.path.abspath(sys.executable))
    return d if d and os.path.isdir(d) else None


def _forbidden_path_prefixes_norm() -> list[str]:
    """Запрещаем дерево Windows; Program Files не блокируем — туда может ставить инсталлятор."""
    out: list[str] = []
    windir = os.environ.get("WINDIR", "")
    if windir:
        w = os.path.normcase(os.path.normpath(windir))
        out.append(w)
    return out


def _is_forbidden_install_location(norm_dir: str) -> bool:
    for prefix in _forbidden_path_prefixes_norm():
        if not prefix:
            continue
        if norm_dir == prefix or norm_dir.startswith(prefix + os.sep):
            return True
    up = os.environ.get("USERPROFILE", "")
    if up:
        nu = os.path.normcase(os.path.normpath(up))
        if norm_dir == nu:
            return True
    return False


def _is_drive_root(path_norm: str) -> bool:
    p = os.path.normpath(path_norm)
    if len(p) == 3 and p[1:3] == ":\\":
        return True
    parent = os.path.dirname(p)
    return parent == p


@dataclass(frozen=True)
class InstallFolderWipeInfo:
    """Можно ли автоматически снести папку с exe отложенным bat после выхода процесса."""

    safe: bool
    reason_key: str | None  # ключ в translations.py; None если safe
    install_dir: str | None


def install_folder_wipe_info() -> InstallFolderWipeInfo:
    app_dir = get_bundle_exe_directory()
    if not app_dir:
        return InstallFolderWipeInfo(False, "uninstall_wipe_not_bundle", None)
    norm = os.path.normcase(os.path.normpath(app_dir))
    if _is_drive_root(norm):
        return InstallFolderWipeInfo(False, "uninstall_wipe_forbidden_path", app_dir)
    if _is_forbidden_install_location(norm):
        return InstallFolderWipeInfo(False, "uninstall_wipe_forbidden_path", app_dir)
    base = os.path.basename(norm.rstrip(os.sep))
    if base.lower() != "corepilot":
        return InstallFolderWipeInfo(False, "uninstall_wipe_bad_folder_name", app_dir)
    marker = os.path.join(app_dir, INSTALL_ROOT_MARKER)
    if not os.path.isfile(marker):
        return InstallFolderWipeInfo(False, "uninstall_wipe_no_marker", app_dir)
    return InstallFolderWipeInfo(True, None, app_dir)


def _find_ollama_uninstall_string() -> str | None:
    """Ищет UninstallString для Ollama в реестре."""
    keys_to_check = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for key_path in keys_to_check:
            try:
                key = winreg.OpenKey(root, key_path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if "ollama" in str(display_name).lower():
                                uninstall_str = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                return str(uninstall_str).strip('"')
                        except FileNotFoundError:
                            pass
                        finally:
                            subkey.Close()
                    except OSError:
                        pass
                key.Close()
            except OSError:
                pass
    return None


def build_uninstall_script(
    remove_model: bool = True,
    remove_ollama: bool = True,
    remove_app: bool = True,
) -> str:
    """Генерирует PowerShell скрипт по выбранным компонентам."""
    if not remove_model and not remove_ollama and not remove_app:
        return (
            '$ErrorActionPreference = "SilentlyContinue"\n'
            'Write-Host "[CorePilot] Нечего удалять." -ForegroundColor DarkYellow\n'
            "Start-Sleep -Seconds 2\n"
        )

    uninstall_str = _find_ollama_uninstall_string() if remove_ollama else None
    model = COREPILOT_LLM_MODEL

    lines = [
        '$ErrorActionPreference = "SilentlyContinue"',
        'Write-Host "[CorePilot] Начинаем удаление..." -ForegroundColor Cyan',
        "",
    ]

    if remove_model:
        lines += [
            'Write-Host "[Модель] Удаление модели Qwen из Ollama..." -ForegroundColor Yellow',
            "$_rmOllama = $null",
            'foreach ($_p in @(',
            '  "$env:LOCALAPPDATA\\Programs\\Ollama\\ollama.exe",',
            '  "$env:LOCALAPPDATA\\Programs\\Ollama\\Ollama.exe"',
            ")) {",
            "  if (Test-Path -LiteralPath $_p) { $_rmOllama = $_p; break }",
            "}",
            "if ($_rmOllama) {",
            f'  & $_rmOllama rm {model} 2>$null',
            "} else {",
            f"  ollama rm {model} 2>$null",
            "}",
            'Write-Host "      Готово" -ForegroundColor Green',
            "",
        ]

    if remove_ollama:
        lines += [
            'Write-Host "[Ollama] Остановка процесса..." -ForegroundColor Yellow',
            "taskkill /f /im ollama.exe 2>$null",
            "Start-Sleep -Seconds 1",
            'Write-Host "      Готово" -ForegroundColor Green',
            "",
            'Write-Host "[Ollama] Запуск деинсталлятора..." -ForegroundColor Yellow',
        ]
        if uninstall_str:
            lines.append(
                f'Start-Process -FilePath "{uninstall_str}" '
                f'-ArgumentList "/VERYSILENT /NORESTART" -Wait 2>$null'
            )
        else:
            lines.append(
                'Write-Host "      UninstallString не найден, пропускаем" -ForegroundColor DarkYellow'
            )
        lines += [
            'Write-Host "      Готово" -ForegroundColor Green',
            "",
            'Write-Host "[Ollama] Очистка папок..." -ForegroundColor Yellow',
            r'if (Test-Path "$env:USERPROFILE\.ollama") '
            r'{ Remove-Item -Recurse -Force "$env:USERPROFILE\.ollama" }',
            r'if (Test-Path "$env:LOCALAPPDATA\Programs\Ollama") '
            r'{ Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\Ollama" }',
            r'if (Test-Path "$env:LOCALAPPDATA\Ollama") '
            r'{ Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Ollama" }',
            r'if (Test-Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Ollama") '
            r'{ Remove-Item -Recurse -Force '
            r'"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Ollama" }',
            'Write-Host "      Готово" -ForegroundColor Green',
            "",
        ]

    if remove_app:
        lines += [
            'Write-Host "[CorePilot] Очистка данных в AppData..." -ForegroundColor Yellow',
            r'if (Test-Path "$env:LOCALAPPDATA\CorePilot") '
            r'{ Remove-Item -Recurse -Force "$env:LOCALAPPDATA\CorePilot" }',
            'Write-Host "      Готово" -ForegroundColor Green',
            "",
        ]

    lines += [
        'Write-Host ""',
        'Write-Host "[CorePilot] Готово." -ForegroundColor Cyan',
        "Start-Sleep -Seconds 2",
    ]

    return "\n".join(lines)


def run_uninstall(
    remove_model: bool = True,
    remove_ollama: bool = True,
    remove_app: bool = True,
    app_instance=None,
    schedule_program_folder_wipe: bool = True,
):
    """
    Создаёт PS1, при безопасном пути — bat удаления папки с exe после выхода.
    schedule_program_folder_wipe: False — не добавлять bat (данные AppData в PS всё равно чистятся при remove_app).
    """
    if not remove_model and not remove_ollama and not remove_app:
        return

    script = build_uninstall_script(
        remove_model=remove_model,
        remove_ollama=remove_ollama,
        remove_app=remove_app,
    )

    tmp_ps1 = tempfile.NamedTemporaryFile(mode="wb", suffix=".ps1", delete=False)
    tmp_ps1.write(b"\xef\xbb\xbf")
    tmp_ps1.write(script.encode("utf-8"))
    tmp_ps1.close()

    do_wipe = (
        remove_app
        and is_exe()
        and schedule_program_folder_wipe
    )
    if do_wipe:
        info = install_folder_wipe_info()
        if not info.safe or not info.install_dir:
            do_wipe = False
        else:
            app_dir = info.install_dir
            # Экранирование для cmd: длинные пути в кавычках
            bat_content = f"""@echo off
timeout /t 3 /nobreak >nul
rmdir /s /q "{app_dir}"
del "%~f0"
"""
            tmp_bat = tempfile.NamedTemporaryFile(
                mode="w", suffix=".bat", delete=False, encoding="utf-8"
            )
            tmp_bat.write(bat_content)
            tmp_bat.close()

            with open(tmp_ps1.name, "ab") as f:
                f.write(
                    f'\nWrite-Host "[CorePilot] Папка программы будет удалена после выхода..." -ForegroundColor DarkYellow\n'
                    f'Start-Process -FilePath "{tmp_bat.name}"\n'.encode("utf-8")
                )

    subprocess.Popen(
        [
            "powershell",
            "-Command",
            f'Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File {tmp_ps1.name}" -Verb RunAs',
        ]
    )

    if remove_app:
        if app_instance:
            app_instance.quit()
        else:
            sys.exit(0)
