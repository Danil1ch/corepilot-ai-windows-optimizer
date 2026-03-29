from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QSizePolicy,
    QLayout,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QFont,
    QColor,
    QPen,
    QBrush,
    QPainter,
    QPolygonF,
)
from PyQt6.QtSvgWidgets import QSvgWidget
import os
from utils import resource_path
from core.translations import t


class SquareToggle(QWidget):
    """Квадрат-флажок с галочкой в стиле Lucide (M20 6 L9 17 L4 12)."""

    toggled = pyqtSignal(bool)
    IND = 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(self.IND, self.IND)
        self.setMinimumSize(self.IND, self.IND)
        self.setMaximumSize(self.IND, self.IND)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        return QSize(self.IND, self.IND)

    def minimumSizeHint(self):
        return QSize(self.IND, self.IND)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, v: bool) -> None:
        v = bool(v)
        if self._checked != v:
            self._checked = v
            self.update()
            self.toggled.emit(v)

    def flip(self) -> None:
        self.setChecked(not self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.flip()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0.5, 0.5, self.IND - 1, self.IND - 1)
        if self._checked:
            p.setBrush(QBrush(QColor("#6B46C1")))
            p.setPen(QPen(QColor("#a78bfa"), 1))
        else:
            p.setBrush(QBrush(QColor("#2a1f4a")))
            p.setPen(QPen(QColor("#6B46C1"), 1))
        p.drawRoundedRect(r, 4, 4)

        if self._checked:
            p.setPen(
                QPen(
                    QColor("#f5f3ff"),
                    2.15,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            # Те же пропорции, что path Lucide check в 24×24
            poly = QPolygonF(
                [
                    QPointF(13.0, 5.9),
                    QPointF(7.7, 12.4),
                    QPointF(4.8, 9.5),
                ]
            )
            p.drawPolyline(poly)


class UninstallDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CorePilot")
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1035;
                border: 1px solid #8B5CF6;
                border-radius: 12px;
            }
            QPushButton#no_btn {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 8px;
                color: #ffffff;
            }
            QPushButton#no_btn:hover {
                background: #4a4a4a;
                border-color: #777777;
            }
            QPushButton#yes_btn {
                background: #EF4444;
                border: none;
                border-radius: 8px;
                color: #ffffff;
            }
            QPushButton#yes_btn:hover { background: #DC2626; }
            QPushButton#yes_btn:disabled {
                background: #4a2a2a;
                color: #888888;
            }
        """)
        self._build_ui()
        self.layout().activate()
        self.adjustSize()
        w = max(self.minimumWidth(), self.sizeHint().width())
        h = self.sizeHint().height()
        self.setFixedSize(w, h)

    def _option_block(
        self, icon_file: str, title: str, hint: str
    ) -> tuple[QWidget, SquareToggle]:
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 1, 0, 1)
        h.setSpacing(10)

        icon_path = resource_path(os.path.join("assets", "icons", icon_file))
        icon = QSvgWidget(icon_path)
        icon.setFixedSize(28, 28)
        icon.setStyleSheet("background: transparent; border: none;")

        toggle = SquareToggle()

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        title_lbl.setStyleSheet("color: #f4f4f5; background: transparent;")
        title_lbl.setWordWrap(True)
        title_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        hint_lbl = QLabel(hint)
        hint_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        hint_lbl.setStyleSheet("color: #ffffff; background: transparent;")
        hint_lbl.setWordWrap(True)
        hint_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(toggle, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        title_row.addWidget(title_lbl, 1, Qt.AlignmentFlag.AlignTop)

        right = QVBoxLayout()
        right.setSpacing(3)
        right.addLayout(title_row)
        right.addWidget(hint_lbl)

        h.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        h.addLayout(right, 1)
        return row, toggle

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 14)
        layout.setSpacing(8)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        trash_icon = QSvgWidget(
            resource_path(os.path.join("assets", "icons", "trash_red.svg"))
        )
        trash_icon.setFixedSize(20, 20)
        trash_icon.setStyleSheet("background: transparent; border: none;")

        title = QLabel(t("uninstall_title"))
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")

        title_row.addWidget(trash_icon)
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        desc = QLabel(t("uninstall_desc"))
        desc.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        desc.setStyleSheet("color: #d4c8ec; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._tg_model = self._add_option(
            layout,
            "setup_model.svg",
            t("uninstall_item_model"),
            t("uninstall_item_model_hint"),
        )
        self._tg_ollama = self._add_option(
            layout,
            "setup_ollama.svg",
            t("uninstall_item_ollama"),
            t("uninstall_item_ollama_hint"),
        )
        self._tg_app = self._add_option(
            layout,
            "bot.svg",
            t("uninstall_item_app"),
            t("uninstall_item_app_hint"),
        )

        for tg in (self._tg_model, self._tg_ollama, self._tg_app):
            tg.toggled.connect(self._sync_yes)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addStretch()

        no_btn = QPushButton(t("uninstall_no"))
        no_btn.setObjectName("no_btn")
        no_btn.setFixedSize(100, 36)
        no_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.clicked.connect(self.reject)

        self._yes_btn = QPushButton(t("uninstall_yes"))
        self._yes_btn.setObjectName("yes_btn")
        self._yes_btn.setFixedSize(100, 36)
        self._yes_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._yes_btn.clicked.connect(self._on_yes)

        btns.addWidget(no_btn)
        btns.addWidget(self._yes_btn)
        layout.addLayout(btns)

        self._sync_yes()

    def _add_option(
        self, layout: QVBoxLayout, icon: str, title: str, hint: str
    ) -> SquareToggle:
        block, tg = self._option_block(icon, title, hint)
        layout.addWidget(block)
        return tg

    def _sync_yes(self):
        any_on = (
            self._tg_model.isChecked()
            or self._tg_ollama.isChecked()
            or self._tg_app.isChecked()
        )
        self._yes_btn.setEnabled(any_on)

    def _on_yes(self):
        from core.uninstaller import run_uninstall, is_exe, install_folder_wipe_info
        from PyQt6.QtWidgets import QApplication, QMessageBox

        rm_app = self._tg_app.isChecked()
        schedule_wipe = True
        if rm_app and is_exe():
            info = install_folder_wipe_info()
            if not info.safe:
                schedule_wipe = False
                QMessageBox.warning(
                    self,
                    t("uninstall_unsafe_folder_title"),
                    t(
                        "uninstall_unsafe_folder_msg",
                        reason=t(info.reason_key or "uninstall_wipe_forbidden_path"),
                        path=info.install_dir or "—",
                    ),
                )

        self.accept()
        run_uninstall(
            remove_model=self._tg_model.isChecked(),
            remove_ollama=self._tg_ollama.isChecked(),
            remove_app=rm_app,
            app_instance=QApplication.instance(),
            schedule_program_folder_wipe=schedule_wipe,
        )

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainterPath, QPen

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        painter.fillPath(path, QColor("#1e1035"))
        painter.setPen(QPen(QColor("#8B5CF6"), 1))
        painter.drawPath(path)
