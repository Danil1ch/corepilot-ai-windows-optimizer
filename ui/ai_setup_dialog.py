"""
Мастер настройки локального ИИ: Ollama + модель (без подключения к main.py).
"""

from __future__ import annotations

import os
import subprocess

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtSvgWidgets import QSvgWidget

from core.ai_stack_constants import (
    COREPILOT_LLM_MODEL,
    OLLAMA_DOWNLOAD_WINDOWS_URL,
    pull_model_command,
)
from core.language import lang_manager
from core.ollama_setup import fetch_ollama_tags, is_model_present
from core.translations import t
from utils import resource_path, get_app_qicon
from ui.chat_panel import LangSwitcher


def _try_start_ollama_app() -> bool:
    """Пытается запустить Ollama.exe из стандартного пути установки Windows."""
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(local, "Programs", "Ollama", "Ollama.exe"),
        os.path.join(local, "Programs", "Ollama", "ollama.exe"),
    ]
    for exe in candidates:
        if os.path.isfile(exe):
            try:
                subprocess.Popen([exe], cwd=os.path.dirname(exe))
                return True
            except OSError:
                continue
    return False


class AiSetupDialog(QDialog):
    """Окно: шаги Ollama и модели, ссылки, проверки, команда pull."""

    # Фиксированная ширина; высота подстраивается под текст (EN короче — окно ниже)
    _WIN_W = 520
    _MIN_H = 440
    _MAX_H = 720

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ollama_ok = False
        self._model_ok = False
        self._ollama_err: str | None = None
        self.setWindowTitle(t("setup_window_title"))
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.CustomizeWindowHint)
        self.setModal(True)
        _ic = get_app_qicon()
        if not _ic.isNull():
            self.setWindowIcon(_ic)
        self._build_ui()
        lang_manager.language_changed.connect(self._retranslate)
        self._retranslate()
        self._apply_style()
        self._refresh_continue()
        self.run_full_check()
        QTimer.singleShot(0, self._fit_window_height)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 8px 14px;
                color: #ffffff;
            }
            QPushButton:hover { border-color: #6B46C1; background-color: #242424; }
            QPushButton:disabled { color: #666666; border-color: #2a2a2a; }
            QPushButton#primary {
                background-color: #6B46C1;
                border: 1px solid #7C3AED;
            }
            QPushButton#primary:hover { background-color: #7C3AED; }
            QPushButton#primary:disabled {
                background-color: #3a3a3a;
                border-color: #3a3a3a;
                color: #888888;
            }
        """)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(14)

        self._title_lbl = QLabel()
        self._title_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        title_row = QHBoxLayout()
        title_row.addWidget(self._title_lbl)
        title_row.addStretch()
        from core.language import get_language
        lang_btn = LangSwitcher()
        lang_btn._ru_active = get_language() == "ru"
        title_row.addWidget(lang_btn)
        root.addLayout(title_row)

        self._subtitle_lbl = QLabel()
        self._subtitle_lbl.setWordWrap(True)
        self._subtitle_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self._subtitle_lbl.setStyleSheet("color: #a3a3a3;")
        root.addWidget(self._subtitle_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #2a2a2a; max-height: 1px; border: none;")
        root.addWidget(line)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(16)
        inner_layout.setContentsMargins(0, 0, 0, 0)

        # --- Блок Ollama ---
        self._ollama_block = self._make_section_header("setup_ollama", "setup_ollama.svg")
        inner_layout.addWidget(self._ollama_block["container"])

        self._ollama_help = QLabel()
        self._ollama_help.setWordWrap(True)
        self._ollama_help.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self._ollama_help.setStyleSheet("color: #c4c4c4;")
        inner_layout.addWidget(self._ollama_help)

        row_o = QHBoxLayout()
        row_o.setSpacing(8)
        self._btn_dl = QPushButton()
        self._btn_dl.clicked.connect(self._open_download_page)
        self._btn_start = QPushButton()
        self._btn_start.clicked.connect(self._on_try_start_ollama)
        self._btn_check_o = QPushButton()
        self._btn_check_o.clicked.connect(self.run_full_check)
        row_o.addWidget(self._btn_dl)
        row_o.addWidget(self._btn_start)
        row_o.addWidget(self._btn_check_o)
        row_o.addStretch()
        inner_layout.addLayout(row_o)

        self._status_o = QLabel()
        self._status_o.setWordWrap(True)
        self._status_o.setStyleSheet("font-size: 11px;")
        inner_layout.addWidget(self._status_o)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2a2a2a; max-height: 1px; border: none;")
        inner_layout.addWidget(sep)

        # --- Блок модели ---
        self._model_block = self._make_section_header("setup_model", "setup_model.svg")
        inner_layout.addWidget(self._model_block["container"])

        self._model_help = QLabel()
        self._model_help.setWordWrap(True)
        self._model_help.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self._model_help.setStyleSheet("color: #c4c4c4;")
        inner_layout.addWidget(self._model_help)

        self._cmd_label = QLabel()
        self._cmd_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._cmd_label.setFont(QFont("Consolas", 10))
        self._cmd_label.setStyleSheet(
            "background-color: #121212; border: 1px solid #333; border-radius: 8px; "
            "padding: 10px; color: #e9d5ff;"
        )
        self._cmd_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        inner_layout.addWidget(self._cmd_label)

        row_m = QHBoxLayout()
        row_m.setSpacing(8)
        self._btn_copy = QPushButton()
        self._btn_copy.clicked.connect(self._on_copy_pull)
        self._btn_check_m = QPushButton()
        self._btn_check_m.clicked.connect(self.check_model_only)
        row_m.addWidget(self._btn_copy)
        row_m.addWidget(self._btn_check_m)
        row_m.addStretch()
        inner_layout.addLayout(row_m)

        self._status_m = QLabel()
        self._status_m.setWordWrap(True)
        self._status_m.setStyleSheet("font-size: 11px;")
        inner_layout.addWidget(self._status_m)

        # Без растяжки снизу — высота контента «по тексту», а не на весь экран
        self._scroll.setWidget(inner)
        root.addWidget(self._scroll, 0)

        foot = QHBoxLayout()
        foot.addStretch()
        self._btn_continue = QPushButton()
        self._btn_continue.setObjectName("primary")
        self._btn_continue.clicked.connect(self.accept)
        foot.addWidget(self._btn_continue)
        root.addLayout(foot)

        self._model_widgets = [
            self._model_block["container"],
            self._model_help,
            self._cmd_label,
            self._btn_copy,
            self._btn_check_m,
            self._status_m,
        ]

    def _make_section_header(self, title_key: str, icon_file: str) -> dict:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        icon_path = resource_path(os.path.join("assets", "icons", icon_file))
        icon = QSvgWidget(icon_path)
        icon.setFixedSize(28, 28)
        icon.setStyleSheet("background: transparent; border: none;")
        lbl = QLabel()
        lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl.setObjectName(title_key)
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(lbl, 1)
        return {"container": container, "title": lbl, "title_key": title_key}

    def _retranslate(self):
        self.setWindowTitle(t("setup_window_title"))
        self._title_lbl.setText(t("setup_title"))
        self._subtitle_lbl.setText(t("setup_subtitle"))
        self._ollama_block["title"].setText(t("setup_ollama_section"))
        self._model_block["title"].setText(t("setup_model_section"))
        self._ollama_help.setText(t("setup_ollama_help"))
        self._model_help.setText(
            t("setup_model_help", model=COREPILOT_LLM_MODEL, cmd=pull_model_command())
        )
        self._cmd_label.setText(pull_model_command())
        self._btn_dl.setText(t("setup_open_download"))
        self._btn_start.setText(t("setup_try_start_ollama"))
        self._btn_check_o.setText(t("setup_check"))
        self._btn_copy.setText(t("setup_copy_command"))
        self._btn_check_m.setText(t("setup_check"))
        self._btn_continue.setText(t("setup_continue"))
        self._sync_status()
        self._fit_window_height()

    def _fit_window_height(self):
        """Подгоняет высоту под текущий язык и текст (без ручного ресайза)."""
        self.layout().activate()
        if self._scroll.widget():
            self._scroll.widget().adjustSize()
        QApplication.processEvents()
        h = max(self.sizeHint().height(), self.minimumSizeHint().height())
        h = max(self._MIN_H, min(h, self._MAX_H))
        self.setFixedSize(self._WIN_W, h)

    def _translate_error(self, code: str | None) -> str:
        if code == "timeout":
            return t("setup_err_timeout")
        if code == "connection":
            return t("setup_err_connection")
        if code:
            return t("setup_err_generic", detail=code)
        return t("setup_err_connection")

    def _sync_status(self):
        if self._ollama_ok:
            self._status_o.setText(t("setup_ollama_ok"))
            self._status_o.setStyleSheet("font-size: 11px; color: #22C55E;")
        elif self._ollama_err:
            self._status_o.setText(
                t("setup_ollama_fail", reason=self._translate_error(self._ollama_err))
            )
            self._status_o.setStyleSheet("font-size: 11px; color: #F87171;")
        else:
            self._status_o.setText(t("setup_ollama_wait"))
            self._status_o.setStyleSheet("font-size: 11px; color: #888888;")

        if not self._ollama_ok:
            self._status_m.setText(t("setup_model_need_ollama"))
            self._status_m.setStyleSheet("font-size: 11px; color: #888888;")
        elif self._model_ok:
            self._status_m.setText(t("setup_model_ok"))
            self._status_m.setStyleSheet("font-size: 11px; color: #22C55E;")
        else:
            self._status_m.setText(
                t("setup_model_missing", model=COREPILOT_LLM_MODEL)
            )
            self._status_m.setStyleSheet("font-size: 11px; color: #FBBF24;")

    def _set_model_section_enabled(self, on: bool):
        for w in self._model_widgets:
            w.setEnabled(on)

    def run_full_check(self):
        ok, models, err = fetch_ollama_tags(timeout=3.0)
        self._ollama_ok = bool(ok)
        self._ollama_err = err if not ok else None
        if ok and models is not None:
            self._model_ok = is_model_present(models)
        else:
            self._model_ok = False
        self._set_model_section_enabled(self._ollama_ok)
        self._sync_status()
        self._refresh_continue()
        self._fit_window_height()

    def check_model_only(self):
        if not self._ollama_ok:
            self._sync_status()
            self._fit_window_height()
            return
        ok, models, err = fetch_ollama_tags(timeout=3.0)
        if not ok:
            self._ollama_ok = False
            self._ollama_err = err
            self._model_ok = False
            self._set_model_section_enabled(False)
            self._status_m.setText(t("setup_ollama_lost", reason=self._translate_error(err)))
            self._status_m.setStyleSheet("font-size: 11px; color: #F87171;")
            self._sync_status()
            self._refresh_continue()
            self._fit_window_height()
            return
        self._ollama_ok = True
        self._ollama_err = None
        self._model_ok = is_model_present(models)
        self._set_model_section_enabled(True)
        self._sync_status()
        self._refresh_continue()
        self._fit_window_height()

    def _refresh_continue(self):
        self._btn_continue.setEnabled(self._ollama_ok and self._model_ok)

    def _open_download_page(self):
        QDesktopServices.openUrl(QUrl(OLLAMA_DOWNLOAD_WINDOWS_URL))

    def _on_try_start_ollama(self):
        if _try_start_ollama_app():
            self._status_o.setText(t("setup_ollama_start_attempt"))
            self._status_o.setStyleSheet("font-size: 11px; color: #a78bfa;")
        else:
            self._status_o.setText(t("setup_ollama_start_fail"))
            self._status_o.setStyleSheet("font-size: 11px; color: #FBBF24;")
        self._fit_window_height()

    def _on_copy_pull(self):
        cmd = pull_model_command()
        QApplication.clipboard().setText(cmd)
        self._status_m.setText(t("setup_copied"))
        self._status_m.setStyleSheet("font-size: 11px; color: #a78bfa;")
        self._fit_window_height()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    dlg = AiSetupDialog()
    dlg.exec()
    sys.exit(0)
