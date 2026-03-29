import sys
import os
import traceback


# Windows: без своего AppUserModelID панель задач часто показывает значок python.exe вместо приложения.
_APP_USER_MODEL_ID = "Danil1ch.CorePilot.AI.1"


def windows_set_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_APP_USER_MODEL_ID)
    except Exception:
        pass


def get_app_qicon():
    """
    Иконка окна и панели задач Windows.

    Порядок: assets/app.png (основной аватар) → assets/app.ico → rasterized assets/icons/bolt.svg.
    Вызов только после QApplication().
    """
    from PyQt6.QtGui import QIcon, QPixmap, QPainter
    from PyQt6.QtCore import Qt, QSize, QRectF
    from PyQt6.QtSvg import QSvgRenderer

    _PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)

    def _add_scaled_png(icon, png_path: str) -> bool:
        pm0 = QPixmap(png_path)
        if pm0.isNull():
            return False
        for s in _PNG_SIZES:
            icon.addPixmap(
                pm0.scaled(
                    s,
                    s,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        return True

    def _add_from_svg(icon, svg_path: str) -> bool:
        renderer = QSvgRenderer(svg_path)
        if not renderer.isValid():
            return False
        for s in _PNG_SIZES:
            pm = QPixmap(QSize(s, s))
            pm.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pm)
            renderer.render(painter, QRectF(0, 0, float(s), float(s)))
            painter.end()
            icon.addPixmap(pm)
        return True

    icon = QIcon()
    base = _app_base_dir()
    png_path = os.path.join(base, "assets", "app.png")
    ico_path = os.path.join(base, "assets", "app.ico")
    svg_path = os.path.join(base, "assets", "icons", "bolt.svg")

    if os.path.isfile(png_path) and _add_scaled_png(icon, png_path):
        return icon
    if os.path.isfile(ico_path):
        ic = QIcon(ico_path)
        if not ic.isNull():
            return ic
    if os.path.isfile(svg_path) and _add_from_svg(icon, svg_path):
        return icon
    return icon


def is_frozen_executable() -> bool:
    """True, если запущен собранный PyInstaller exe (отдельное консольное окно не используем)."""
    return getattr(sys, "frozen", False)


def cli_error(message: str) -> None:
    """В stderr только при запуске из исходников — для отладки в cmd. В exe не печатаем."""
    if is_frozen_executable():
        return
    print(message, file=sys.stderr)


def cli_traceback() -> None:
    """Текущее исключение в stderr только при запуске из исходников."""
    if is_frozen_executable():
        return
    traceback.print_exc()


def _app_base_dir() -> str:
    """Корень приложения: каталог проекта в dev, _MEIPASS при сборке PyInstaller one-file."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path: str) -> str:
    """Возвращает корректный путь к ресурсу — работает и в .py и в .exe (PyInstaller)."""
    return os.path.join(_app_base_dir(), relative_path)


def get_data_dir() -> str:
    """Каталог data (actions.json, presets.json). Для exe: положите data в bundle (PyInstaller --add-data)."""
    return os.path.join(_app_base_dir(), "data")


def data_file_path(*parts: str) -> str:
    """Путь к файлу внутри data/, без зависимости от текущей рабочей папки."""
    return os.path.join(get_data_dir(), *parts)
