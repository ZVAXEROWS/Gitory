"""Application setup and dependency injection.

Creates the QApplication, initializes all services, and launches
the main window.
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from gitory.infrastructure.config_store import ConfigStore
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.repo_store import RepoStore
from gitory.themes.theme_manager import ThemeManager
from gitory.views.main_window import MainWindow

logger = logging.getLogger(__name__)


def create_app() -> tuple[QApplication, MainWindow]:
    """Create and configure the application.

    Returns:
        Tuple of (QApplication, MainWindow).
    """
    # Configure logging.
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Enable high-DPI scaling.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
    )

    # Create Qt application.
    app = QApplication(sys.argv)
    app.setApplicationName("Gitory")
    app.setApplicationDisplayName("Gitory — Git Visualizer")
    app.setOrganizationName("Gitory")
    app.setApplicationVersion("0.1.0")

    # Initialize services (dependency injection).
    config_store = ConfigStore()
    repo_store = RepoStore()
    git_executor = GitExecutor(git_binary=config_store.config.git_executable)

    # Verify git is available.
    git_check = git_executor.check_git_installed()
    if not git_check.success:
        logger.error("Git not found: %s", git_check.error_message)
        # We'll continue — the user can configure the path in settings.

    # Apply theme.
    theme_manager = ThemeManager(app)
    theme_manager.apply_theme(config_store.config.theme)

    # Create main window.
    window = MainWindow(git_executor, config_store, repo_store)

    return app, window


def run() -> int:
    """Run the application.

    Returns:
        Application exit code.
    """
    app, window = create_app()
    window.show()
    return app.exec()
