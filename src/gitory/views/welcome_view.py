"""Welcome view — landing screen for opening or initializing a repository."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class WelcomeView(QWidget):
    """Landing screen shown when no repository is open.

    Displays the app logo/name, Open and Init buttons,
    and a list of recently opened repositories.

    Signals:
        open_clicked: User wants to browse for a repository.
        init_clicked: User wants to initialize a new repository.
        recent_selected: User selected a recent repository (path string).
    """

    open_clicked = Signal()
    init_clicked = Signal()
    recent_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the welcome screen layout."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # Spacer.
        layout.addStretch(2)

        # App title.
        title = QLabel("Gitory")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        title.setStyleSheet("color: #7aa2f7;")
        layout.addWidget(title)

        # Subtitle.
        subtitle = QLabel("Visualize. Understand. Control.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #565f89;")
        layout.addWidget(subtitle)

        layout.addSpacing(32)

        # Action buttons.
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setSpacing(16)

        open_btn = QPushButton("📂  Open Repository")
        open_btn.setObjectName("primaryButton")
        open_btn.setMinimumSize(200, 48)
        open_btn.setFont(QFont("Segoe UI", 11))
        open_btn.clicked.connect(self.open_clicked.emit)
        btn_layout.addWidget(open_btn)

        init_btn = QPushButton("🆕  Initialize Repository")
        init_btn.setMinimumSize(200, 48)
        init_btn.setFont(QFont("Segoe UI", 11))
        init_btn.clicked.connect(self.init_clicked.emit)
        btn_layout.addWidget(init_btn)

        layout.addLayout(btn_layout)

        layout.addSpacing(32)

        # Recent repositories.
        recent_header = QLabel("Recent Repositories")
        recent_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        recent_header.setObjectName("sectionHeader")
        layout.addWidget(recent_header)

        self._recent_list = QListWidget()
        self._recent_list.setMaximumWidth(500)
        self._recent_list.setMaximumHeight(200)
        self._recent_list.setStyleSheet(
            "QListWidget { background-color: #16161e; border: 1px solid #292e42; "
            "border-radius: 8px; padding: 4px; }"
            "QListWidget::item { padding: 8px 12px; border-radius: 4px; margin: 2px; }"
            "QListWidget::item:hover { background-color: #292e42; }"
            "QListWidget::item:selected { background-color: #283457; color: #7aa2f7; }"
        )
        self._recent_list.itemDoubleClicked.connect(self._on_recent_selected)

        # Center the list.
        list_container = QHBoxLayout()
        list_container.addStretch()
        list_container.addWidget(self._recent_list)
        list_container.addStretch()
        layout.addLayout(list_container)

        layout.addStretch(3)

    def set_recent_repos(self, entries: list) -> None:
        """Update the recent repositories list.

        Args:
            entries: List of RecentEntry objects with path and name.
        """
        self._recent_list.clear()
        if not entries:
            item = QListWidgetItem("No recent repositories")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(Qt.GlobalColor.gray)
            self._recent_list.addItem(item)
            return

        for entry in entries:
            item = QListWidgetItem(f"📁 {entry.name}\n   {entry.path}")
            item.setData(Qt.ItemDataRole.UserRole, entry.path)
            self._recent_list.addItem(item)

    def _on_recent_selected(self, item: QListWidgetItem) -> None:
        """Handle double-click on a recent repository."""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.recent_selected.emit(path)
