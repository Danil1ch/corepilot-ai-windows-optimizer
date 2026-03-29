"""
Chat Panel - Панель чата с AI
Qwen только объясняет действия и отвечает на вопросы
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QScrollArea, QLabel, QFrame,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QIcon, QKeyEvent, QPainter, QColor, QLinearGradient, QPainterPath
from PyQt6.QtSvgWidgets import QSvgWidget
import os
import json
import threading
from utils import resource_path
from typing import Dict
from core import Memory, QwenProvider
from core.persona import build_greeting_prompt, build_explanation_prompt, build_question_prompt
from core.language import get_language, resolve_response_language
from core.translations import t
from actions import execute_action
from ui.qwen_thread import QwenThread


class LangSwitcher(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ru_active = True
        self._shimmer = 0.0
        self.setFixedSize(80, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"shimmer")
        self._anim.setDuration(600)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def get_shimmer(self): return self._shimmer
    def set_shimmer(self, v):
        self._shimmer = v
        self.update()
    shimmer = pyqtProperty(float, get_shimmer, set_shimmer)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        half = w // 2

        # Фон контейнера
        bg = QPainterPath()
        bg.addRoundedRect(0, 0, w, h, 8, 8)
        p.fillPath(bg, QColor("#1e1e1e"))

        for i, label in enumerate(["RU", "EN"]):
            is_active = (i == 0) == self._ru_active
            x = i * half

            clip = QPainterPath()
            if i == 0:
                clip.addRoundedRect(1, 1, half - 1, h - 2, 7, 7)
            else:
                clip.addRoundedRect(half, 1, half - 1, h - 2, 7, 7)
            p.setClipPath(clip)

            if is_active:
                # Базовый фиолетовый
                p.fillRect(x, 1, half - 1, h - 2, QColor("#6B46C1"))
                # Shimmer — яркая полоса скользит слева направо при переключении
                if self._shimmer > 0:
                    sx = x + int((half - 1) * self._shimmer) - 20
                    shimmer_grad = QLinearGradient(sx, 0, sx + 40, 0)
                    shimmer_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
                    shimmer_grad.setColorAt(0.5, QColor(255, 255, 255, 90))
                    shimmer_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                    p.fillRect(x, 1, half - 1, h - 2, shimmer_grad)
                # Блик сверху — эффект "поднято"
                top_light = QLinearGradient(0, 1, 0, 8)
                top_light.setColorAt(0, QColor(255, 255, 255, 55))
                top_light.setColorAt(1, QColor(255, 255, 255, 0))
                p.fillRect(x, 1, half - 1, 8, top_light)
            else:
                # Утоплено — тёмный фон
                p.fillRect(x, 1, half - 1, h - 2, QColor("#161616"))
                # Тень сверху — эффект "вдавлено"
                top_shadow = QLinearGradient(0, 1, 0, 9)
                top_shadow.setColorAt(0, QColor(0, 0, 0, 100))
                top_shadow.setColorAt(1, QColor(0, 0, 0, 0))
                p.fillRect(x, 1, half - 1, 9, top_shadow)

            p.setClipping(False)

            p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold if is_active else QFont.Weight.Normal))
            p.setPen(QColor("#ffffff") if is_active else QColor("#888888"))
            p.drawText(x, 0, half, h, Qt.AlignmentFlag.AlignCenter, label)

        # Разделитель
        p.setPen(QColor("#3a3a3a"))
        p.drawLine(half, 4, half, h - 4)

        # Обводка поверх всего
        p.setClipping(False)
        p.setPen(QColor("#6B46C1"))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 8, 8)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._ru_active = not self._ru_active
        from core.language import lang_manager
        lang_manager.set_language("ru" if self._ru_active else "en")
        self._shimmer = 0.0
        self._anim.stop()
        self._anim.start()
        self.update()


class ChatPanel(QWidget):
    action_applied = pyqtSignal(str)   # action_id
    rollback_confirmed = pyqtSignal(str)  # action_id
    ai_generation_changed = pyqtSignal(bool)  # True — идёт ответ ИИ (блок твиков слева)

    def __init__(self):
        super().__init__()
        self.memory = Memory()
        self.qwen_provider = QwenProvider()
        self.thinking_widget = None
        self._thinking_label = None
        self.qwen_thread = None
        self._cancel_event = None
        self._generation_seq = 0
        self._ai_busy = False
        self._generation_can_stop = False
        self._input_shows_stop = False
        self._send_icon_path = ""
        self._stop_icon_path = ""
        self.system_data = {}
        self.last_user_message = ""
        self.pending_action = None
        self.pending_restart = False
        self.init_ui()

    def set_system_data(self, data: dict):
        """Получает данные системы от left_panel после загрузки"""
        self.system_data = data
        self._send_greeting()

    def _send_greeting(self):
        """Отправляет приветственное сообщение после загрузки системы"""
        self._remove_stretch()
        while self.messages_layout.count() > 0:
            item = self.messages_layout.itemAt(0)
            if item and item.widget():
                item.widget().deleteLater()
                self.messages_layout.removeItem(item)
            else:
                break

        # Получаем top-3 рекомендации для контекста приветствия
        from core.prompt_builder import load_actions
        from core.recommendation_engine import get_recommendations
        actions = load_actions()
        top_actions = []
        if actions:
            result = get_recommendations(self.system_data, actions, self.memory.completed_actions)
            top_actions = result["recommended"][:3]

        if not self.qwen_provider.is_available():
            hints = [self._get_action_title(a) for a in top_actions if a.get("title_ru")]
            hint_str = ""
            if hints:
                hint_str = f"\n\nПриоритетные действия: {', '.join(hints)}."
            self._add_ai_message(t("basic_mode_msg"))
            return

        system_prompt = build_greeting_prompt(self.system_data, response_language=get_language())
        self._run_qwen(system_prompt, "Напиши приветствие.", mode="greeting")

    def on_rollback_clicked(self, action: dict):
        action_id = action.get("id", "")
        rollback_cmd = action.get("rollback_command")
        title = self._get_action_title(action)

        if not rollback_cmd:
            self._add_ai_message(t("rollback_unavailable", title=title))
            return

        self._add_user_message(t("rollback_user_msg", title=title))

        import tempfile, subprocess
        script_lines = [
            f'Write-Host "[CorePilot] Откат: {action_id}..." -ForegroundColor Cyan',
            rollback_cmd,
            f'Write-Host "[CorePilot] Готово" -ForegroundColor Green',
            'Read-Host "Press Enter to close"',
        ]
        script = "\n".join(script_lines)
        tmp = tempfile.NamedTemporaryFile(mode='wb', suffix='.ps1', delete=False)
        tmp.write(b'\xef\xbb\xbf')
        tmp.write(script.encode('utf-8'))
        tmp.close()

        subprocess.Popen([
            'powershell', '-Command',
            f'Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File {tmp.name}" -Verb RunAs'
        ])

        best_effort = action.get("rollback_best_effort", False)
        note = " (approximate rollback)" if best_effort else ""
        self._add_ai_message(t("rollback_opening", note=note))
        QTimer.singleShot(500, lambda: self._ask_rollback_confirmation(action))

    def _ask_rollback_confirmation(self, action: dict):
        self._remove_stretch()
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        avatar_container.setStyleSheet("background: transparent; border: none;")
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_icon = QSvgWidget(resource_path(os.path.join("assets", "icons", "bot.svg")))
        bot_icon.setFixedSize(28, 28)
        bot_icon.setStyleSheet("background: transparent; border: none;")
        avatar_layout.addWidget(bot_icon, 0, Qt.AlignmentFlag.AlignCenter)
        avatar_container.setLayout(avatar_layout)

        content = QVBoxLayout()
        content.setSpacing(8)

        bubble = QLabel(t("confirm_rollback"))
        bubble.setFont(QFont("Segoe UI", 11))
        bubble.setMinimumWidth(300)
        bubble.setMaximumWidth(560)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a; border-radius: 16px;
                border: 1px solid #3a3a3a; padding: 14px 18px; color: #ffffff;
            }
        """)
        content.addWidget(bubble)

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(8)

        yes_btn = QPushButton(t("yes_rollback"))
        yes_btn.setFont(QFont("Segoe UI", 10))
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setStyleSheet("""
            QPushButton { background: #166534; border: none; border-radius: 8px; padding: 8px 16px; color: #ffffff; }
            QPushButton:hover { background: #15803d; }
        """)

        no_btn = QPushButton(t("no"))
        no_btn.setFont(QFont("Segoe UI", 10))
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setStyleSheet("""
            QPushButton { background: #3a3a3a; border: none; border-radius: 8px; padding: 8px 16px; color: #ffffff; }
            QPushButton:hover { background: #4a4a4a; }
        """)

        def on_yes():
            container.setVisible(False)
            self.rollback_confirmed.emit(action["id"])
            self._add_ai_message(t("rollback_done"))

        def on_no():
            container.setVisible(False)
            self._add_ai_message(t("rollback_cancelled"))

        yes_btn.clicked.connect(on_yes)
        no_btn.clicked.connect(on_no)
        btns_layout.addWidget(yes_btn)
        btns_layout.addWidget(no_btn)
        btns_layout.addStretch()
        content.addLayout(btns_layout)

        layout.addWidget(avatar_container, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(content)
        layout.addStretch()
        container.setLayout(layout)
        self.messages_layout.addWidget(container)
        self.messages_layout.addStretch()
        QTimer.singleShot(50, self._scroll_bottom)

    def _get_action_title(self, action: dict) -> str:
        lang = get_language()
        if lang == "en":
            return action.get("title_en") or action.get("title_ru", action.get("id", ""))
        return action.get("title_ru", action.get("id", ""))

    def on_action_clicked(self, action: dict):
        """Вызывается когда юзер нажал на кнопку действия слева"""
        if self._ai_busy:
            return
        self.pending_action = action
        title = self._get_action_title(action)

        self._add_user_message(t("action_user_msg", title=title))

        if self.qwen_provider.is_available():
            system_prompt = build_explanation_prompt(action, self.system_data, response_language=get_language())
            self._run_qwen(system_prompt, f"Explain action: {title}", mode="explanation", action=action)
        else:
            desc = action.get("description_ru", "Нет описания")
            risk = action.get("risk_level", "low")
            effect = action.get("estimated_effect", "")
            risk_labels = {"none": "Безопасно", "low": "Низкий", "medium": "Средний", "high": "Высокий"}
            self._add_ai_message_with_apply(
                f"{desc}\n\nЭффект: {effect}\nРиск: {risk_labels.get(risk, risk)}",
                action
            )

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Заголовок
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(0, 0, 0, 15)

        bolt_path = resource_path(os.path.join("assets", "icons", "bolt.svg"))
        bolt_icon = QSvgWidget(bolt_path)
        bolt_icon.setFixedSize(28, 28)
        bolt_icon.setStyleSheet("background: transparent; border: none;")

        header = QLabel("CorePilot AI")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))

        lang_btn = LangSwitcher()
        lang_btn._ru_active = get_language() == "ru"
        self._lang_btn = lang_btn

        self._shop_btn = QPushButton(t("shop_btn"))
        self._shop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._shop_btn.setFont(QFont("Segoe UI", 10))
        self._shop_btn.setFixedHeight(32)
        self._shop_btn.setIcon(QIcon(resource_path(os.path.join("assets", "icons", "store.svg"))))
        self._shop_btn.setIconSize(QSize(16, 16))
        self._shop_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #6B46C1;
                border-radius: 8px;
                padding: 0px 14px 0px 10px;
                color: #ffffff;
            }
            QPushButton:hover { background: #2a1f4a; color: #ffffff; }
        """)

        self._shop_btn.clicked.connect(self._open_store)

        header_layout.addWidget(bolt_icon)
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self._shop_btn)
        header_layout.addWidget(lang_btn)
        main_layout.addLayout(header_layout)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("QFrame { background-color: #1d1d1d; border: none; }")
        main_layout.addWidget(divider)

        # Область сообщений
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(10)

        # Стартовое сообщение пока грузится система
        loading_msg = self._create_ai_bubble(t("loading_msg"))
        self.messages_layout.addWidget(loading_msg)
        self.messages_layout.addStretch()

        self.messages_container.setLayout(self.messages_layout)
        self.messages_area.setWidget(self.messages_container)
        main_layout.addWidget(self.messages_area, 1)

        # Поле ввода
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border: 2px solid #3a3a3a;
                border-radius: 12px;
            }
        """)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(18, 10, 8, 10)
        input_layout.setSpacing(8)

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText(t("input_placeholder"))
        self.input_field.setFont(QFont("Segoe UI", 12))
        self.input_field.setFixedHeight(42)
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_field.document().setDocumentMargin(2)
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_field.setStyleSheet("""
            QTextEdit { background: transparent; border: none; color: #ffffff; padding: 6px 0px; }
        """)

        self.send_button = QPushButton()
        self.send_button.setFixedSize(36, 36)
        self.send_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.setEnabled(False)
        self._send_icon_path = resource_path(os.path.join("assets", "icons", "send.svg"))
        self._stop_icon_path = resource_path(os.path.join("assets", "icons", "stop.svg"))
        self.send_button.setIcon(QIcon(self._send_icon_path))
        self.send_button.setIconSize(QSize(20, 20))
        self.send_button.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; border-radius: 18px; }
            QPushButton:enabled { background-color: #6B46C1; }
            QPushButton:enabled:hover { background-color: #7C3AED; }
            QPushButton:enabled:pressed { background-color: #5B21B6; }
            QPushButton:disabled { background-color: transparent; }
        """)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        input_container.setLayout(input_layout)

        self.send_button.clicked.connect(self.send_message)
        self.input_field.textChanged.connect(self._update_send_btn)
        self.input_field.keyPressEvent = self._key_press

        main_layout.addWidget(input_container)
        self.setLayout(main_layout)

        from core.language import lang_manager
        lang_manager.language_changed.connect(self.retranslate)
        self.retranslate()

    def _open_store(self):
        from ui.store_dialog import StoreDialog
        dialog = StoreDialog(parent=self)
        dialog.exec()

    def retranslate(self):
        self.input_field.setPlaceholderText(t("input_placeholder"))
        self._shop_btn.setText(t("shop_btn"))
        if self._thinking_label:
            self._thinking_label.setText(t("thinking_msg"))
        if self._input_shows_stop:
            self.send_button.setToolTip(t("stop_generation_tooltip"))

        self.setStyleSheet("""
            QWidget { background-color: #1a1a1a; color: #e0e0e0; }
            QLabel { background: transparent; color: #ffffff; }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: transparent; width: 10px; border-radius: 5px; margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #6B46C1; border-radius: 5px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #7C3AED; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #1a1a1a; border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

    def _create_ai_bubble(self, text: str) -> QWidget:
        """Создаёт пузырь сообщения от AI"""
        message = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        avatar_container.setStyleSheet("background: transparent; border: none;")
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = resource_path(os.path.join("assets", "icons", "bot.svg"))
        bot_icon = QSvgWidget(icon_path)
        bot_icon.setFixedSize(28, 28)
        bot_icon.setStyleSheet("background: transparent; border: none;")
        avatar_layout.addWidget(bot_icon, 0, Qt.AlignmentFlag.AlignCenter)
        avatar_container.setLayout(avatar_layout)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Segoe UI", 11))
        bubble.setMinimumWidth(300)
        bubble.setMaximumWidth(560)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-radius: 16px;
                border: 1px solid #3a3a3a;
                padding: 14px 18px;
                color: #ffffff;
            }
        """)

        layout.addWidget(avatar_container, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(bubble, 1)
        layout.addStretch()
        message.setLayout(layout)
        return message

    def _create_user_bubble(self, text: str) -> QWidget:
        """Создаёт пузырь сообщения от юзера"""
        message = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Segoe UI", 11))
        bubble.setMinimumWidth(200)
        bubble.setMaximumWidth(560)
        bubble.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6B46C1, stop:1 #7C3AED);
                border-radius: 16px;
                padding: 14px 18px;
                color: #ffffff;
            }
        """)

        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        avatar_container.setStyleSheet("background: transparent; border: none;")
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_icon_path = resource_path(os.path.join("assets", "icons", "user.svg"))
        user_icon = QSvgWidget(user_icon_path)
        user_icon.setFixedSize(28, 28)
        user_icon.setStyleSheet("background: transparent; border: none;")
        avatar_layout.addWidget(user_icon, 0, Qt.AlignmentFlag.AlignCenter)
        avatar_container.setLayout(avatar_layout)

        layout.addStretch()
        layout.addWidget(bubble)
        layout.addWidget(avatar_container, 0, Qt.AlignmentFlag.AlignTop)
        message.setLayout(layout)
        return message

    def _add_ai_message(self, text: str):
        self._remove_stretch()
        msg = self._create_ai_bubble(text)
        self.messages_layout.addWidget(msg)
        self.messages_layout.addStretch()
        QTimer.singleShot(50, self._scroll_bottom)

    def _add_user_message(self, text: str):
        self._remove_stretch()
        msg = self._create_user_bubble(text)
        self.messages_layout.addWidget(msg)
        self.messages_layout.addStretch()
        QTimer.singleShot(50, self._scroll_bottom)

    def _add_ai_message_with_apply(self, text: str, action: dict):
        """Добавляет сообщение AI с кнопкой Применить"""
        self._remove_stretch()

        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        avatar_container.setStyleSheet("background: transparent; border: none;")
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = resource_path(os.path.join("assets", "icons", "bot.svg"))
        bot_icon = QSvgWidget(icon_path)
        bot_icon.setFixedSize(28, 28)
        bot_icon.setStyleSheet("background: transparent; border: none;")
        avatar_layout.addWidget(bot_icon, 0, Qt.AlignmentFlag.AlignCenter)
        avatar_container.setLayout(avatar_layout)

        content = QVBoxLayout()
        content.setSpacing(8)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Segoe UI", 11))
        bubble.setMinimumWidth(300)
        bubble.setMaximumWidth(560)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-radius: 16px;
                border: 1px solid #3a3a3a;
                padding: 14px 18px;
                color: #ffffff;
            }
        """)
        content.addWidget(bubble)

        # Кнопка Применить
        action_type = action.get("action_type", "powershell")
        apply_btn = QPushButton(t("apply_btn", title=self._get_action_title(action)))
        apply_btn.setFont(QFont("Segoe UI", 10))
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setMaximumWidth(560)
        apply_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6B46C1, stop:1 #7C3AED);
                border: none; border-radius: 10px;
                padding: 10px 16px; color: #ffffff; text-align: left;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #8B5CF6);
            }
            QPushButton:pressed { background: #5B21B6; }
        """)

        if action_type == "powershell":
            apply_btn.clicked.connect(lambda checked, a=action: self._execute_powershell_action([a["id"]]))
        else:
            apply_btn.clicked.connect(lambda checked, aid=action["id"]: self._execute_open_action(aid))

        content.addWidget(apply_btn)

        layout.addWidget(avatar_container, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(content)
        layout.addStretch()
        container.setLayout(layout)

        self.messages_layout.addWidget(container)
        self.messages_layout.addStretch()
        QTimer.singleShot(50, self._scroll_bottom)

    def _execute_open_action(self, action_id: str):
        """Выполняет open-действие тихо — mark_completed сразу при успехе"""
        success, message = execute_action(action_id)
        if success:
            self.memory.mark_completed(action_id)
            self.action_applied.emit(action_id)
        icon = "" if success else "⚠️ "
        self._add_ai_message(f"{icon}{message}")

    def _execute_powershell_action(self, action_ids: list):
        """Запускает PowerShell команды. Повторяемые — скрыто, твики — с окном."""
        from actions.system_actions import load_actions_db
        from core.prompt_builder import load_actions
        import tempfile
        import subprocess

        try:
            actions_db = load_actions_db()
        except Exception as e:
            self._add_ai_message(f"⚠️ Не удалось загрузить базу действий: {e}")
            return

        all_actions = {a["id"]: a for a in load_actions()}
        repeatable_ids = [aid for aid in action_ids if all_actions.get(aid, {}).get("repeatable", False)]
        tweak_ids = [aid for aid in action_ids if aid not in repeatable_ids]

        # Повторяемые — запускаем скрыто
        for action_id in repeatable_ids:
            action = actions_db.get(action_id)
            if action and action.get("command"):
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", action["command"]]
                )
                self.memory.mark_completed(action_id)
                self.action_applied.emit(action_id)
        if repeatable_ids:
            self._add_ai_message(t("done_applied"))

        # Твики — с окном и подтверждением
        if not tweak_ids:
            return

        commands = []
        for action_id in tweak_ids:
            action = actions_db.get(action_id)
            if action and action.get("command"):
                commands.append(f'Write-Host "[CorePilot] {action_id}..." -ForegroundColor Cyan')
                commands.append(action["command"])
                commands.append(f'Write-Host "[CorePilot] {action_id} - OK" -ForegroundColor Green')

        if not commands:
            return

        commands.append('Write-Host "[CorePilot] Done!" -ForegroundColor Yellow')
        commands.append('Read-Host "Press Enter to close"')

        script = "\n".join(commands)
        tmp = tempfile.NamedTemporaryFile(mode='wb', suffix='.ps1', delete=False)
        tmp.write(b'\xef\xbb\xbf')
        tmp.write(script.encode('utf-8'))
        tmp.close()

        subprocess.Popen([
            'powershell', '-Command',
            f'Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File {tmp.name}" -Verb RunAs'
        ])

        self._add_ai_message(t("ps_opening"))
        QTimer.singleShot(500, lambda: self._ask_confirmation(tweak_ids, all_actions))

    def _ask_confirmation(self, action_ids: list, all_actions: dict = None):
        """Показывает диалог подтверждения выполнения"""
        self._remove_stretch()

        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        avatar_container.setStyleSheet("background: transparent; border: none;")
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = resource_path(os.path.join("assets", "icons", "bot.svg"))
        bot_icon = QSvgWidget(icon_path)
        bot_icon.setFixedSize(28, 28)
        bot_icon.setStyleSheet("background: transparent; border: none;")
        avatar_layout.addWidget(bot_icon, 0, Qt.AlignmentFlag.AlignCenter)
        avatar_container.setLayout(avatar_layout)

        content = QVBoxLayout()
        content.setSpacing(8)

        bubble = QLabel(t("confirm_done"))
        bubble.setFont(QFont("Segoe UI", 11))
        bubble.setMinimumWidth(300)
        bubble.setMaximumWidth(560)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-radius: 16px;
                border: 1px solid #3a3a3a;
                padding: 14px 18px;
                color: #ffffff;
            }
        """)
        content.addWidget(bubble)

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(8)

        yes_btn = QPushButton(t("yes_done"))
        yes_btn.setFont(QFont("Segoe UI", 10))
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setStyleSheet("""
            QPushButton {
                background: #166534;
                border: none; border-radius: 8px;
                padding: 8px 16px; color: #ffffff;
            }
            QPushButton:hover { background: #15803d; }
        """)

        no_btn = QPushButton(t("no"))
        no_btn.setFont(QFont("Segoe UI", 10))
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: none; border-radius: 8px;
                padding: 8px 16px; color: #ffffff;
            }
            QPushButton:hover { background: #4a4a4a; }
        """)

        def on_yes():
            container.setVisible(False)
            needs_restart = False
            for action_id in action_ids:
                self.memory.mark_completed(action_id)
                self.action_applied.emit(action_id)
                if all_actions.get(action_id, {}).get("restart_required", False):
                    needs_restart = True
            self._add_ai_message(t("done_applied"))
            if needs_restart:
                self.pending_restart = True
                QTimer.singleShot(300, self._show_restart_banner)

        def on_no():
            container.setVisible(False)
            self._add_ai_message(t("not_applied"))

        yes_btn.clicked.connect(on_yes)
        no_btn.clicked.connect(on_no)

        btns_layout.addWidget(yes_btn)
        btns_layout.addWidget(no_btn)
        btns_layout.addStretch()
        content.addLayout(btns_layout)

        layout.addWidget(avatar_container, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(content)
        layout.addStretch()
        container.setLayout(layout)

        self.messages_layout.addWidget(container)
        self.messages_layout.addStretch()
        QTimer.singleShot(50, self._scroll_bottom)

    def _show_restart_banner(self):
        self._remove_stretch()

        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        avatar_container.setStyleSheet("background: transparent; border: none;")
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_icon = QSvgWidget(resource_path(os.path.join("assets", "icons", "bot.svg")))
        bot_icon.setFixedSize(28, 28)
        bot_icon.setStyleSheet("background: transparent; border: none;")
        avatar_layout.addWidget(bot_icon, 0, Qt.AlignmentFlag.AlignCenter)
        avatar_container.setLayout(avatar_layout)

        content = QVBoxLayout()
        content.setSpacing(8)

        # Плашка
        bubble = QWidget()
        bubble.setMinimumWidth(300)
        bubble.setMaximumWidth(560)
        bubble.setStyleSheet("background-color: #2a2a2a; border-radius: 16px; border: 1px solid #3a3a3a;")
        bubble_layout = QHBoxLayout()
        bubble_layout.setContentsMargins(14, 12, 14, 12)
        bubble_layout.setSpacing(10)

        restart_icon = QSvgWidget(resource_path(os.path.join("assets", "icons", "restart.svg")))
        restart_icon.setFixedSize(18, 18)
        restart_icon.setStyleSheet("background: transparent; border: none;")
        # Красим SVG в фиолетовый
        from PyQt6.QtGui import QPainter, QColor
        from PyQt6.QtSvg import QSvgRenderer
        restart_icon.setStyleSheet("background: transparent; border: none; color: #a78bfa;")

        bubble_text = QLabel(t("restart_required"))
        bubble_text.setFont(QFont("Segoe UI", 11))
        bubble_text.setStyleSheet("color: #ffffff; background: transparent; border: none;")

        bubble_layout.addWidget(restart_icon)
        bubble_layout.addWidget(bubble_text)
        bubble_layout.addStretch()
        bubble.setLayout(bubble_layout)
        content.addWidget(bubble)

        # Кнопки
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(8)
        btns_layout.setContentsMargins(2, 0, 0, 0)

        reboot_btn = QPushButton(t("restart_now"))
        reboot_btn.setFont(QFont("Segoe UI", 10))
        reboot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reboot_btn.setMinimumHeight(36)
        reboot_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a; border-radius: 8px;
                padding: 8px 16px; color: #ffffff;
            }
            QPushButton:hover { background: #444444; }
            QPushButton:disabled { background: #2a2a2a; color: #555555; border-color: #333333; }
        """)

        later_btn = QPushButton(t("restart_later"))
        later_btn.setFont(QFont("Segoe UI", 10))
        later_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        later_btn.setMinimumHeight(36)
        later_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a; border-radius: 8px;
                padding: 8px 16px; color: #ffffff;
            }
            QPushButton:hover { background: #444444; }
            QPushButton:disabled { background: #2a2a2a; color: #555555; border-color: #333333; }
        """)

        def on_reboot():
            reboot_btn.setEnabled(False)
            later_btn.setEnabled(False)
            reboot_btn.setText(t("restarting"))
            import subprocess
            subprocess.Popen(["shutdown", "/r", "/t", "5"])

        def on_later():
            reboot_btn.setEnabled(False)
            later_btn.setEnabled(False)

        reboot_btn.clicked.connect(on_reboot)
        later_btn.clicked.connect(on_later)

        btns_layout.addWidget(reboot_btn)
        btns_layout.addWidget(later_btn)
        btns_layout.addStretch()
        content.addLayout(btns_layout)

        layout.addWidget(avatar_container, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(content)
        layout.addStretch()
        container.setLayout(layout)

        self.messages_layout.addWidget(container)
        self.messages_layout.addStretch()
        QTimer.singleShot(50, self._scroll_bottom)

    def send_message(self):
        """Отправка свободного вопроса"""
        if self._ai_busy:
            return
        text = self.input_field.toPlainText().strip()
        if not text:
            return

        self._add_user_message(text)
        self.last_user_message = text
        self.input_field.clear()
        # Сразу блокируем действия слева и кнопку отправки (иначе до _run_qwen есть пауза на таймере).
        self._ai_busy = True
        self._generation_can_stop = False
        self.ai_generation_changed.emit(True)
        self._sync_input_action_button()
        QTimer.singleShot(800, self._process_free_question)

    def _process_free_question(self):
        """Обрабатывает свободный вопрос через Qwen"""
        if not self.qwen_provider.is_available():
            self._finish_generation()
            self._add_ai_message(t("qwen_unavailable"))
            return

        system_prompt = build_question_prompt(self.last_user_message, self.system_data, response_language=resolve_response_language(self.last_user_message))
        self._run_qwen(system_prompt, self.last_user_message, mode="question")

    def _finish_generation(self):
        self._hide_thinking()
        self._ai_busy = False
        self._generation_can_stop = False
        self.ai_generation_changed.emit(False)
        self._sync_input_action_button()

    def _on_stop_generation(self):
        if self._cancel_event:
            self._cancel_event.set()

    def _sync_input_action_button(self):
        """Справа в поле ввода: стрелка отправки или «стоп» (только если можно прервать генерацию)."""
        try:
            self.send_button.clicked.disconnect()
        except TypeError:
            pass
        if self._ai_busy and self._generation_can_stop:
            if os.path.exists(self._stop_icon_path):
                self.send_button.setIcon(QIcon(self._stop_icon_path))
            self.send_button.setIconSize(QSize(20, 20))
            self.send_button.setToolTip(t("stop_generation_tooltip"))
            self.send_button.setEnabled(True)
            self.send_button.clicked.connect(self._on_stop_generation)
            self._input_shows_stop = True
        else:
            self.send_button.setIcon(QIcon(self._send_icon_path))
            self.send_button.setIconSize(QSize(20, 20))
            self.send_button.setToolTip("")
            self._input_shows_stop = False
            self.send_button.clicked.connect(self.send_message)
            self._update_send_btn()

    def _run_qwen(self, system_prompt: str, user_prompt: str, mode: str = "question", action: dict = None):
        """Запускает Qwen в отдельном потоке (стрим + отмена, кроме приветствия)."""
        if self.qwen_thread is not None and self.qwen_thread.isRunning():
            if self._cancel_event:
                self._cancel_event.set()
            self.qwen_thread.wait(30000)

        self._generation_seq += 1
        seq = self._generation_seq
        self._cancel_event = threading.Event()
        can_stop = mode != "greeting"
        self._generation_can_stop = can_stop

        self._ai_busy = True
        self.ai_generation_changed.emit(True)
        self._show_thinking()
        self._sync_input_action_button()

        self.qwen_thread = QwenThread(
            self.qwen_provider, user_prompt, system_prompt, self._cancel_event
        )
        self.qwen_thread.finished.connect(
            lambda r, s=seq, m=mode, a=action: self._on_qwen_thread_finished(r, m, a, s)
        )
        self.qwen_thread.error.connect(lambda _e, s=seq: self._on_qwen_thread_error(s))
        self.qwen_thread.cancelled.connect(lambda p, s=seq: self._on_qwen_thread_cancelled(p, s))
        self.qwen_thread.start()

    def _on_qwen_thread_finished(self, response: str, mode: str, action: dict, seq: int):
        if seq != self._generation_seq:
            return
        self._finish_generation()
        self._on_qwen_response_body(response, mode, action)

    def _on_qwen_thread_error(self, seq: int):
        if seq != self._generation_seq:
            return
        self._finish_generation()
        self._add_ai_message(t("action_error"))

    def _on_qwen_thread_cancelled(self, partial: str, seq: int):
        if seq != self._generation_seq:
            return
        self._finish_generation()
        self._add_ai_message(t("response_stopped"))

    def _on_qwen_response_body(self, response: str, mode: str, action: dict = None):
        message = self._parse_message(response)
        if mode == "explanation" and action:
            self._add_ai_message_with_apply(message, action)
        else:
            self._add_ai_message(message)

    def _parse_message(self, response: str) -> str:
        """Парсит JSON ответ от Qwen, возвращает только message"""
        try:
            response = response.replace('\\"', '"').strip()
            import re
            matches = re.findall(r'\{[^{}]*"message"[^{}]*\}', response, re.DOTALL)
            if matches:
                response = matches[0]
            parsed = json.loads(response)
            return parsed.get("message", response)
        except Exception:
            try:
                from json_repair import repair_json
                parsed = json.loads(repair_json(response))
                return parsed.get("message", response)
            except Exception:
                return response

    def _show_thinking(self):
        """Пузырь «думает»; остановка — только кнопкой справа в поле ввода (если разрешено)."""
        self._remove_stretch()
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        avatar_container.setStyleSheet("background: transparent; border: none;")
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_icon = QSvgWidget(resource_path(os.path.join("assets", "icons", "bot.svg")))
        bot_icon.setFixedSize(28, 28)
        bot_icon.setStyleSheet("background: transparent; border: none;")
        avatar_layout.addWidget(bot_icon, 0, Qt.AlignmentFlag.AlignCenter)
        avatar_container.setLayout(avatar_layout)

        self._thinking_label = QLabel(t("thinking_msg"))
        self._thinking_label.setFont(QFont("Segoe UI", 11))
        self._thinking_label.setMinimumWidth(200)
        self._thinking_label.setMaximumWidth(480)
        self._thinking_label.setWordWrap(True)
        self._thinking_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-radius: 16px;
                border: 1px solid #3a3a3a;
                padding: 14px 18px;
                color: #888888;
            }
        """)

        layout.addWidget(avatar_container, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._thinking_label, 1, Qt.AlignmentFlag.AlignTop)
        layout.addStretch()
        container.setLayout(layout)

        self.thinking_widget = container
        self.messages_layout.addWidget(self.thinking_widget)
        self.messages_layout.addStretch()
        QTimer.singleShot(50, self._scroll_bottom)

    def _hide_thinking(self):
        if self.thinking_widget:
            self._remove_stretch()
            self.messages_layout.removeWidget(self.thinking_widget)
            self.thinking_widget.deleteLater()
            self.thinking_widget = None
        self._thinking_label = None

    def _remove_stretch(self):
        if self.messages_layout.count() > 0:
            item = self.messages_layout.itemAt(self.messages_layout.count() - 1)
            if item and item.spacerItem():
                self.messages_layout.removeItem(item)

    def _scroll_bottom(self):
        self.messages_area.verticalScrollBar().setValue(
            self.messages_area.verticalScrollBar().maximum()
        )

    def _update_send_btn(self):
        if self._input_shows_stop:
            self.send_button.setEnabled(True)
            return
        self.send_button.setEnabled(
            bool(self.input_field.toPlainText().strip()) and not self._ai_busy
        )

    def _key_press(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                QTextEdit.keyPressEvent(self.input_field, event)
            else:
                self.send_message()
        else:
            QTextEdit.keyPressEvent(self.input_field, event)
