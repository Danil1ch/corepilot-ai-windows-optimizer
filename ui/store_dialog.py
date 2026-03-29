from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor, QPainterPath, QPen
import os
from utils import resource_path
from core.translations import t


APPS = [
    {
        "category_ru": "Мониторинг и драйверы",
        "category_en": "Monitoring & Drivers",
        "items": [
            {"name": "NVIDIA App",             "desc_ru": "Управление драйверами и настройками видеокарт NVIDIA",   "desc_en": "Driver and GPU settings manager by NVIDIA",        "url": "https://us.download.nvidia.com/nvapp/client/11.0.6.383/NVIDIA_app_v11.0.6.383.exe"},
            {"name": "AMD Software: Adrenalin", "desc_ru": "Драйверы, настройки и мониторинг видеокарт AMD",      "desc_en": "Drivers, settings and monitoring for AMD GPUs",       "url": "https://drivers.amd.com/drivers/installer/25.30/whql/amd-software-adrenalin-edition-26.3.1-minimalsetup-260317_web.exe"},
            {"name": "Intel Arc Control",       "desc_ru": "Настройка видеокарт Arc и процессоров Intel",          "desc_en": "Tuning software for Intel Arc GPUs and processors",    "url": "https://www.intel.com/content/www/us/en/products/docs/discrete-gpus/arc/software/arc-control.html"},
            {"name": "MSI Afterburner",         "desc_ru": "Разгон и мониторинг видеокарты в реальном времени",    "desc_en": "GPU overclocking and real-time performance monitoring",  "url": "https://download.msi.com/uti_exe/vga/MSIAfterburnerSetup.zip"},
            {"name": "HWiNFO64",                "desc_ru": "Профессиональный мониторинг всех компонентов системы",          "desc_en": "Professional monitoring of all hardware components",     "url": "https://www.hwinfo.com/files/hwi64_844.exe"},
        ]
    },
    {
        "category_ru": "Игры и геймплей",
        "category_en": "Gaming",
        "items": [
            {"name": "Steam",           "desc_ru": "Магазин и лаунчер игр от Valve",         "desc_en": "Game store and launcher by Valve",   "url": "https://cdn.fastly.steamstatic.com/client/installer/SteamSetup.exe"},
            {"name": "Epic Games",      "desc_ru": "Магазин и лаунчер игр от Epic",          "desc_en": "Game store and launcher by Epic",    "url": "https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/installer/download/EpicGamesLauncherInstaller.msi"},
            {"name": "Ubisoft Connect", "desc_ru": "Лаунчер игр и платформа Ubisoft",     "desc_en": "Ubisoft game launcher and platform",  "url": "https://ubi.li/4vxt9"},
            {"name": "Discord",         "desc_ru": "Голосовой чат и мессенджер для геймеров",  "desc_en": "Voice chat and messenger for gamers", "url": "https://discord.com/api/downloads/distributions/app/installers/latest?channel=stable&platform=win&arch=x64"},
            {"name": "OBS Studio",      "desc_ru": "Запись экрана и стриминг без ограничений",  "desc_en": "Screen recording and streaming",      "url": "https://cdn-fastly.obsproject.com/downloads/OBS-Studio-32.1.0-Windows-x64-Installer.exe"},
        ]
    },
    {
        "category_ru": "Браузеры",
        "category_en": "Browsers",
        "items": [
            {"name": "Google Chrome", "desc_ru": "Быстрый браузер от Google на Chromium",    "desc_en": "Fast Chromium-based browser by Google", "url": "https://www.google.com/chrome/"},
            {"name": "Firefox",       "desc_ru": "Браузер с открытым кодом от Mozilla",    "desc_en": "Open source browser by Mozilla",       "url": "https://www.firefox.com/thanks/"},
            {"name": "Brave",         "desc_ru": "Браузер с встроенной блокировкой рекламы",  "desc_en": "Browser with built-in ad blocker",    "url": "https://laptop-updates.brave.com/download/BRV002?bitness=64"},
        ]
    },
    {
        "category_ru": "Утилиты",
        "category_en": "Utilities",
        "items": [
            {"name": "7-Zip",       "desc_ru": "Бесплатный архиватор, поддерживает ZIP, RAR, 7z",  "desc_en": "Free archiver, supports ZIP, RAR, 7z",  "url": "https://www.7-zip.org/a/7z2409-x64.exe"},
            {"name": "VLC",         "desc_ru": "Медиаплеер, играет любые форматы видео",       "desc_en": "Media player, plays any video format",  "url": "https://videolan.ip-connect.info/vlc/3.0.23/win64/vlc-3.0.23-win64.exe"},
            {"name": "Notepad++",   "desc_ru": "Текстовый редактор с подсветкой синтаксиса",   "desc_en": "Text editor with syntax highlighting",  "url": "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/latest"},
            {"name": "qBittorrent", "desc_ru": "Торрент-клиент без рекламы и спионского ПО",    "desc_en": "Torrent client, no ads or spyware",    "url": "https://sourceforge.net/projects/qbittorrent/files/latest/download"},
            {"name": "Telegram",    "desc_ru": "Быстрый мессенджер с облачными хранением",   "desc_en": "Fast messenger with cloud storage",    "url": "https://www.softportal.com/get-36716-telegram.html"},
        ]
    },
    {
        "category_ru": "Разработка",
        "category_en": "Development",
        "items": [
            {"name": "VS Code", "desc_ru": "Редактор кода от Microsoft с поддержкой расширений",  "desc_en": "Code editor by Microsoft with extensions", "url": "https://code.visualstudio.com/thank-you?dv=win64user"},
            {"name": "Python",  "desc_ru": "Интерпретатор Python для Windows",              "desc_en": "Python interpreter for Windows",          "url": "https://www.python.org/downloads/"},
            {"name": "Git",     "desc_ru": "Система контроля версий для отслеживания изменений",  "desc_en": "Version control system for tracking changes", "url": "https://github.com/git-for-windows/git/releases/latest"},
        ]
    },
]


ICON_MAP = {
    "NVIDIA App":             "nvidia.svg",
    "AMD Software: Adrenalin": "amd.svg",
    "Intel Arc Control":       "intel.svg",
    "MSI Afterburner":         "msiafterburner.svg",
    "HWiNFO64":                "hwinfo64.svg",
    "Steam":                   "steam.svg",
    "Epic Games":              "epicgames.svg",
    "Ubisoft Connect":         "ubisoft.svg",
    "Discord":                 "discord.svg",
    "OBS Studio":              "obs.svg",
    "Google Chrome":           "chrome.svg",
    "Firefox":                 "firefox.svg",
    "Brave":                   "brave.svg",
    "7-Zip":                   "7zip.svg",
    "VLC":                     "vlc.svg",
    "Notepad++":               "notepadpp.svg",
    "qBittorrent":             "qbittorrent.svg",
    "Telegram":                "telegram.svg",
    "VS Code":                 "vscode.svg",
    "Python":                  "python.svg",
    "Git":                     "git.svg",
}


class StoreDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CorePilot Store")
        self.setFixedSize(720, 620)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setStyleSheet("""
            QPushButton#install_btn {
                background: transparent;
                border: 1px solid #6B46C1;
                border-radius: 6px;
                padding: 5px 14px;
                color: #a78bfa;
                font-family: 'Segoe UI';
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton#install_btn:hover { background: #6B46C1; color: #ffffff; }
            QPushButton#close_btn {
                background: transparent;
                border: none;
            }
            QPushButton#close_btn:hover { opacity: 0.7; }
        """)

        # Шапка
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 16, 0)
        header_layout.setSpacing(10)

        from PyQt6.QtSvgWidgets import QSvgWidget
        store_icon = QSvgWidget(resource_path(os.path.join("assets", "icons", "store.svg")))

        store_icon.setFixedSize(18, 18)
        store_icon.setStyleSheet("background: transparent; border: none;")

        title = QLabel(t("shop_title"))
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")

        from PyQt6.QtSvgWidgets import QSvgWidget as SvgW
        close_icon = SvgW(resource_path(os.path.join("assets", "icons", "store_close.svg")))
        close_icon.setFixedSize(20, 20)
        close_icon.setStyleSheet("background: transparent; border: none;")

        close_btn = QPushButton()
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_btn_layout = QHBoxLayout(close_btn)
        close_btn_layout.setContentsMargins(4, 4, 4, 4)
        close_btn_layout.addWidget(close_icon)

        header_layout.addWidget(store_icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)

        # Разделитель
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #3a2a5a;")

        # Скролл с приложениями
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setContentsMargins(0, 0, 0, 0)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical { background: transparent; width: 6px; border-radius: 3px; margin: 0px; }
            QScrollBar::handle:vertical { background: #6B46C1; border-radius: 3px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #7C3AED; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: #2a1a4a; border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(16, 4, 16, 20)
        scroll_layout.setSpacing(0)

        from core.language import get_language
        lang = get_language()

        for category in APPS:
            cat_label = QLabel((category["category_en"] if lang == "en" else category["category_ru"]).upper())
            cat_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            cat_label.setStyleSheet("color: #8B5CF6; background: transparent; padding-top: 14px; padding-bottom: 4px; letter-spacing: 1px;")
            scroll_layout.addWidget(cat_label)


            for app in category["items"]:
                item = self._create_app_item(app, lang)
                scroll_layout.addWidget(item)
                scroll_layout.addSpacing(3)

        scroll_layout.addSpacing(16)
        scroll.setWidget(scroll_content)

        layout.addWidget(header)
        layout.addWidget(divider)
        layout.addWidget(scroll)
        layout.addSpacing(12)

    def _create_app_item(self, app: dict, lang: str) -> QWidget:
        item = QWidget()
        item.setFixedHeight(62)
        item.setObjectName("app_item")
        item.setStyleSheet("""
            QWidget#app_item {
                background: #16082a;
                border-radius: 8px;
                border: 1px solid #2a1a4a;
            }
            QWidget#app_item:hover {
                background: #1e1040;
                border: 1px solid #6B46C1;
            }
            QLabel { background: transparent; border: none; }
        """)
        layout = QHBoxLayout(item)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Иконка
        icon_file = ICON_MAP.get(app["name"])
        if icon_file:
            from PyQt6.QtSvgWidgets import QSvgWidget
            icon_path = resource_path(os.path.join("assets", "icons", "shop", icon_file))
            icon = QSvgWidget(icon_path)
            icon.setFixedSize(36, 36)
            icon.setStyleSheet("background: transparent; border: none;")
            layout.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(1)
        info.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        name = QLabel(app["name"])
        name.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name.setStyleSheet("color: #ffffff;")

        desc = QLabel(app["desc_en"] if lang == "en" else app["desc_ru"])
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet("color: #a0a0a0;")

        info.addWidget(name)
        info.addWidget(desc)

        btn = QPushButton("Install" if lang == "en" else "Установить")
        btn.setObjectName("install_btn")
        btn.setFixedSize(130, 34)
        btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda checked, url=app["url"]: self._open_url(url))

        layout.addLayout(info)
        layout.addStretch()
        layout.addWidget(btn)

        return item

    def _open_url(self, url: str):
        import webbrowser
        webbrowser.open(url)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        painter.fillPath(path, QColor("#1e1035"))
        painter.setPen(QPen(QColor("#8B5CF6"), 1))
        painter.drawPath(path)
