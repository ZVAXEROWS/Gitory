"""Init wizard — dialog for initializing a new Git repository."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class InitWizard(QDialog):
    """Dialog for initializing a new Git repository.

    Lets the user choose a directory, set a name, and select
    which scaffold files to create (README, .gitignore, LICENSE).

    Signals:
        init_requested: Emitted with (path, name, readme, gitignore, license).
    """

    init_requested = Signal(Path, str, bool, bool, bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Initialize New Repository")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title.
        title = QLabel("Initialize New Repository")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #7aa2f7;")
        layout.addWidget(title)

        # Path.
        path_label = QLabel("Repository Path")
        path_label.setObjectName("sectionHeader")
        layout.addWidget(path_label)

        path_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Select a folder...")
        path_row.addWidget(self._path_edit, stretch=1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        # Name.
        name_label = QLabel("Repository Name")
        name_label.setObjectName("sectionHeader")
        layout.addWidget(name_label)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("My Project")
        layout.addWidget(self._name_edit)

        # Scaffold options.
        options_label = QLabel("Initial Files")
        options_label.setObjectName("sectionHeader")
        layout.addWidget(options_label)

        self._readme_check = QCheckBox("Create README.md")
        self._readme_check.setChecked(True)
        layout.addWidget(self._readme_check)

        self._gitignore_check = QCheckBox("Create .gitignore")
        self._gitignore_check.setChecked(True)
        layout.addWidget(self._gitignore_check)

        self._license_check = QCheckBox("Create MIT License")
        self._license_check.setChecked(False)
        layout.addWidget(self._license_check)

        layout.addStretch()

        # Buttons.
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        init_btn = QPushButton("Initialize Repository")
        init_btn.setObjectName("primaryButton")
        init_btn.clicked.connect(self._on_init)
        btn_layout.addWidget(init_btn)

        layout.addLayout(btn_layout)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self._path_edit.setText(path)
            if not self._name_edit.text():
                self._name_edit.setText(Path(path).name)

    def _on_init(self) -> None:
        path_text = self._path_edit.text().strip()
        if not path_text:
            return

        self.init_requested.emit(
            Path(path_text),
            self._name_edit.text().strip(),
            self._readme_check.isChecked(),
            self._gitignore_check.isChecked(),
            self._license_check.isChecked(),
        )
        self.accept()
