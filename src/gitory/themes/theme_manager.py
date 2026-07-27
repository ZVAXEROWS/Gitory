"""Theme manager.

Loads and applies QSS stylesheets for the application.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

# Directory containing QSS theme files.
_THEMES_DIR = Path(__file__).parent

# Available themes.
AVAILABLE_THEMES = {
    "dark": _THEMES_DIR / "dark.qss",
    "light": _THEMES_DIR / "light.qss",
}


class ThemeManager:
    """Loads and applies QSS themes to the application."""

    def __init__(self, app: QApplication) -> None:
        """Initialize the theme manager.

        Args:
            app: The QApplication instance to style.
        """
        self._app = app
        self._current_theme = ""

    @property
    def current_theme(self) -> str:
        """Name of the currently applied theme."""
        return self._current_theme

    @property
    def available_themes(self) -> list[str]:
        """List of available theme names."""
        return list(AVAILABLE_THEMES.keys())

    def apply_theme(self, name: str) -> bool:
        """Apply a theme by name.

        Args:
            name: Theme name ('dark' or 'light').

        Returns:
            True if the theme was applied successfully.
        """
        path = AVAILABLE_THEMES.get(name)
        if not path or not path.exists():
            logger.warning("Theme not found: %s", name)
            return False

        try:
            qss = path.read_text(encoding="utf-8")
            self._app.setStyleSheet(qss)
            self._current_theme = name
            logger.info("Applied theme: %s", name)
            return True
        except OSError as e:
            logger.error("Failed to load theme %s: %s", name, e)
            return False

    def toggle_theme(self) -> str:
        """Toggle between dark and light themes.

        Returns:
            Name of the newly applied theme.
        """
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.apply_theme(new_theme)
        return new_theme
