from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPainterPath, QPen
from PyQt6.QtSvgWidgets import QSvgWidget
import os
from utils import resource_path
from core.translations import t
from core.language import lang_manager, get_language


class ActionRow(QWidget):
    action_clicked = pyqtSignal(dict)
    rollback_clicked = pyqtSignal(dict)

    def __init__(self, action: dict, is_event: bool = False, parent=None):
        super().__init__(parent)
        self.action = action
        self.is_event = is_event
        self._applied = False
        self._hovered = False
        self._ai_lock = False

        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(8)

        # Success иконка (только в applied)
        self._success_icon = QSvgWidget(resource_path(os.path.join("assets", "icons", "success.svg")))
        self._success_icon.setFixedSize(16, 16)
        self._success_icon.setStyleSheet("background: transparent; border: none;")
        self._layout.addWidget(self._success_icon)

        # Текст
        self._label = QLabel()
        self._label.setFont(QFont("Segoe UI", 10))
        self._label.setStyleSheet("background: transparent; border: none;")
        self._layout.addWidget(self._label, 1)

        # Risk иконка (только в active, для medium/high)
        risk = action.get("risk_level", "low")
        risk_icon_file = {"medium": "warning.svg", "high": "danger.svg"}.get(risk)
        self._risk_icon = None
        if risk_icon_file:
            risk_path = resource_path(os.path.join("assets", "icons", risk_icon_file))
            if os.path.exists(risk_path):
                self._risk_icon = QSvgWidget(risk_path)
                self._risk_icon.setFixedSize(16, 16)
                self._risk_icon.setStyleSheet("background: transparent; border: none;")
                self._risk_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self._layout.addWidget(self._risk_icon)

        # Undo иконка (только в applied, если есть rollback)
        self._undo_icon = None
        if action.get("rollback_command"):
            undo_path = resource_path(os.path.join("assets", "icons", "undo.svg"))
            if os.path.exists(undo_path):
                self._undo_icon = QSvgWidget(undo_path)
                self._undo_icon.setFixedSize(14, 14)
                self._undo_icon.setStyleSheet("background: transparent; border: none;")
                self._undo_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self._layout.addWidget(self._undo_icon)

        # Начальное состояние
        self.set_active()
        lang_manager.language_changed.connect(self._on_language_changed)

    def _get_title(self) -> str:
        lang = get_language()
        if lang == "en":
            return self.action.get("title_en") or self.action.get("title_ru", self.action.get("id", ""))
        return self.action.get("title_ru", self.action.get("id", ""))

    def _on_language_changed(self):
        if self._applied:
            self.set_applied()
        else:
            self.set_active()

    def set_active(self):
        self._applied = False
        self._hovered = False

        title = self._get_title()
        self._label.setText(f"  {title}")

        self._label.setStyleSheet("color: #e0e0e0; background: transparent; border: none;")

        self._success_icon.hide()
        if self._risk_icon:
            self._risk_icon.show()
        if self._undo_icon:
            self._undo_icon.hide()

        self._sync_lock_appearance()
        self.update()

    def set_applied(self):
        self._applied = True
        self._hovered = False
        self._ai_lock = False

        title = self._get_title()
        suffix = t("event_suffix") if self.is_event else t("applied_suffix")
        self._label.setText(f"{title} {suffix}")
        self._label.setStyleSheet("color: #22C55E; background: transparent; border: none;")

        self._success_icon.show()
        if self._risk_icon:
            self._risk_icon.hide()
        if self._undo_icon:
            self._undo_icon.show()
            best_effort = self.action.get("rollback_best_effort", False)
            self.setToolTip(t("rollback_tooltip_approx") if best_effort else t("rollback_tooltip"))
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setToolTip("")

        self.update()

    def set_ai_lock(self, locked: bool):
        """Блокирует клик по активной строке, пока ИИ генерирует ответ (для твиков)."""
        self._ai_lock = locked
        if not self._applied:
            self._sync_lock_appearance()
        self.update()

    def _sync_lock_appearance(self):
        if self._ai_lock:
            self.setToolTip(t("action_wait_ai"))
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            self.setToolTip("")
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self.rect()
        radius = 8.0

        risk = self.action.get("risk_level", "low")
        risk_colors = {"none": "#22C55E", "low": "#22C55E", "medium": "#F59E0B", "high": "#EF4444"}

        if self._applied:
            bg = "#1a1a1a" if self._hovered else "#141414"
            border = "#3a3a3a" if self._hovered else "#1f1f1f"
            left_color = "#22C55E"
        else:
            if self._ai_lock:
                bg = "#181818"
                border = "#2a2a2a"
            else:
                bg = "#242424" if self._hovered else "#1a1a1a"
                border = "#6B46C1" if self._hovered else "#2a2a2a"
            left_color = risk_colors.get(risk, "#22C55E")

        # Фон
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(bg))
        path = QPainterPath()
        path.addRoundedRect(r.x(), r.y(), r.width(), r.height(), radius, radius)
        painter.fillPath(path, painter.brush())

        from PyQt6.QtCore import QRectF
        # Правая граница + верх + низ
        pen = QPen(QColor(border), 1)
        painter.setPen(pen)
        painter.drawLine(int(radius), r.top(), r.right() - int(radius), r.top())
        painter.drawLine(int(radius), r.bottom(), r.right() - int(radius), r.bottom())
        painter.drawLine(r.right(), int(radius), r.right(), r.bottom() - int(radius))
        painter.drawArc(QRectF(r.right() - radius*2, r.top(), radius*2, radius*2), 0, 90*16)
        painter.drawArc(QRectF(r.right() - radius*2, r.bottom() - radius*2, radius*2, radius*2), 270*16, 90*16)

        # Левая полоска со скруглением
        left_pen = QPen(QColor(left_color), 3)
        painter.setPen(left_pen)
        painter.drawLine(r.left() + 1, r.top() + int(radius), r.left() + 1, r.bottom() - int(radius))
        painter.drawArc(QRectF(r.left(), r.top(), radius*2, radius*2), 90*16, 90*16)
        painter.drawArc(QRectF(r.left(), r.bottom() - radius*2, radius*2, radius*2), 180*16, 90*16)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._applied:
            if self._undo_icon:
                self.rollback_clicked.emit(self.action)
        else:
            if self._ai_lock:
                return
            self.action_clicked.emit(self.action)
