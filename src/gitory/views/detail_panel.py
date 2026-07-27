"""Detail panel — right panel showing selected commit information."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gitory.domain.models.commit import Commit


class DetailPanel(QWidget):
    """Right-side panel displaying commit details.

    Shows full commit metadata, parent/child relationships,
    and action buttons when a commit is selected.

    Signals:
        show_diff_clicked: Emitted with SHA to view diff.
        checkout_clicked: Emitted with SHA to checkout.
        cherry_pick_clicked: Emitted with SHA to cherry-pick.
        copy_sha_clicked: Emitted with SHA to copy.
    """

    show_diff_clicked = Signal(str)
    checkout_clicked = Signal(str)
    cherry_pick_clicked = Signal(str)
    copy_sha_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("detailPanel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(450)
        self._current_sha = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the detail panel layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header.
        header = QLabel("Commit Details")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        # Scroll area for content.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(6)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # SHA.
        self._sha_label = self._add_field("SHA")
        self._sha_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # Author.
        self._author_label = self._add_field("Author")

        # Date.
        self._date_label = self._add_field("Date")

        # Message.
        self._message_label = self._add_field("Message")
        self._message_label.setWordWrap(True)

        # Parents.
        self._parents_label = self._add_field("Parents")

        # Branches.
        self._branches_label = self._add_field("Branches")

        # Tags.
        self._tags_label = self._add_field("Tags")

        # Spacer.
        self._content_layout.addStretch()

        # Action buttons.
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(6)

        self._diff_btn = QPushButton("📄 Show Diff")
        self._diff_btn.setObjectName("primaryButton")
        self._diff_btn.clicked.connect(lambda: self.show_diff_clicked.emit(self._current_sha))
        btn_layout.addWidget(self._diff_btn)

        self._checkout_btn = QPushButton("↩ Checkout Commit")
        self._checkout_btn.clicked.connect(lambda: self.checkout_clicked.emit(self._current_sha))
        btn_layout.addWidget(self._checkout_btn)

        self._cherry_btn = QPushButton("🍒 Cherry Pick")
        self._cherry_btn.clicked.connect(lambda: self.cherry_pick_clicked.emit(self._current_sha))
        btn_layout.addWidget(self._cherry_btn)

        self._copy_btn = QPushButton("📋 Copy SHA")
        self._copy_btn.clicked.connect(lambda: self.copy_sha_clicked.emit(self._current_sha))
        btn_layout.addWidget(self._copy_btn)

        layout.addLayout(btn_layout)

        # Initially hidden.
        self._set_visible(False)

    def show_commit(self, commit: Commit) -> None:
        """Display details for a commit.

        Args:
            commit: Commit to display.
        """
        self._current_sha = commit.sha
        self._sha_label.setText(commit.sha)
        self._author_label.setText(f"{commit.author_name} <{commit.author_email}>")
        self._date_label.setText(f"{commit.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  ({commit.relative_time})")
        self._message_label.setText(commit.message)

        parents = ", ".join(s[:7] for s in commit.parent_shas) if commit.parent_shas else "None (root commit)"
        self._parents_label.setText(parents)

        self._branches_label.setText(", ".join(commit.branches) if commit.branches else "—")
        self._tags_label.setText(", ".join(commit.tags) if commit.tags else "—")

        self._set_visible(True)

    def clear(self) -> None:
        """Clear the detail panel."""
        self._current_sha = ""
        self._set_visible(False)

    def _add_field(self, label_text: str) -> QLabel:
        """Add a labeled field to the content layout."""
        header = QLabel(label_text)
        header.setStyleSheet("color: #565f89; font-size: 9pt; font-weight: bold; margin-top: 4px;")

        value = QLabel("—")
        value.setStyleSheet("color: #c0caf5; font-size: 10pt; padding-left: 4px;")
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self._content_layout.addWidget(header)
        self._content_layout.addWidget(value)
        return value

    def _set_visible(self, visible: bool) -> None:
        """Show or hide the commit detail fields and buttons."""
        self._diff_btn.setVisible(visible)
        self._checkout_btn.setVisible(visible)
        self._cherry_btn.setVisible(visible)
        self._copy_btn.setVisible(visible)
