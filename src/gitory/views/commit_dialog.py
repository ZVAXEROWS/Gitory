"""Commit dialog — staging area and commit message input."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
)

from gitory.domain.models.diff import StatusEntry, StatusResult


class CommitDialog(QDialog):
    """Dialog for staging files and creating commits.

    Signals:
        commit_requested: Emitted with (message, stage_all, push_after).
    """

    commit_requested = Signal(str, bool, bool)

    def __init__(self, status: StatusResult | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Commit Changes")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        self._status = status
        self._setup_ui()
        if status:
            self._populate_files(status)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title.
        title = QLabel("Commit Changes")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #7aa2f7;")
        layout.addWidget(title)

        # File lists.
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Staged files.
        staged_container = QVBoxLayout()
        staged_label = QLabel("Staged Changes")
        staged_label.setObjectName("sectionHeader")

        self._staged_list = QListWidget()
        staged_widget = QWidget()
        staged_layout = QVBoxLayout(staged_widget)
        staged_layout.setContentsMargins(0, 0, 0, 0)
        staged_layout.addWidget(staged_label)
        staged_layout.addWidget(self._staged_list)
        splitter.addWidget(staged_widget)

        # Unstaged files.
        unstaged_widget = QWidget()
        unstaged_layout = QVBoxLayout(unstaged_widget)
        unstaged_layout.setContentsMargins(0, 0, 0, 0)
        unstaged_label = QLabel("Unstaged Changes")
        unstaged_label.setObjectName("sectionHeader")
        unstaged_layout.addWidget(unstaged_label)

        self._unstaged_list = QListWidget()
        unstaged_layout.addWidget(self._unstaged_list)
        splitter.addWidget(unstaged_widget)

        layout.addWidget(splitter, stretch=1)

        # Stage all checkbox.
        self._stage_all_check = QCheckBox("Stage all changes before committing")
        self._stage_all_check.setChecked(True)
        layout.addWidget(self._stage_all_check)

        # Commit message.
        msg_label = QLabel("Commit Message")
        msg_label.setObjectName("sectionHeader")
        layout.addWidget(msg_label)

        self._message_edit = QPlainTextEdit()
        self._message_edit.setPlaceholderText("Enter commit message...")
        self._message_edit.setMaximumHeight(120)
        self._message_edit.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self._message_edit)

        # Buttons.
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        commit_btn = QPushButton("✅ Commit")
        commit_btn.setObjectName("primaryButton")
        commit_btn.clicked.connect(lambda: self._on_commit(push=False))
        btn_layout.addWidget(commit_btn)

        commit_push_btn = QPushButton("📤 Commit & Push")
        commit_push_btn.setObjectName("primaryButton")
        commit_push_btn.clicked.connect(lambda: self._on_commit(push=True))
        btn_layout.addWidget(commit_push_btn)

        layout.addLayout(btn_layout)

    def _populate_files(self, status: StatusResult) -> None:
        """Populate the staged and unstaged file lists."""
        for entry in status.staged_entries:
            icon = self._status_icon(entry)
            item = QListWidgetItem(f"{icon} {entry.path}")
            self._staged_list.addItem(item)

        for entry in status.unstaged_entries:
            icon = self._status_icon(entry)
            item = QListWidgetItem(f"{icon} {entry.path}")
            self._unstaged_list.addItem(item)

        for entry in status.untracked_entries:
            item = QListWidgetItem(f"? {entry.path}")
            item.setForeground(Qt.GlobalColor.gray)
            self._unstaged_list.addItem(item)

    @staticmethod
    def _status_icon(entry: StatusEntry) -> str:
        from gitory.domain.models.diff import FileStatus
        icons = {
            FileStatus.MODIFIED: "M",
            FileStatus.ADDED: "A",
            FileStatus.DELETED: "D",
            FileStatus.RENAMED: "R",
            FileStatus.COPIED: "C",
            FileStatus.UNTRACKED: "?",
        }
        status = entry.index_status if entry.is_staged else entry.worktree_status
        return icons.get(status, "·")

    def _on_commit(self, push: bool) -> None:
        message = self._message_edit.toPlainText().strip()
        if not message:
            self._message_edit.setStyleSheet(
                "QPlainTextEdit { border: 2px solid #f7768e; }"
            )
            return

        self.commit_requested.emit(message, self._stage_all_check.isChecked(), push)
        self.accept()
