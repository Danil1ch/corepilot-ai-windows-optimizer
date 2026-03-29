"""CorePilot AI - Main Entry Point
Запуск приложения с splash screen

Author: Danil1ch — https://github.com/Danil1ch
"""

import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.splash_screen import SplashScreen
from ui.main_window import MainWindow
from core.ollama_setup import check_ollama_and_model
from ui.ai_setup_dialog import AiSetupDialog
from utils import get_app_qicon, windows_set_app_user_model_id


def force_foreground(hwnd):
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    ctypes.windll.user32.BringWindowToTop(hwnd)
    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE


def main():
    windows_set_app_user_model_id()
    app = QApplication(sys.argv)
    app_icon = get_app_qicon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Проверяем Ollama и модель
    ollama_ok, model_ok, _ = check_ollama_and_model()
    if not ollama_ok or not model_ok:
        dlg = AiSetupDialog()
        if dlg.exec() != AiSetupDialog.DialogCode.Accepted:
            sys.exit(0)

    # Показываем splash screen
    splash = SplashScreen()
    splash.show()

    # Создаём главное окно (но не показываем)
    main_window = MainWindow()

    # Через 2 секунды закрываем splash и показываем главное окно
    def show_main_window():
        splash.close()
        main_window.showMaximized()
        main_window.raise_()
        main_window.activateWindow()
        hwnd = int(main_window.winId())
        force_foreground(hwnd)

    QTimer.singleShot(2000, show_main_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()