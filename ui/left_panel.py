"""
Left Panel - Системная информация + кнопки действий
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QScrollArea, QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from ui.action_row import ActionRow
import os
import re
from utils import resource_path, data_file_path
from core.translations import t, power_plan_display_name
from core.language import lang_manager


# ---------- Блок пресетов ----------
class PresetSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._title_label = None
        self._build_ui()
        lang_manager.language_changed.connect(self.retranslate)

    def retranslate(self):
        if self._title_label:
            self._title_label.setText(t("presets"))
        preset_keys = ["preset_gaming", "preset_streaming", "preset_developer", "preset_everyday", "preset_cleanup", "preset_all"]
        pid_list = ["gaming", "streaming", "developer", "everyday", "cleanup", "all"]
        for pid, key in zip(pid_list, preset_keys):
            if pid in self.preset_buttons:
                self.preset_buttons[pid].setText(f"  {t(key)}")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 4)
        header.setSpacing(8)

        bolt_path = resource_path(os.path.join("assets", "icons", "presets.svg"))
        bolt_icon = QSvgWidget(bolt_path)
        bolt_icon.setFixedSize(18, 18)
        bolt_icon.setStyleSheet("background: transparent; border: none;")

        self._title_label = title = QLabel(t("presets"))
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")

        header.addWidget(bolt_icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        presets = [
            (t("preset_gaming"),      "gaming",    "gaming.svg"),
            (t("preset_streaming"),   "streaming", "streaming.svg"),
            (t("preset_developer"),   "developer", "developer.svg"),
            (t("preset_everyday"),    "everyday",  "everyday.svg"),
            (t("preset_cleanup"),     "cleanup",   "cleanup.svg"),
            (t("preset_all"),         "all",       "all_actions.svg"),
        ]
        self.preset_buttons = {}
        for label, pid, icon_file in presets:
            btn = QPushButton(f"  {label}")
            btn.setFont(QFont("Segoe UI", 10))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(pid == "all")
            btn.setMinimumHeight(38)
            icon_path = resource_path(os.path.join("assets", "icons", icon_file))
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(18, 18))
            btn.setStyleSheet("""
                QPushButton {
                    background: #1a1a1a;
                    border: 1px solid #2a2a2a;
                    border-left: 3px solid #6B46C1;
                    border-radius: 8px;
                    padding: 8px 12px;
                    color: #e0e0e0;
                    text-align: left;
                }
                QPushButton:hover { background: #242424; color: #ffffff; border-color: #6B46C1; border-left-color: #6B46C1; }
                QPushButton:checked { background: #2a1f4a; color: #a78bfa; border-left-color: #a78bfa; }
            """)
            btn.clicked.connect(lambda checked, p=pid, b=btn: self._select(p, b))
            layout.addWidget(btn)
            self.preset_buttons[pid] = btn

    preset_changed = pyqtSignal(str)

    def _select(self, preset_id: str, clicked_btn: QPushButton):
        for pid, btn in self.preset_buttons.items():
            btn.setChecked(pid == preset_id)
        self.preset_changed.emit(preset_id)


# ---------- Поток загрузки системных данных ----------
class SystemInfoWorker(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        try:
            from system.system_info import get_system_snapshot
            data = get_system_snapshot()
        except Exception:
            data = {}
        try:
            from system.action_state import load_action_states
            # Реальное состояние Windows (для контекста / будущего). Блок «Выполнено» слева — только из Memory (AppData).
            data["_action_states"] = load_action_states()
        except Exception:
            data["_action_states"] = {}
        self.finished.emit(data)


# ---------- Левая панель ----------
class LeftPanel(QWidget):
    action_clicked = pyqtSignal(dict)
    rollback_clicked = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.system_data = {}
        self.all_actions_visible = False
        self.action_buttons = []
        self._section_labels = []
        self._current_preset = "all"
        self.init_ui()
        self.load_system_info()
        lang_manager.language_changed.connect(self.retranslate)

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(16)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        icon_container = QWidget()
        icon_container.setStyleSheet("background: transparent;")
        icon_layout = QVBoxLayout()
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        laptop_path = resource_path(os.path.join("assets", "icons", "laptop.svg"))
        laptop_icon = QSvgWidget(laptop_path)
        laptop_icon.setFixedSize(32, 32)
        laptop_icon.setStyleSheet("background: transparent; border: none;")
        icon_layout.addWidget(laptop_icon, 0, Qt.AlignmentFlag.AlignCenter)
        icon_container.setLayout(icon_layout)

        self._header_label = header = QLabel(t("system_info"))
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(icon_container)
        header_layout.addWidget(header)
        self.main_layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.info_container = QWidget()
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(8)

        self._build_placeholder_cards()

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #0f0f0f; border: none;")
        self.info_layout.addWidget(divider)

        self.preset_section = PresetSection()
        self.preset_section.preset_changed.connect(self._on_preset_changed)
        self.info_layout.addWidget(self.preset_section)

        actions_header_layout = QHBoxLayout()
        actions_header_layout.setSpacing(8)
        actions_header_layout.setContentsMargins(0, 0, 0, 0)

        bolt_path = resource_path(os.path.join("assets", "icons", "bolt.svg"))
        bolt_icon = QSvgWidget(bolt_path)
        bolt_icon.setFixedSize(18, 18)
        bolt_icon.setStyleSheet("background: transparent; border: none;")

        self._actions_header = actions_header = QLabel(t("actions"))
        actions_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        actions_header.setStyleSheet("color: #ffffff; background: transparent;")

        actions_header_layout.addWidget(bolt_icon)
        actions_header_layout.addWidget(actions_header)
        actions_header_layout.addStretch()
        self.info_layout.addLayout(actions_header_layout)

        self.actions_container = QVBoxLayout()
        self.actions_container.setSpacing(6)
        self.info_layout.addLayout(self.actions_container)

        self.toggle_btn = QPushButton(t("show_all"))
        self.toggle_btn.setFont(QFont("Segoe UI", 10))
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 8px;
                color: #888888;
            }
            QPushButton:hover { color: #ffffff; border-color: #6B46C1; }
        """)
        self.toggle_btn.clicked.connect(self.toggle_actions)
        self.info_layout.addWidget(self.toggle_btn)

        self.info_layout.addStretch()
        self.info_container.setLayout(self.info_layout)
        scroll.setWidget(self.info_container)
        self.main_layout.addWidget(scroll)

        # Разделитель перед кнопкой удаления
        footer_divider = QFrame()
        footer_divider.setFrameShape(QFrame.Shape.HLine)
        footer_divider.setFixedHeight(1)
        footer_divider.setStyleSheet("background-color: #0f0f0f; border: none;")
        self.main_layout.addWidget(footer_divider)

        # Кнопка удаления — вне скролла, всегда видна
        self._uninstall_btn = self._create_uninstall_button()
        self.main_layout.addWidget(self._uninstall_btn)

        self.setLayout(self.main_layout)

        self._build_action_buttons()

        self.setStyleSheet("""
            QWidget { background-color: #0f0f0f; color: #e0e0e0; }
            QLabel { background: transparent; }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: transparent; width: 6px; margin: 0px 2px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #6B46C1; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #7C3AED; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #1a1a1a; border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

    def retranslate(self):
        self._header_label.setText(t("system_info"))
        self._actions_header.setText(t("actions"))
        self.toggle_btn.setText(t("collapse") if self.all_actions_visible else t("show_all"))
        # Обновляем карточки системной информации (лейблы)
        card_keys = ["cpu", "gpu", "ram", "disk", "power", "startup", "windows"]
        for key, card in zip(card_keys, self._info_label_widgets):
            card.setText(t(key))
        # Пересобираем action кнопки с новым языком
        self.rebuild_action_buttons()
        self._update_uninstall_btn_text()
        if self.system_data:
            self._update_info_cards()

    def _build_placeholder_cards(self):
        self.info_cards = {}
        self._info_label_widgets = []
        params = [
            ("cpu.svg",     t("cpu"),     "cpu"),
            ("gpu.svg",     t("gpu"),     "gpu"),
            ("ram.svg",     t("ram"),     "ram"),
            ("disk.svg",    t("disk"),    "disk"),
            ("power.svg",   t("power"),   "power"),
            ("startup.svg", t("startup"), "startup"),
            ("windows.svg", t("windows"), "windows"),
        ]
        for icon_file, label, key in params:
            card, value_widget, label_widget = self._create_info_card(icon_file, label, t("analyzing"))
            self.info_cards[key] = value_widget
            self._info_label_widgets.append(label_widget)
            self.info_layout.addWidget(card)

    def _update_info_cards(self):
        d = self.system_data

        cpu = d.get("cpu", t("unknown"))
        cpu = re.sub(r'\s+\d+-Core.*$', '', cpu).strip()

        gpu = d.get("gpu", t("unknown"))
        gpu = gpu.replace("NVIDIA ", "").replace("GeForce ", "").replace("Radeon ", "")

        ram_gb = d.get("ram_gb", 0)
        ram = f"{ram_gb} GB" if ram_gb else t("unknown")

        disk_gb = d.get("disk_total_gb", 0)
        disk_type = d.get("disk_type", "")
        disk_free = d.get("disk_free_gb", 0)
        disk = t("disk_free", type=disk_type, free=disk_free, total=disk_gb) if disk_gb else t("unknown")

        startup_count = d.get("startup_apps_count", None)
        startup = t("startup_apps", count=startup_count) if startup_count is not None else t("unknown")

        windows = d.get("windows_full_name", t("unknown"))
        power = power_plan_display_name(
            d.get("power_plan_guid"),
            d.get("power_plan") or "",
        )

        values = {
            "cpu": cpu, "gpu": gpu, "ram": ram, "disk": disk,
            "power": power, "startup": startup, "windows": windows,
        }
        for key, widget in self.info_cards.items():
            val = values.get(key, t("unknown"))
            fm = widget.fontMetrics()
            elided = fm.elidedText(val, Qt.TextElideMode.ElideRight, 260)
            widget.setText(elided)
            widget.setToolTip(val)

    def _create_info_card(self, icon_file, label, value):
        card = QWidget()
        card.setObjectName("info_card")
        card.setFixedHeight(70)

        layout = QHBoxLayout()
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        icon_path = resource_path(os.path.join("assets", "icons", icon_file))
        if os.path.exists(icon_path):
            svg = QSvgWidget(icon_path)
            svg.setFixedSize(32, 32)
            svg.setStyleSheet("background: transparent; border: none;")
        else:
            svg = QLabel("?")
            svg.setFixedSize(32, 32)
            svg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            svg.setStyleSheet("color: #6B46C1; font-size: 18px; background: transparent;")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        label_w = QLabel(label)
        label_w.setFont(QFont("Segoe UI", 9))
        label_w.setStyleSheet("color: #8b8b8b; background: transparent;")

        value_w = QLabel(value)
        value_w.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        value_w.setStyleSheet("color: #ffffff; background: transparent;")

        text_layout.addWidget(label_w)
        text_layout.addWidget(value_w)

        layout.addWidget(svg)
        layout.addLayout(text_layout)
        layout.addStretch()
        card.setLayout(layout)
        card.setStyleSheet("""
            QWidget#info_card {
                background-color: #1a1a1a;
                border-radius: 10px;
                border: none;
            }
        """)
        return card, value_w, label_w

    def _make_section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet("color: #666666; background: transparent; padding: 6px 0px 2px 4px;")
        return lbl

    def _build_action_buttons(self):
        from core.prompt_builder import load_actions
        from core.recommendation_engine import get_recommendations
        from core.memory import Memory

        actions = load_actions()
        if not actions:
            no_actions = QLabel(t("actions_not_loaded"))
            no_actions.setStyleSheet("color: #888888; background: transparent;")
            self.actions_container.addWidget(no_actions)
            self.toggle_btn.setVisible(False)
            return

        valid_ids = {a["id"] for a in actions}
        actions_map = {a["id"]: a for a in actions}
        HIDDEN_IDS = {"self_destruct"}

        memory = Memory()
        memory_ids = {aid for aid in memory.completed_actions if aid in valid_ids}
        applied_ids = list(memory_ids)

        EVENT_CATEGORIES = {"cleanup", "network"}

        result = get_recommendations(self.system_data, actions, applied_ids)
        recommended = [a for a in result["recommended"] if a["id"] not in HIDDEN_IDS]
        neutral     = [a for a in result["neutral"]     if a["id"] not in HIDDEN_IDS]
        caution     = [a for a in result["caution"]     if a["id"] not in HIDDEN_IDS]

        corepilot_applied = [
            actions_map[aid] for aid in memory_ids
            if aid in actions_map and aid not in HIDDEN_IDS
        ]

        self.action_buttons  = []
        self._section_labels = []
        TOP_N = 5
        shown = 0
        seen = set()

        for action in recommended + neutral + caution:
            aid = action["id"]
            if aid in seen:
                continue
            seen.add(aid)
            row = self._create_action_row(action, applied=False)
            self.action_buttons.append((row, aid))
            self.actions_container.addWidget(row)
            row.setVisible(shown < TOP_N)
            shown += 1

        rec_extra = [a for a in recommended[TOP_N:] if a["id"] not in seen]
        if rec_extra:
            lbl = self._make_section_label(t("section_recommended"))
            self.actions_container.addWidget(lbl)
            self._section_labels.append(lbl)
            lbl.setVisible(False)
            for action in rec_extra:
                seen.add(action["id"])
                row = self._create_action_row(action, applied=False)
                self.action_buttons.append((row, action["id"]))
                self.actions_container.addWidget(row)
                row.setVisible(False)

        other = [a for a in neutral + caution if a["id"] not in seen]
        if other:
            lbl = self._make_section_label(t("section_other"))
            self.actions_container.addWidget(lbl)
            self._section_labels.append(lbl)
            lbl.setVisible(False)
            for action in other:
                seen.add(action["id"])
                row = self._create_action_row(action, applied=False)
                self.action_buttons.append((row, action["id"]))
                self.actions_container.addWidget(row)
                row.setVisible(False)

        cp_deduped = [a for a in corepilot_applied if a["id"] not in seen]
        if cp_deduped:
            lbl = self._make_section_label(t("section_done"))
            self.actions_container.addWidget(lbl)
            self._section_labels.append(lbl)
            lbl.setVisible(False)
            for action in cp_deduped:
                seen.add(action["id"])
                is_event = action.get("category") in EVENT_CATEGORIES
                row = self._create_action_row(action, applied=True, is_event=is_event)
                self.action_buttons.append((row, action["id"]))
                self.actions_container.addWidget(row)
                row.setVisible(False)

        if len(self.action_buttons) <= TOP_N:
            self.toggle_btn.setVisible(False)

    def _create_uninstall_button(self) -> QWidget:
        container = QWidget()
        container.setFixedHeight(48)
        container.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(25, 7, 25, 7)

        trash_normal = resource_path(os.path.join("assets", "icons", "trash.svg"))
        trash_red    = resource_path(os.path.join("assets", "icons", "trash_red.svg"))

        btn = QPushButton(f"  {t('uninstall_btn')}")
        btn.setFont(QFont("Segoe UI", 10))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(34)
        btn.setIcon(QIcon(trash_normal))
        btn.setIconSize(QSize(14, 14))
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 0px 14px;
                color: #555555;
                text-align: center;
            }
            QPushButton:hover {
                background: #1a1a1a;
                border-color: #EF4444;
                color: #EF4444;
            }
        """)

        original_enter = btn.enterEvent
        original_leave = btn.leaveEvent

        def on_enter(e):
            btn.setIcon(QIcon(trash_red))
            original_enter(e)

        def on_leave(e):
            btn.setIcon(QIcon(trash_normal))
            original_leave(e)

        btn.enterEvent = on_enter
        btn.leaveEvent = on_leave

        btn.clicked.connect(self._on_uninstall_clicked)
        self._uninstall_btn_inner = btn
        layout.addWidget(btn)
        return container

    def _on_uninstall_clicked(self):
        from ui.uninstall_dialog import UninstallDialog
        dlg = UninstallDialog(parent=self.window())
        dlg.exec()

    def _update_uninstall_btn_text(self):
        if hasattr(self, '_uninstall_btn_inner'):
            self._uninstall_btn_inner.setText(f"  {t('uninstall_btn')}")

    def _create_action_row(self, action: dict, applied: bool = False, is_event: bool = False) -> ActionRow:
        row = ActionRow(action, is_event=is_event)
        row.action_clicked.connect(self.action_clicked)
        row.rollback_clicked.connect(self.rollback_clicked)
        if applied:
            row.set_applied()
        return row

    def _get_preset_action_ids(self, preset_id: str):
        import json
        if preset_id == "all":
            return None
        try:
            with open(data_file_path("presets.json"), "r", encoding="utf-8") as f:
                presets_data = json.load(f)
            preset = next((p for p in presets_data["presets"] if p["id"] == preset_id), None)
            if preset and preset.get("actions"):
                return set(preset["actions"])
        except Exception:
            pass
        return None

    def _apply_preset_visibility(self, preset_id: str, expanded: bool):
        preset_actions = self._get_preset_action_ids(preset_id)
        TOP_N = 5
        shown = 0

        for row, aid in self.action_buttons:
            if row._applied:
                row.setVisible(True)
                continue
            if preset_actions is None:
                row.setVisible(expanded or shown < TOP_N)
                shown += 1
            else:
                in_preset = aid in preset_actions
                row.setVisible(in_preset and (expanded or shown < TOP_N))
                if in_preset:
                    shown += 1

        for lbl in self._section_labels:
            lbl.setVisible(expanded and preset_actions is None)

        total = sum(
            1 for row, aid in self.action_buttons
            if not row._applied and (preset_actions is None or aid in preset_actions)
        )
        self.toggle_btn.setVisible(total > TOP_N)
        self.toggle_btn.setText(t("collapse") if expanded else t("show_all"))

    def _on_preset_changed(self, preset_id: str):
        self._current_preset = preset_id
        self.all_actions_visible = False
        self._apply_preset_visibility(preset_id, expanded=False)

    def toggle_actions(self):
        self.all_actions_visible = not self.all_actions_visible
        self._apply_preset_visibility(self._current_preset, expanded=self.all_actions_visible)

    def mark_action_applied(self, action_id: str):
        from core.prompt_builder import load_actions
        actions = load_actions()
        action = next((a for a in actions if a.get("id") == action_id), None)
        if not action:
            return
        for row, aid in self.action_buttons:
            if aid == action_id:
                row.set_applied()
                row.setVisible(True)
                break

    def rebuild_action_buttons(self):
        """Полная пересборка списка действий — используется после отката"""
        # Очищаем старые виджеты
        while self.actions_container.count():
            item = self.actions_container.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self.action_buttons = []
        self._section_labels = []
        self._build_action_buttons()
        self._apply_preset_visibility(self._current_preset, self.all_actions_visible)

    def mark_action_rolled_back(self, action_id: str):
        from core.memory import Memory
        Memory().unmark_completed(action_id)
        self.rebuild_action_buttons()

    def set_action_rows_ai_locked(self, locked: bool):
        """Блокирует клики по всем невыполненным действиям, пока ИИ пишет ответ."""
        for row, _aid in self.action_buttons:
            if row._applied:
                row.set_ai_lock(False)
            else:
                row.set_ai_lock(locked)

    def load_system_info(self):
        self.worker = SystemInfoWorker()
        self.worker.finished.connect(self.on_system_info_loaded)
        self.worker.start()

    def on_system_info_loaded(self, data: dict):
        self.system_data = data
        self._update_info_cards()
        # Список действий строился в init_ui с пустым system_data; пересчитываем по реальному снимку
        self.rebuild_action_buttons()

    def get_system_data(self) -> dict:
        return self.system_data
