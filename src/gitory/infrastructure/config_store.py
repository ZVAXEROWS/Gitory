"""Application configuration store.

Persists user preferences and settings to a JSON file.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


def _default_config_dir() -> Path:
    """Return the default configuration directory."""
    return Path.home() / ".gitory"


@dataclass(slots=True)
class AppConfig:
    """Application settings.

    Attributes:
        theme: Current theme name ('dark' or 'light').
        animations_enabled: Whether UI animations are active.
        graph_row_height: Vertical spacing between graph rows (px).
        graph_lane_width: Horizontal spacing between graph lanes (px).
        graph_node_radius: Radius of commit node circles (px).
        zoom_sensitivity: Zoom factor per scroll tick (1.0 = no zoom).
        git_executable: Path to the git binary.
        graph_max_commits: Maximum commits to load initially.
        font_size: Base font size in points.
        show_terminal: Whether the terminal panel is visible.
        window_width: Last window width.
        window_height: Last window height.
        window_x: Last window X position.
        window_y: Last window Y position.
        window_maximized: Whether the window was maximized.
    """

    theme: str = "dark"
    animations_enabled: bool = True
    graph_row_height: int = 50
    graph_lane_width: int = 30
    graph_node_radius: int = 8
    zoom_sensitivity: float = 1.15
    git_executable: str = "git"
    graph_max_commits: int = 500
    font_size: int = 10
    show_terminal: bool = True
    window_width: int = 1400
    window_height: int = 900
    window_x: int = -1
    window_y: int = -1
    window_maximized: bool = False


class ConfigStore:
    """Manages application configuration persistence.

    Loads from and saves to ~/.gitory/config.json.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the config store.

        Args:
            config_dir: Directory for config files. Defaults to ~/.gitory.
        """
        self._config_dir = config_dir or _default_config_dir()
        self._file = self._config_dir / "config.json"
        self._config = AppConfig()
        self._load()

    @property
    def config(self) -> AppConfig:
        """Current application configuration."""
        return self._config

    def save(self) -> None:
        """Persist the current configuration to disk."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        data = asdict(self._config)
        self._file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.debug("Configuration saved to %s", self._file)

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self._config = AppConfig()
        self.save()

    def _load(self) -> None:
        """Load configuration from disk, falling back to defaults."""
        if not self._file.exists():
            return

        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            # Only update fields that exist in the dataclass to handle
            # config evolution gracefully (new fields get defaults).
            valid_fields = {f.name for f in self._config.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_fields}
            self._config = AppConfig(**filtered)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Failed to load config, using defaults: %s", e)
            self._config = AppConfig()
