"""Diff viewer — side-by-side diff comparison window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gitory.domain.models.diff import FileDiff, LineType


class DiffViewer(QWidget):
    """Side-by-side diff viewer widget.

    Displays file changes with syntax highlighting:
    - Green for additions
    - Red for deletions
    - Grey for context lines
    - File tree on the left
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diff Viewer")
        self.setMinimumSize(900, 600)
        self._diffs: list[FileDiff] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # File tree.
        self._file_tree = QTreeWidget()
        self._file_tree.setHeaderHidden(True)
        self._file_tree.setMaximumWidth(250)
        self._file_tree.itemClicked.connect(self._on_file_selected)
        layout.addWidget(self._file_tree)

        # Diff area — side by side.
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Old (left).
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_header = QLabel("Old Version")
        left_header.setObjectName("sectionHeader")
        left_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(left_header)

        self._old_view = QPlainTextEdit()
        self._old_view.setReadOnly(True)
        self._old_view.setFont(QFont("Cascadia Code", 10))
        self._old_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        left_layout.addWidget(self._old_view)
        splitter.addWidget(left_container)

        # New (right).
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_header = QLabel("New Version")
        right_header.setObjectName("sectionHeader")
        right_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(right_header)

        self._new_view = QPlainTextEdit()
        self._new_view.setReadOnly(True)
        self._new_view.setFont(QFont("Cascadia Code", 10))
        self._new_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        right_layout.addWidget(self._new_view)
        splitter.addWidget(right_container)

        layout.addWidget(splitter, stretch=1)

        # Sync scroll between panels.
        self._old_view.verticalScrollBar().valueChanged.connect(
            self._new_view.verticalScrollBar().setValue,
        )
        self._new_view.verticalScrollBar().valueChanged.connect(
            self._old_view.verticalScrollBar().setValue,
        )

    def set_diffs(self, diffs: list[FileDiff]) -> None:
        """Load file diffs into the viewer.

        Args:
            diffs: List of FileDiff objects to display.
        """
        self._diffs = diffs
        self._file_tree.clear()

        for i, diff in enumerate(diffs):
            icon = {
                "ADDED": "+",
                "DELETED": "-",
                "MODIFIED": "~",
                "RENAMED": "→",
            }.get(diff.status.name, "·")

            item = QTreeWidgetItem(self._file_tree, [f"{icon} {diff.display_path}"])
            item.setData(0, Qt.ItemDataRole.UserRole, i)

            # Color by status.
            color_map = {
                "ADDED": "#6BCB77",
                "DELETED": "#f7768e",
                "MODIFIED": "#e0af68",
                "RENAMED": "#7aa2f7",
            }
            item.setForeground(0, QColor(color_map.get(diff.status.name, "#c0caf5")))

        # Select first file.
        if diffs:
            self._file_tree.setCurrentItem(self._file_tree.topLevelItem(0))
            self._show_diff(diffs[0])

    def _on_file_selected(self, item: QTreeWidgetItem, _: int) -> None:
        index = item.data(0, Qt.ItemDataRole.UserRole)
        if index is not None and 0 <= index < len(self._diffs):
            self._show_diff(self._diffs[index])

    def _show_diff(self, diff: FileDiff) -> None:
        """Render a single file's diff in the side-by-side views."""
        self._old_view.clear()
        self._new_view.clear()

        if diff.is_binary:
            self._old_view.setPlainText("Binary file — cannot display diff")
            self._new_view.setPlainText("Binary file — cannot display diff")
            return

        old_cursor = self._old_view.textCursor()
        new_cursor = self._new_view.textCursor()

        # Format definitions.
        context_fmt = QTextCharFormat()
        context_fmt.setForeground(QColor("#a9b1d6"))

        add_fmt = QTextCharFormat()
        add_fmt.setForeground(QColor("#6BCB77"))
        add_fmt.setBackground(QColor("#1a2e1a"))

        del_fmt = QTextCharFormat()
        del_fmt.setForeground(QColor("#f7768e"))
        del_fmt.setBackground(QColor("#2e1a1a"))

        header_fmt = QTextCharFormat()
        header_fmt.setForeground(QColor("#7aa2f7"))

        for hunk in diff.hunks:
            # Hunk header.
            header_text = f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@ {hunk.header}\n"
            old_cursor.insertText(header_text, header_fmt)
            new_cursor.insertText(header_text, header_fmt)

            for line in hunk.lines:
                if line.type == LineType.CONTEXT:
                    line_no_old = f"{line.old_line_no:>4} " if line.old_line_no else "     "
                    line_no_new = f"{line.new_line_no:>4} " if line.new_line_no else "     "
                    old_cursor.insertText(f"{line_no_old}{line.content}\n", context_fmt)
                    new_cursor.insertText(f"{line_no_new}{line.content}\n", context_fmt)
                elif line.type == LineType.DELETION:
                    line_no = f"{line.old_line_no:>4} " if line.old_line_no else "     "
                    old_cursor.insertText(f"{line_no}- {line.content}\n", del_fmt)
                    new_cursor.insertText("\n", context_fmt)  # Empty line for alignment.
                elif line.type == LineType.ADDITION:
                    line_no = f"{line.new_line_no:>4} " if line.new_line_no else "     "
                    old_cursor.insertText("\n", context_fmt)  # Empty line for alignment.
                    new_cursor.insertText(f"{line_no}+ {line.content}\n", add_fmt)
