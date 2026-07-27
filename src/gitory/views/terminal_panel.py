"""Terminal panel — bottom panel showing git command log and manual input."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class TerminalPanel(QWidget):
    """Bottom panel that logs all git commands and allows manual input.

    Shows every git command the application executes along with
    stdout and stderr output. Users can also type manual git commands.

    Signals:
        command_entered: Emitted when the user types a command and presses Enter.
    """

    command_entered = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("terminalPanel")
        self.setMinimumHeight(120)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the terminal panel layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar.
        header = QWidget()
        header.setStyleSheet("background-color: #16161e; border-bottom: 1px solid #292e42;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 12, 4)

        title = QLabel("Terminal")
        title.setStyleSheet("color: #565f89; font-size: 9pt; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Output area.
        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont("Cascadia Code", 9))
        self._output.setStyleSheet(
            "QPlainTextEdit { background-color: #13131a; color: #a9b1d6; "
            "border: none; border-radius: 0; padding: 8px; }"
        )
        self._output.setMaximumBlockCount(2000)  # Limit memory usage.
        layout.addWidget(self._output, stretch=1)

        # Input line.
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #13131a; border-top: 1px solid #292e42;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 4, 12, 4)

        prompt = QLabel("$")
        prompt.setStyleSheet("color: #7aa2f7; font-family: 'Cascadia Code'; font-size: 10pt; font-weight: bold;")
        input_layout.addWidget(prompt)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a git command...")
        self._input.setFont(QFont("Cascadia Code", 9))
        self._input.setStyleSheet(
            "QLineEdit { background-color: #13131a; color: #c0caf5; "
            "border: none; border-radius: 0; padding: 4px; }"
        )
        self._input.returnPressed.connect(self._on_enter)
        input_layout.addWidget(self._input, stretch=1)

        layout.addWidget(input_container)

    def append_command(self, command: str) -> None:
        """Display a command that was executed.

        Args:
            command: The full command string (including $ prefix).
        """
        self._append_colored(command, "#7aa2f7")

    def append_output(self, text: str, is_error: bool = False) -> None:
        """Display command output.

        Args:
            text: Output text.
            is_error: True for stderr (shown in red).
        """
        color = "#f7768e" if is_error else "#a9b1d6"
        self._append_colored(text, color)

    def append_info(self, text: str) -> None:
        """Display an informational message.

        Args:
            text: Info text (shown in dim color).
        """
        self._append_colored(text, "#565f89")

    def _append_colored(self, text: str, color: str) -> None:
        """Append colored text to the output area."""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        cursor = self._output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    def _on_enter(self) -> None:
        """Handle Enter key in the input field."""
        text = self._input.text().strip()
        if text:
            self._input.clear()
            self.command_entered.emit(text)
