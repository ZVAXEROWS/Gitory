"""Settings view model.

Manages application preferences and theme switching.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from gitory.infrastructure.config_store import AppConfig, ConfigStore


class SettingsViewModel(QObject):
    """ViewModel for the settings dialog.

    Signals:
        config_changed: Emitted when any setting is updated.
        theme_changed: Emitted with the new theme name.
    """

    config_changed = Signal()
    theme_changed = Signal(str)

    def __init__(self, config_store: ConfigStore, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._store = config_store

    @property
    def config(self) -> AppConfig:
        """Current configuration."""
        return self._store.config

    def set_theme(self, theme: str) -> None:
        """Switch the application theme."""
        self._store.config.theme = theme
        self._store.save()
        self.theme_changed.emit(theme)

    def set_git_executable(self, path: str) -> None:
        """Update the git executable path."""
        self._store.config.git_executable = path
        self._store.save()
        self.config_changed.emit()

    def set_graph_settings(
        self,
        row_height: int | None = None,
        lane_width: int | None = None,
        node_radius: int | None = None,
        max_commits: int | None = None,
    ) -> None:
        """Update graph visualization settings."""
        cfg = self._store.config
        if row_height is not None:
            cfg.graph_row_height = row_height
        if lane_width is not None:
            cfg.graph_lane_width = lane_width
        if node_radius is not None:
            cfg.graph_node_radius = node_radius
        if max_commits is not None:
            cfg.graph_max_commits = max_commits
        self._store.save()
        self.config_changed.emit()

    def set_animations_enabled(self, enabled: bool) -> None:
        """Toggle UI animations."""
        self._store.config.animations_enabled = enabled
        self._store.save()
        self.config_changed.emit()

    def set_zoom_sensitivity(self, value: float) -> None:
        """Update zoom sensitivity."""
        self._store.config.zoom_sensitivity = max(1.01, min(2.0, value))
        self._store.save()
        self.config_changed.emit()

    def save_window_state(self, width: int, height: int, x: int, y: int, maximized: bool) -> None:
        """Persist the window geometry."""
        cfg = self._store.config
        cfg.window_width = width
        cfg.window_height = height
        cfg.window_x = x
        cfg.window_y = y
        cfg.window_maximized = maximized
        self._store.save()

    def reset_defaults(self) -> None:
        """Reset all settings to defaults."""
        self._store.reset_to_defaults()
        self.config_changed.emit()
        self.theme_changed.emit(self._store.config.theme)
