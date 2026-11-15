import os
import sys
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QWidget
import qtawesome as qta

THEMES: dict[str, dict[str, str]] = {
    "light": {
        "BG_MAIN": "#f1f5f9",
        "BG_CARD": "#ffffff",
        "BG_CARD_HOVER": "#f8fafc",
        "BG_INPUT": "#f8fafc",
        "BG_SEGMENT": "#e2e8f0",
        "BG_HEADER": "#f8fafc",
        "SIDEBAR_BG": "#1e293b",
        "SIDEBAR_HOVER": "#334155",
        "SIDEBAR_ACTIVE": "#0f172a",
        "SIDEBAR_BORDER": "#1e293b",
        "BORDER": "#cbd5e1",
        "BORDER_LIGHT": "#e2e8f0",
        "TEXT_PRIMARY": "#0f172a",
        "TEXT_SECONDARY": "#334155",
        "TEXT_MUTED": "#64748b",
        "ICON_NEUTRAL": "#1e293b",
        "DONUT_EMPTY": "#e2e8f0",
        "PERIOD_ACTIVE_BG": "#0f172a",
        "PERIOD_ACTIVE_TEXT": "#ffffff",
        "SELECT_BG": "#dbeafe",
        "SELECT_TEXT": "#1e3a8a",
        "DANGER_BG": "#ffffff",
        "DANGER_HOVER": "#fef2f2",
        "DANGER_BORDER": "#fecaca",
        "DANGER_TEXT": "#dc2626",
    },
    "dark": {
        "BG_MAIN": "#0f172a",
        "BG_CARD": "#1e293b",
        "BG_CARD_HOVER": "#263348",
        "BG_INPUT": "#0f172a",
        "BG_SEGMENT": "#1e293b",
        "BG_HEADER": "#162032",
        "SIDEBAR_BG": "#090e1a",
        "SIDEBAR_HOVER": "#1e293b",
        "SIDEBAR_ACTIVE": "#172033",
        "SIDEBAR_BORDER": "#1e293b",
        "BORDER": "#334155",
        "BORDER_LIGHT": "#334155",
        "TEXT_PRIMARY": "#f8fafc",
        "TEXT_SECONDARY": "#cbd5e1",
        "TEXT_MUTED": "#94a3b8",
        "ICON_NEUTRAL": "#f1f5f9",
        "DONUT_EMPTY": "#334155",
        "PERIOD_ACTIVE_BG": "#3b82f6",
        "PERIOD_ACTIVE_TEXT": "#ffffff",
        "SELECT_BG": "#1d4ed8",
        "SELECT_TEXT": "#ffffff",
        "DANGER_BG": "#1e293b",
        "DANGER_HOVER": "#3f1d24",
        "DANGER_BORDER": "#7f1d1d",
        "DANGER_TEXT": "#f87171",
    },
}


class ThemeManager(QObject):
    """Zarządza aktualnym motywem (light / dark) i powiadamia widoki o zmianie."""

    theme_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.current_mode: str = "light"

    def get_colors(self) -> dict[str, str]:
        return THEMES[self.current_mode]

    def toggle_theme(self) -> None:
        new_mode = "dark" if self.current_mode == "light" else "light"
        self.set_theme(new_mode)

    def set_theme(self, mode: str) -> None:
        if mode not in THEMES:
            return
        self.current_mode = mode
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_stylesheet(app, mode)
        self.theme_changed.emit(mode)


theme_manager = ThemeManager()


def get_resource_path(relative_path: str) -> str:
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


def apply_stylesheet(app: QApplication, mode: str = "light") -> None:
    """Wczytuje plik style.qss i podstawia kolory wybranego motywu."""
    qss_path = get_resource_path("style.qss")
    if not os.path.exists(qss_path):
        return

    with open(qss_path, "r", encoding="utf-8") as file:
        qss_content = file.read()

    palette = THEMES[mode]
    for token, hex_value in palette.items():
        qss_content = qss_content.replace(f"__{token}__", hex_value)

    app.setStyleSheet(qss_content)


def get_safe_icon(icon_name: str, color: str | None = None) -> QIcon:
    """Pobiera ikonę qtawesome; jeśli kolor nie jest podany, dopasowuje go do motywu."""
    resolved_color = color or theme_manager.get_colors()["ICON_NEUTRAL"]
    try:
        return qta.icon(icon_name, color=resolved_color)
    except Exception:
        return qta.icon("fa5s.circle", color=resolved_color)


def apply_card_shadow(widget: QWidget) -> None:
    """Dodaje miękki cień pod kartą."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(18)
    shadow.setOffset(0, 3)
    shadow.setColor(QColor(0, 0, 0, 35))
    widget.setGraphicsEffect(shadow)