"""
Main Window - Главное окно приложения
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from ui.left_panel import LeftPanel
from ui.chat_panel import ChatPanel
from utils import get_app_qicon


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("CorePilot AI - Smart PC Assistant")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint)
        ic = get_app_qicon()
        if not ic.isNull():
            self.setWindowIcon(ic)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.left_panel = LeftPanel()
        self.chat_panel = ChatPanel()

        # Клик на действие слева → объяснение справа
        self.left_panel.action_clicked.connect(self.chat_panel.on_action_clicked)

        # Системная информация загружена → передаём в chat_panel для приветствия
        self.left_panel.worker.finished.connect(self.chat_panel.set_system_data)

        # Действие подтверждено как выполненное → обновляем кнопку слева
        self.chat_panel.action_applied.connect(self.left_panel.mark_action_applied)

        # Откат действия → передаём в chat_panel
        self.left_panel.rollback_clicked.connect(self.chat_panel.on_rollback_clicked)

        # Откат подтверждён → восстанавливаем кнопку слева
        self.chat_panel.rollback_confirmed.connect(self.left_panel.mark_action_rolled_back)

        # Пока ИИ генерирует ответ — блокируем твики слева
        self.chat_panel.ai_generation_changed.connect(self.left_panel.set_action_rows_ai_locked)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet("QFrame { background-color: #141414; border: none; }")

        main_layout.addWidget(self.left_panel, 3)
        main_layout.addWidget(divider)
        main_layout.addWidget(self.chat_panel, 7)

        central_widget.setLayout(main_layout)

        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")
