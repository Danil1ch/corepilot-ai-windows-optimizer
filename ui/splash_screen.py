"""
Splash Screen - Экран загрузки приложения
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtSvgWidgets import QSvgWidget
import os
from utils import resource_path, get_app_qicon


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Убираем рамку окна
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        _ic = get_app_qicon()
        if not _ic.isNull():
            self.setWindowIcon(_ic)
        
        # Размер окна
        self.setFixedSize(550, 350)
        
        # Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Иконка (фиолетовая молния SVG) - оборачиваем в контейнер для центрирования
        icon_container = QWidget()
        icon_container.setStyleSheet("background: transparent;")
        icon_layout = QVBoxLayout()
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_path = resource_path(os.path.join("assets", "icons", "bolt.svg"))
        self.icon = QSvgWidget(icon_path)
        self.icon.setFixedSize(64, 64)
        self.icon.setStyleSheet("background: transparent; border: none;")
        
        icon_layout.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignCenter)
        icon_container.setLayout(icon_layout)
        
        # Добавляем opacity effect для анимации
        self.icon_opacity = QGraphicsOpacityEffect()
        self.icon_opacity.setOpacity(1.0)
        self.icon.setGraphicsEffect(self.icon_opacity)
        
        # Название приложения
        self.title = QLabel("CorePilot AI")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 38, QFont.Weight.Bold))
        self.title.setStyleSheet("color: white; background: transparent;")
        
        # Подзаголовок
        self.subtitle = QLabel("Smart PC Assistant")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setFont(QFont("Segoe UI", 15))
        self.subtitle.setStyleSheet("color: white; background: transparent;")
        
        # Версия
        self.version = QLabel("v1.0.0")
        self.version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version.setFont(QFont("Segoe UI", 10))
        self.version.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent;")
        
        # Изначально текст скрыт
        self.title.setVisible(False)
        self.subtitle.setVisible(False)
        self.version.setVisible(False)
        
        layout.addWidget(icon_container)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.version)
        
        self.setLayout(layout)
        
        # Стили с градиентом
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6B46C1,
                    stop:1 #7C3AED
                );
                border-radius: 20px;
            }
        """)
        
        # Центрируем окно на экране
        self.center_on_screen()
        
        # Запускаем анимацию
        self.setWindowOpacity(1.0)
        self.start_animations()
    
    def start_animations(self):
        """Запускает последовательность анимаций"""
        # Сразу запускаем электрический импульс
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self.electric_pulse)
    
    def electric_pulse(self):
        """Эффект электрического импульса на молнии"""
        # Группа параллельных анимаций для эффекта электричества
        self.pulse_group = QParallelAnimationGroup(self)
        
        # Только мерцание через opacity effect - без scale чтобы не было смещения
        flicker1 = QPropertyAnimation(self.icon_opacity, b"opacity")
        flicker1.setDuration(80)
        flicker1.setStartValue(1.0)
        flicker1.setEndValue(0.3)
        
        flicker2 = QPropertyAnimation(self.icon_opacity, b"opacity")
        flicker2.setDuration(80)
        flicker2.setStartValue(0.3)
        flicker2.setEndValue(1.0)
        
        flicker3 = QPropertyAnimation(self.icon_opacity, b"opacity")
        flicker3.setDuration(60)
        flicker3.setStartValue(1.0)
        flicker3.setEndValue(0.4)
        
        flicker4 = QPropertyAnimation(self.icon_opacity, b"opacity")
        flicker4.setDuration(60)
        flicker4.setStartValue(0.4)
        flicker4.setEndValue(1.0)
        
        flicker5 = QPropertyAnimation(self.icon_opacity, b"opacity")
        flicker5.setDuration(50)
        flicker5.setStartValue(1.0)
        flicker5.setEndValue(0.5)
        
        flicker6 = QPropertyAnimation(self.icon_opacity, b"opacity")
        flicker6.setDuration(50)
        flicker6.setStartValue(0.5)
        flicker6.setEndValue(1.0)
        
        # Последовательность мерцаний
        flicker_sequence = QSequentialAnimationGroup(self)
        flicker_sequence.addAnimation(flicker1)
        flicker_sequence.addAnimation(flicker2)
        flicker_sequence.addAnimation(flicker3)
        flicker_sequence.addAnimation(flicker4)
        flicker_sequence.addAnimation(flicker5)
        flicker_sequence.addAnimation(flicker6)
        
        # Запускаем только мерцание
        self.pulse_group.addAnimation(flicker_sequence)
        
        self.pulse_group.start()
        self.pulse_group.finished.connect(self.show_text)
    
    def show_text(self):
        """Показывает текст после анимации молнии"""
        self.title.setVisible(True)
        self.subtitle.setVisible(True)
        self.version.setVisible(True)
        
        # Плавное появление текста
        self.title.setStyleSheet("color: rgba(255, 255, 255, 0); background: transparent;")
        self.subtitle.setStyleSheet("color: rgba(255, 255, 255, 0); background: transparent;")
        self.version.setStyleSheet("color: rgba(255, 255, 255, 0); background: transparent;")
        
        # Анимация появления текста
        text_group = QParallelAnimationGroup(self)
        
        # Используем изменение stylesheet для fade in текста
        from PyQt6.QtCore import QTimer
        
        steps = 20
        duration = 500
        step_time = duration // steps
        
        def fade_text(step=0):
            if step <= steps:
                opacity = step / steps
                self.title.setStyleSheet(f"color: rgba(255, 255, 255, {opacity}); background: transparent;")
                self.subtitle.setStyleSheet(f"color: rgba(255, 255, 255, {opacity}); background: transparent;")
                self.version.setStyleSheet(f"color: rgba(255, 255, 255, {opacity * 0.6}); background: transparent;")
                QTimer.singleShot(step_time, lambda: fade_text(step + 1))
        
        fade_text()

    
    def center_on_screen(self):
        """Центрирует окно на экране"""
        from PyQt6.QtGui import QGuiApplication
        # Получаем геометрию основного экрана
        screen = QGuiApplication.primaryScreen().availableGeometry()
        # Вычисляем центральную позицию
        x = (screen.width() - self.width()) // 2 + screen.x()
        y = (screen.height() - self.height()) // 2 + screen.y()
        self.move(x, y)
