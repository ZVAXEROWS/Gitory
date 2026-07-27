"""Simple dialogs for branch, tag, remote, settings, and confirmations."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

# ──────────────────────────────────────────────────────────────────────
# Branch Dialog
# ──────────────────────────────────────────────────────────────────────

class BranchDialog(QDialog):
    """Dialog for creating or renaming a branch."""

    branch_requested = Signal(str, str)  # (name, start_point)

    def __init__(self, title: str = "Create Branch", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel(title)
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #7aa2f7;")
        layout.addWidget(header)

        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("feature/my-branch")
        form.addRow("Branch Name:", self._name_edit)

        self._start_edit = QLineEdit()
        self._start_edit.setPlaceholderText("HEAD (default)")
        form.addRow("Start Point:", self._start_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        name = self._name_edit.text().strip()
        if name:
            self.branch_requested.emit(name, self._start_edit.text().strip())
            self.accept()


# ──────────────────────────────────────────────────────────────────────
# Tag Dialog
# ──────────────────────────────────────────────────────────────────────

class TagDialog(QDialog):
    """Dialog for creating a tag."""

    tag_requested = Signal(str, str, str)  # (name, message, target)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Tag")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Create Tag")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #7aa2f7;")
        layout.addWidget(header)

        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("v1.0.0")
        form.addRow("Tag Name:", self._name_edit)

        self._message_edit = QLineEdit()
        self._message_edit.setPlaceholderText("Optional annotation message")
        form.addRow("Message:", self._message_edit)

        self._target_edit = QLineEdit()
        self._target_edit.setPlaceholderText("HEAD (default)")
        form.addRow("Target:", self._target_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        name = self._name_edit.text().strip()
        if name:
            self.tag_requested.emit(
                name,
                self._message_edit.text().strip(),
                self._target_edit.text().strip() or "HEAD",
            )
            self.accept()


# ──────────────────────────────────────────────────────────────────────
# Remote Dialog
# ──────────────────────────────────────────────────────────────────────

class RemoteDialog(QDialog):
    """Dialog for adding a remote."""

    remote_requested = Signal(str, str)  # (name, url)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Remote")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Add Remote")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #7aa2f7;")
        layout.addWidget(header)

        form = QFormLayout()
        self._name_edit = QLineEdit("origin")
        form.addRow("Remote Name:", self._name_edit)

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://github.com/user/repo.git")
        form.addRow("URL:", self._url_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        name = self._name_edit.text().strip()
        url = self._url_edit.text().strip()
        if name and url:
            self.remote_requested.emit(name, url)
            self.accept()


# ──────────────────────────────────────────────────────────────────────
# Settings Dialog
# ──────────────────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    """Application settings dialog."""

    settings_changed = Signal(dict)

    def __init__(self, config, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._config = config

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Settings")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #7aa2f7;")
        layout.addWidget(header)

        # Theme.
        theme_group = QGroupBox("Appearance")
        theme_layout = QFormLayout(theme_group)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light"])
        self._theme_combo.setCurrentText(config.theme)
        theme_layout.addRow("Theme:", self._theme_combo)

        self._anim_check = QCheckBox("Enable animations")
        self._anim_check.setChecked(config.animations_enabled)
        theme_layout.addRow(self._anim_check)
        layout.addWidget(theme_group)

        # Graph.
        graph_group = QGroupBox("Graph")
        graph_layout = QFormLayout(graph_group)

        self._row_height_spin = QSpinBox()
        self._row_height_spin.setRange(20, 200)
        self._row_height_spin.setValue(config.graph_row_height)
        graph_layout.addRow("Row Height (px):", self._row_height_spin)

        self._lane_width_spin = QSpinBox()
        self._lane_width_spin.setRange(15, 100)
        self._lane_width_spin.setValue(config.graph_lane_width)
        graph_layout.addRow("Lane Width (px):", self._lane_width_spin)

        self._node_radius_spin = QSpinBox()
        self._node_radius_spin.setRange(4, 20)
        self._node_radius_spin.setValue(config.graph_node_radius)
        graph_layout.addRow("Node Radius (px):", self._node_radius_spin)

        self._max_commits_spin = QSpinBox()
        self._max_commits_spin.setRange(50, 10000)
        self._max_commits_spin.setSingleStep(100)
        self._max_commits_spin.setValue(config.graph_max_commits)
        graph_layout.addRow("Max Commits:", self._max_commits_spin)

        self._zoom_spin = QDoubleSpinBox()
        self._zoom_spin.setRange(1.01, 2.0)
        self._zoom_spin.setSingleStep(0.05)
        self._zoom_spin.setValue(config.zoom_sensitivity)
        graph_layout.addRow("Zoom Sensitivity:", self._zoom_spin)
        layout.addWidget(graph_group)

        # Git.
        git_group = QGroupBox("Git")
        git_layout = QFormLayout(git_group)
        self._git_path_edit = QLineEdit(config.git_executable)
        git_layout.addRow("Git Executable:", self._git_path_edit)
        layout.addWidget(git_group)

        # Buttons.
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults,
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._on_restore,
        )
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        self.settings_changed.emit({
            "theme": self._theme_combo.currentText(),
            "animations_enabled": self._anim_check.isChecked(),
            "graph_row_height": self._row_height_spin.value(),
            "graph_lane_width": self._lane_width_spin.value(),
            "graph_node_radius": self._node_radius_spin.value(),
            "graph_max_commits": self._max_commits_spin.value(),
            "zoom_sensitivity": self._zoom_spin.value(),
            "git_executable": self._git_path_edit.text().strip(),
        })
        self.accept()

    def _on_restore(self) -> None:
        from gitory.infrastructure.config_store import AppConfig
        defaults = AppConfig()
        self._theme_combo.setCurrentText(defaults.theme)
        self._anim_check.setChecked(defaults.animations_enabled)
        self._row_height_spin.setValue(defaults.graph_row_height)
        self._lane_width_spin.setValue(defaults.graph_lane_width)
        self._node_radius_spin.setValue(defaults.graph_node_radius)
        self._max_commits_spin.setValue(defaults.graph_max_commits)
        self._zoom_spin.setValue(defaults.zoom_sensitivity)
        self._git_path_edit.setText(defaults.git_executable)


# ──────────────────────────────────────────────────────────────────────
# Confirmation Dialog
# ──────────────────────────────────────────────────────────────────────

class ConfirmationDialog:
    """Static helper for showing destructive-action confirmation dialogs."""

    @staticmethod
    def confirm(
        parent,
        title: str,
        message: str,
        detail: str = "",
        destructive: bool = True,
    ) -> bool:
        """Show a confirmation dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Main message.
            detail: Additional detail text.
            destructive: If True, styles the confirm button as dangerous.

        Returns:
            True if the user confirmed.
        """
        box = QMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(message)
        if detail:
            box.setDetailedText(detail)
        box.setIcon(QMessageBox.Icon.Warning if destructive else QMessageBox.Icon.Question)
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        box.setDefaultButton(QMessageBox.StandardButton.No)

        return box.exec() == QMessageBox.StandardButton.Yes
