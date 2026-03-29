"""
UI translations for CorePilot AI
"""

TRANSLATIONS = {
    "ru": {
        # Left panel
        "system_info": "Системная информация",
        "presets": "Пресеты",
        "actions": "Действия",
        "show_all": "▼ Показать все действия",
        "collapse": "▲ Свернуть",
        "analyzing": "Анализ системы...",
        "actions_not_loaded": "Действия не загружены",
        "unknown": "Не удалось определить",
        # Info card labels
        "cpu": "Процессор",
        "gpu": "Видеокарта",
        "ram": "Оперативная память",
        "disk": "Системный диск",
        "power": "План электропитания",
        "startup": "Автозагрузка",
        "windows": "Версия Windows",
        # Disk / startup values
        "disk_free": "{type} • {free} GB свободно из {total} GB",
        "startup_apps": "{count} приложений",
        # Power plan values (по GUID Windows, не зависят от языка системы)
        "power_plan_balanced": "Сбалансированный",
        "power_plan_high": "Высокая производительность",
        "power_plan_ultimate": "Максимальная производительность",
        "power_plan_saver": "Энергосбережение",
        # Preset names
        "preset_gaming": "Игровой",
        "preset_streaming": "Стримерский",
        "preset_developer": "Для разработчиков",
        "preset_everyday": "Обычное использование",
        "preset_cleanup": "Очистка",
        "preset_all": "Все действия",
        # Section labels
        "section_recommended": "— Рекомендуется",
        "section_other": "— Остальные действия",
        "section_done": "— Выполнено в CorePilot",
        # Action row
        "applied_suffix": "— применено",
        "event_suffix": "— выполнялось ранее",
        "rollback_tooltip": "Откатить изменение",
        "rollback_tooltip_approx": "Откатить изменение (приблизительно)",
        # Shop
        "shop_btn": "Магазин",
        "shop_title": "Магазин",
        # Uninstall
        "uninstall_btn": "Удалить CorePilot",
        "uninstall_title": "Удалить CorePilot?",
        "uninstall_desc": "Действие необратимо. Отметьте компоненты, которые нужно убрать.",
        "uninstall_item_model": "Модель Qwen",
        "uninstall_item_model_hint": "Файлы модели, которые CorePilot использовал через Ollama.",
        "uninstall_item_ollama": "Ollama",
        "uninstall_item_ollama_hint": "Сама программа Ollama и её данные на этом компьютере.",
        "uninstall_item_app": "CorePilot",
        "uninstall_item_app_hint": "Сам CorePilot и его данные.",
        "uninstall_yes": "Да",
        "uninstall_no": "Нет",
        "uninstall_unsafe_folder_title": "Папка программы",
        "uninstall_unsafe_folder_msg": "Файлы CorePilot (.exe и папка установки) не будут удалены автоматически:\n{reason}\n\nУдалите папку вручную, если нужно:\n{path}\n\nОстальные отмеченные шаги (данные в AppData, модель, Ollama) всё равно будут запущены.",
        "uninstall_wipe_not_bundle": "Запуск из исходников — папку с .exe не трогаем.",
        "uninstall_wipe_no_marker": "Рядом с .exe нет файла CorePilot.install_root (нужна официальная сборка).",
        "uninstall_wipe_bad_folder_name": "Папка с программой должна называться CorePilot (как в инструкции по установке).",
        "uninstall_wipe_forbidden_path": "Путь похож на системный или небезопасный — автоматическое удаление отключено.",
        # Chat panel
        "chat_title": "CorePilot AI",
        "input_placeholder": "💬 Напиши сообщение или выбери действие слева...",
        "loading_msg": "💭 Анализирую систему...",
        "thinking_msg": "💭 CorePilot думает...",
        "stop_generation_tooltip": "Остановить ответ",
        "response_stopped": "Ответ остановлен.",
        "action_wait_ai": "Дождитесь ответа CorePilot",
        "basic_mode_msg": "CorePilot готов к работе.\n\n⚠️ Qwen недоступен — работаю в базовом режиме.",
        "qwen_unavailable": "⚠️ Qwen недоступен. Убедись что Ollama запущен.",
        "action_error": "⚠️ Ошибка при обработке запроса.",
        "ps_opening": "⚡ Открываю PowerShell от администратора...\nСмотри в открывшемся окне!",
        "done_applied": "Готово. Действие применено.",
        "not_applied": "Действие не было применено.",
        "rollback_opening": "⚡ Открываю PowerShell для отката{note}...\nСмотри в открывшемся окне!",
        "rollback_done": "↶ Откат применён. Твик снова доступен.",
        "rollback_cancelled": "Откат отменён.",
        "rollback_unavailable": "⚠️ Для '{title}' откат недоступен.",
        # Confirmation dialogs
        "confirm_done": "❓ Действие выполнено?",
        "confirm_rollback": "❓ Откат выполнен?",
        "yes_done": "✅ Да, выполнено",
        "yes_rollback": "✅ Да, откат выполнен",
        "no": "❌ Нет",
        # Restart banner
        "restart_required": "Для применения изменений требуется перезагрузка",
        "restart_now": "Перезагрузить сейчас",
        "restart_later": "Позже",
        "restarting": "Перезагрузка через 5 сек...",
        # Apply button
        "apply_btn": "⚡ Применить: {title}",
        # Rollback user message
        "rollback_user_msg": "↶ Откат: {title}",
        "action_user_msg": "🔧 {title}",
        # AI setup wizard
        "setup_window_title": "Настройка ИИ — CorePilot",
        "setup_title": "Настройка приложения",
        "setup_subtitle": "CorePilot использует Ollama и модель Qwen на вашем ПК. "
        "Сначала установите и запустите Ollama, затем скачайте модель одной командой.",
        "setup_ollama_section": "Шаг 1 — Ollama",
        "setup_model_section": "Шаг 2 — модель",
        "setup_ollama_help": "1) Нажмите «Скачать Ollama», установите программу.\n"
        "2) Откройте Ollama из меню «Пуск» (иконка в трее — программа работает).\n"
        "3) Нажмите «Проверить». Если не помогло — «Попробовать запустить».",
        "setup_model_help": "Скопируйте команду и вставьте в командную строку или PowerShell.",
        "setup_open_download": "Скачать Ollama",
        "setup_try_start_ollama": "Попробовать запустить",
        "setup_check": "Проверить",
        "setup_copy_command": "Копировать команду",
        "setup_close": "Закрыть",
        "setup_continue": "Продолжить",
        "setup_ollama_ok": "Ollama отвечает — связь есть.",
        "setup_ollama_wait": "Ollama пока не отвечает. Установите и запустите, затем «Проверить».",
        "setup_ollama_fail": "Не удалось связаться с Ollama: {reason}",
        "setup_model_need_ollama": "Сначала настройте Ollama (шаг 1).",
        "setup_model_ok": "Модель найдена — можно продолжать.",
        "setup_model_missing": "Модель «{model}» не найдена. Выполните команду выше и снова «Проверить».",
        "setup_err_timeout": "тайм-аут (программа не ответила вовремя).",
        "setup_err_connection": "нет связи (Ollama не запущена или блокируется сетью).",
        "setup_err_generic": "{detail}",
        "setup_ollama_start_attempt": "Попытка запуска Ollama… Подождите пару секунд и нажмите «Проверить».",
        "setup_ollama_start_fail": "Не удалось найти Ollama.exe. Откройте вручную из меню «Пуск».",
        "setup_ollama_lost": "Связь пропала: {reason}",
        "setup_copied": "Команда скопирована в буфер обмена.",
    },
    "en": {
        # Left panel
        "system_info": "System Information",
        "presets": "Presets",
        "actions": "Actions",
        "show_all": "▼ Show all actions",
        "collapse": "▲ Collapse",
        "analyzing": "Analyzing system...",
        "actions_not_loaded": "Actions not loaded",
        "unknown": "Could not determine",
        # Info card labels
        "cpu": "Processor",
        "gpu": "Graphics Card",
        "ram": "RAM",
        "disk": "System Disk",
        "power": "Power Plan",
        "startup": "Startup Apps",
        "windows": "Windows Version",
        # Disk / startup values
        "disk_free": "{type} • {free} GB free of {total} GB",
        "startup_apps": "{count} apps",
        # Power plan values (by Windows GUID — matches UI language)
        "power_plan_balanced": "Balanced",
        "power_plan_high": "High performance",
        "power_plan_ultimate": "Ultimate Performance",
        "power_plan_saver": "Power saver",
        # Preset names
        "preset_gaming": "Gaming",
        "preset_streaming": "Streaming",
        "preset_developer": "Developer",
        "preset_everyday": "Everyday Use",
        "preset_cleanup": "Cleanup",
        "preset_all": "All Actions",
        # Section labels
        "section_recommended": "— Recommended",
        "section_other": "— Other actions",
        "section_done": "— Done in CorePilot",
        # Action row
        "applied_suffix": "— applied",
        "event_suffix": "— done previously",
        "rollback_tooltip": "Rollback change",
        "rollback_tooltip_approx": "Rollback change (approximate)",
        # Shop
        "shop_btn": "Store",
        "shop_title": "Store",
        # Uninstall
        "uninstall_btn": "Uninstall CorePilot",
        "uninstall_title": "Uninstall CorePilot?",
        "uninstall_desc": "This cannot be undone. Select the components to remove.",
        "uninstall_item_model": "Qwen model",
        "uninstall_item_model_hint": "The model files CorePilot used via Ollama.",
        "uninstall_item_ollama": "Ollama",
        "uninstall_item_ollama_hint": "The Ollama app and its local data on this PC.",
        "uninstall_item_app": "CorePilot",
        "uninstall_item_app_hint": "CorePilot app and its data.",
        "uninstall_yes": "Yes",
        "uninstall_no": "No",
        "uninstall_unsafe_folder_title": "Application folder",
        "uninstall_unsafe_folder_msg": "CorePilot program files will not be removed automatically:\n{reason}\n\nDelete the folder manually if needed:\n{path}\n\nOther selected steps (AppData, model, Ollama) will still run.",
        "uninstall_wipe_not_bundle": "Running from source — the program folder is not removed.",
        "uninstall_wipe_no_marker": "CorePilot.install_root is missing next to the .exe (official bundle required).",
        "uninstall_wipe_bad_folder_name": "The folder containing the app must be named CorePilot (see install instructions).",
        "uninstall_wipe_forbidden_path": "Path looks unsafe or system — automatic folder wipe is disabled.",
        # Chat panel
        "chat_title": "CorePilot AI",
        "input_placeholder": "💬 Type a message or select an action on the left...",
        "loading_msg": "💭 Analyzing system...",
        "thinking_msg": "💭 CorePilot is thinking...",
        "stop_generation_tooltip": "Stop response",
        "response_stopped": "Response stopped.",
        "action_wait_ai": "Wait for CorePilot to finish",
        "basic_mode_msg": "CorePilot is ready.\n\n⚠️ Qwen unavailable — running in basic mode.",
        "qwen_unavailable": "⚠️ Qwen unavailable. Make sure Ollama is running.",
        "action_error": "⚠️ Error processing request.",
        "ps_opening": "⚡ Opening PowerShell as administrator...\nCheck the opened window!",
        "done_applied": "Done. Action applied.",
        "not_applied": "Action was not applied.",
        "rollback_opening": "⚡ Opening PowerShell for rollback{note}...\nCheck the opened window!",
        "rollback_done": "↶ Rollback applied. Tweak is available again.",
        "rollback_cancelled": "Rollback cancelled.",
        "rollback_unavailable": "⚠️ Rollback not available for '{title}'.",
        # Confirmation dialogs
        "confirm_done": "❓ Action completed?",
        "confirm_rollback": "❓ Rollback completed?",
        "yes_done": "✅ Yes, done",
        "yes_rollback": "✅ Yes, rolled back",
        "no": "❌ No",
        # Restart banner
        "restart_required": "A restart is required to apply changes",
        "restart_now": "Restart now",
        "restart_later": "Later",
        "restarting": "Restarting in 5 sec...",
        # Apply button
        "apply_btn": "⚡ Apply: {title}",
        # Rollback user message
        "rollback_user_msg": "↶ Rollback: {title}",
        "action_user_msg": "🔧 {title}",
        # AI setup wizard
        "setup_window_title": "AI setup — CorePilot",
        "setup_title": "Application Setup",
        "setup_subtitle": "CorePilot uses Ollama and a Qwen model on your PC. "
        "Install and start Ollama first, then download the model with one command.",
        "setup_ollama_section": "Step 1 — Ollama",
        "setup_model_section": "Step 2 — Model",
        "setup_ollama_help": "1) Click «Download Ollama» and install.\n"
        "2) Open Ollama from the Start menu (tray icon means it is running).\n"
        "3) Click «Check». If it fails, try «Try to start».",
        "setup_model_help": "Copy the command and paste it into Command Prompt or PowerShell.",
        "setup_open_download": "Download Ollama",
        "setup_try_start_ollama": "Try to start",
        "setup_check": "Check",
        "setup_copy_command": "Copy command",
        "setup_close": "Close",
        "setup_continue": "Continue",
        "setup_ollama_ok": "Ollama is responding.",
        "setup_ollama_wait": "Ollama is not responding yet. Install, start it, then «Check».",
        "setup_ollama_fail": "Cannot reach Ollama: {reason}",
        "setup_model_need_ollama": "Set up Ollama first (step 1).",
        "setup_model_ok": "Model found — you can continue.",
        "setup_model_missing": "Model «{model}» not found. Run the command above, then «Check».",
        "setup_err_timeout": "timed out (no response in time).",
        "setup_err_connection": "no connection (Ollama not running or blocked).",
        "setup_err_generic": "{detail}",
        "setup_ollama_start_attempt": "Trying to start Ollama… Wait a few seconds, then «Check».",
        "setup_ollama_start_fail": "Could not find Ollama.exe. Open it from the Start menu.",
        "setup_ollama_lost": "Connection lost: {reason}",
        "setup_copied": "Command copied to clipboard.",
    }
}


def t(key: str, **kwargs) -> str:
    """Возвращает перевод для текущего языка интерфейса."""
    from core.language import get_language
    lang = get_language()
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


# Стандартные схемы питания Windows (язык названия в WMI = язык ОС; GUID одинаковый везде)
_POWER_GUID_TO_KEY = {
    "381b4222-f694-41f0-9685-ff5bb260df2e": "power_plan_balanced",
    "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c": "power_plan_high",
    "a1841308-3541-4fab-bc81-f71556f20b4a": "power_plan_saver",
    "e9a42b02-d5df-448d-aa00-03f14749eb61": "power_plan_ultimate",
}


def power_plan_display_name(guid: str | None, wmi_localized_name: str) -> str:
    """
    Текст плана для левой панели на языке интерфейса.
    Сначала по GUID (стандартные схемы), затем по имени от Windows:
    «Максимальная производительность» после powercfg -duplicatescheme получает
    новый GUID — узнаём по характерным словам (RU/EN).
    """
    g = (guid or "").strip().lower()
    if g in _POWER_GUID_TO_KEY:
        return t(_POWER_GUID_TO_KEY[g])
    raw = (wmi_localized_name or "").strip()
    if not raw or raw.lower() == "unknown":
        return t("unknown")
    low = raw.lower()
    # Порядок важен: "Ultimate Performance" не должен попасть под «high performance»
    if "ultimate" in low or "максимальн" in low:
        return t("power_plan_ultimate")
    if "high performance" in low or "высокая производительность" in low or (
        "высокая" in low and "производительн" in low
    ):
        return t("power_plan_high")
    if "balanced" in low or "сбаланс" in low:
        return t("power_plan_balanced")
    if "power saver" in low or "энергосбереж" in low:
        return t("power_plan_saver")
    return raw
