"""Sidebar — left panel showing repository info, branches, tags, stashes."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gitory.domain.models.branch import Branch
from gitory.domain.models.repository import RepositoryInfo
from gitory.domain.models.stash import StashEntry
from gitory.domain.models.tag import Tag


class Sidebar(QWidget):
    """Left sidebar showing repository structure.

    Displays:
    - Repository info (name, current branch, HEAD)
    - Local branches
    - Remote branches
    - Tags
    - Stashes

    Signals:
        branch_selected: Branch name clicked.
        tag_selected: Tag name clicked.
        stash_selected: Stash index clicked.
    """

    branch_selected = Signal(str)
    tag_selected = Signal(str)
    stash_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(220)
        self.setMaximumWidth(350)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the sidebar layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Repository info header.
        self._repo_label = QLabel("No repository open")
        self._repo_label.setObjectName("sectionHeader")
        self._repo_label.setWordWrap(True)
        layout.addWidget(self._repo_label)

        self._branch_label = QLabel("")
        self._branch_label.setStyleSheet("color: #7aa2f7; font-weight: bold; padding: 2px 0;")
        layout.addWidget(self._branch_label)

        self._head_label = QLabel("")
        self._head_label.setObjectName("statusLabel")
        layout.addWidget(self._head_label)

        # Tree widget.
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.setRootIsDecorated(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._tree, stretch=1)

        # Section root items.
        self._branches_root = QTreeWidgetItem(self._tree, ["Branches"])
        self._branches_root.setExpanded(True)
        self._branches_root.setFlags(Qt.ItemFlag.ItemIsEnabled)

        self._remote_root = QTreeWidgetItem(self._tree, ["Remote Branches"])
        self._remote_root.setExpanded(True)
        self._remote_root.setFlags(Qt.ItemFlag.ItemIsEnabled)

        self._tags_root = QTreeWidgetItem(self._tree, ["Tags"])
        self._tags_root.setExpanded(False)
        self._tags_root.setFlags(Qt.ItemFlag.ItemIsEnabled)

        self._stash_root = QTreeWidgetItem(self._tree, ["Stashes"])
        self._stash_root.setExpanded(False)
        self._stash_root.setFlags(Qt.ItemFlag.ItemIsEnabled)

        # Bold section headers.
        bold_font = QFont()
        bold_font.setBold(True)
        for root in (self._branches_root, self._remote_root, self._tags_root, self._stash_root):
            root.setFont(0, bold_font)

    def update_repo_info(self, info: RepositoryInfo) -> None:
        """Update the repository info section.

        Args:
            info: Repository metadata.
        """
        self._repo_label.setText(f"Repo: {info.name}")
        branch_text = info.current_branch if not info.is_detached else "HEAD (detached)"
        self._branch_label.setText(f"Branch: {branch_text}")
        self._head_label.setText(f"HEAD: {info.head_sha[:7]}" if info.head_sha else "")

    def update_branches(self, branches: list[Branch]) -> None:
        """Update the branch lists.

        Args:
            branches: All branches (local and remote).
        """
        # Clear existing.
        self._branches_root.takeChildren()
        self._remote_root.takeChildren()

        for branch in branches:
            if branch.is_remote:
                item = QTreeWidgetItem(self._remote_root, [branch.name])
                item.setData(0, Qt.ItemDataRole.UserRole, ("remote_branch", branch.name))
                item.setToolTip(0, f"Remote branch: {branch.name}\nTip: {branch.tip_sha}")
            else:
                display = branch.name
                if branch.is_current:
                    display = f"* {branch.name}"
                item = QTreeWidgetItem(self._branches_root, [display])
                item.setData(0, Qt.ItemDataRole.UserRole, ("branch", branch.name))
                item.setToolTip(0, f"Branch: {branch.name}\nTip: {branch.tip_sha}")

                if branch.is_current:
                    item.setForeground(0, QColor("#7aa2f7"))
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)

        # Update counts in header.
        local_count = sum(1 for b in branches if not b.is_remote)
        remote_count = sum(1 for b in branches if b.is_remote)
        self._branches_root.setText(0, f"Branches ({local_count})")
        self._remote_root.setText(0, f"Remote ({remote_count})")

    def update_tags(self, tags: list[Tag]) -> None:
        """Update the tags list."""
        self._tags_root.takeChildren()
        for tag in tags:
            item = QTreeWidgetItem(self._tags_root, [tag.name])
            item.setData(0, Qt.ItemDataRole.UserRole, ("tag", tag.name))
            item.setToolTip(0, f"Tag: {tag.name}\nCommit: {tag.short_sha}")
        self._tags_root.setText(0, f"Tags ({len(tags)})")

    def update_stashes(self, stashes: list[StashEntry]) -> None:
        """Update the stashes list."""
        self._stash_root.takeChildren()
        for stash in stashes:
            item = QTreeWidgetItem(self._stash_root, [stash.display_name])
            item.setData(0, Qt.ItemDataRole.UserRole, ("stash", stash.index))
            item.setToolTip(0, f"Stash: {stash.ref}\n{stash.message}")
        self._stash_root.setText(0, f"Stashes ({len(stashes)})")

    def clear(self) -> None:
        """Clear all sidebar data."""
        self._repo_label.setText("No repository open")
        self._branch_label.setText("")
        self._head_label.setText("")
        self._branches_root.takeChildren()
        self._remote_root.takeChildren()
        self._tags_root.takeChildren()
        self._stash_root.takeChildren()

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle tree item clicks and emit appropriate signals."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        item_type, value = data
        if item_type in ("branch", "remote_branch"):
            self.branch_selected.emit(value)
        elif item_type == "tag":
            self.tag_selected.emit(value)
        elif item_type == "stash":
            self.stash_selected.emit(value)
