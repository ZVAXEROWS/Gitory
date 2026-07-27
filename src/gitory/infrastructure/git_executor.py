"""Git command executor.

Wraps subprocess to run official Git CLI commands. All Git operations
in the application flow through this single class, ensuring a consistent
interface, logging, error handling, and timeout management.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

# Default timeout for git commands (seconds).
DEFAULT_TIMEOUT = 30

# Longer timeout for network operations (push, pull, fetch, clone).
NETWORK_TIMEOUT = 120


@dataclass(frozen=True, slots=True)
class GitResult:
    """Result of a git command execution.

    Attributes:
        stdout: Captured standard output.
        stderr: Captured standard error.
        return_code: Process exit code (0 = success).
        command: The full command string that was executed.
    """

    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    command: str = ""

    @property
    def success(self) -> bool:
        """True if the command exited with code 0."""
        return self.return_code == 0

    @property
    def error_message(self) -> str:
        """Human-readable error message from stderr, stripped of whitespace."""
        return self.stderr.strip() if self.stderr else ""

    @property
    def output(self) -> str:
        """Stripped stdout content."""
        return self.stdout.strip() if self.stdout else ""


class GitExecutor(QObject):
    """Executes Git CLI commands via subprocess.

    All git operations in the application go through this class. It provides:
    - Consistent command building with repo path
    - Timeout handling
    - Command logging via Qt signals
    - Error capture without exceptions (returns GitResult)

    Signals:
        command_executed: Emitted after every command with the full command string.
        output_received: Emitted with stdout/stderr output for the terminal panel.
    """

    command_executed = Signal(str)       # Full command string
    output_received = Signal(str, bool)  # (text, is_error)

    def __init__(
        self,
        repo_path: Path | None = None,
        git_binary: str = "git",
        parent: QObject | None = None,
    ) -> None:
        """Initialize the executor.

        Args:
            repo_path: Path to the Git repository root. If None, commands
                run without -C (useful for git init, git clone).
            git_binary: Path to the git executable. Defaults to 'git' on PATH.
            parent: Qt parent object.
        """
        super().__init__(parent)
        self._repo_path = repo_path
        self._git_binary = git_binary

    @property
    def repo_path(self) -> Path | None:
        """Current repository path."""
        return self._repo_path

    @repo_path.setter
    def repo_path(self, path: Path | None) -> None:
        """Update the repository path for subsequent commands."""
        self._repo_path = path

    def run(
        self,
        *args: str,
        timeout: int = DEFAULT_TIMEOUT,
        use_repo_path: bool = True,
    ) -> GitResult:
        """Execute a git command synchronously.

        Args:
            *args: Git subcommand and arguments (e.g., 'log', '--oneline').
            timeout: Maximum seconds to wait for the command.
            use_repo_path: If True, prepends -C <repo_path> to the command.

        Returns:
            GitResult with stdout, stderr, and return code.
        """
        cmd = self._build_command(list(args), use_repo_path)
        cmd_str = " ".join(cmd)

        logger.debug("Executing: %s", cmd_str)
        self.command_executed.emit(f"$ {cmd_str}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self._repo_path) if self._repo_path and use_repo_path else None,
                encoding="utf-8",
                errors="replace",
                # Prevent console window popup on Windows.
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

            git_result = GitResult(
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                command=cmd_str,
            )

            # Emit output for the terminal panel.
            if result.stdout.strip():
                self.output_received.emit(result.stdout.strip(), False)
            if result.stderr.strip():
                self.output_received.emit(result.stderr.strip(), result.returncode != 0)

            if not git_result.success:
                logger.warning("Git command failed [%d]: %s", result.returncode, cmd_str)
                logger.warning("stderr: %s", result.stderr.strip())

            return git_result

        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout}s: {cmd_str}"
            logger.error(error_msg)
            self.output_received.emit(error_msg, True)
            return GitResult(stderr=error_msg, return_code=-1, command=cmd_str)

        except FileNotFoundError:
            error_msg = (
                f"Git executable not found: '{self._git_binary}'. "
                "Please ensure Git is installed and on your PATH, "
                "or configure the path in Settings."
            )
            logger.error(error_msg)
            self.output_received.emit(error_msg, True)
            return GitResult(stderr=error_msg, return_code=-1, command=cmd_str)

        except OSError as e:
            error_msg = f"OS error running git: {e}"
            logger.error(error_msg)
            self.output_received.emit(error_msg, True)
            return GitResult(stderr=error_msg, return_code=-1, command=cmd_str)

    def run_network(self, *args: str) -> GitResult:
        """Execute a git command that involves network I/O.

        Uses an extended timeout suitable for push/pull/fetch/clone.
        """
        return self.run(*args, timeout=NETWORK_TIMEOUT)

    def check_git_installed(self) -> GitResult:
        """Verify that the git executable is accessible."""
        return self.run("--version", use_repo_path=False)

    def is_git_repository(self, path: Path) -> bool:
        """Check if the given path is inside a git repository."""
        old_path = self._repo_path
        self._repo_path = path
        result = self.run("rev-parse", "--git-dir")
        self._repo_path = old_path
        return result.success

    def _build_command(self, args: list[str], use_repo_path: bool) -> list[str]:
        """Build the full command list.

        Args:
            args: Git subcommand and arguments.
            use_repo_path: Whether to include -C <path>.

        Returns:
            Complete command list ready for subprocess.
        """
        cmd = [self._git_binary]

        # Use -C to run git in the repo directory without changing cwd.
        if use_repo_path and self._repo_path:
            cmd.extend(["-C", str(self._repo_path)])

        cmd.extend(args)
        return cmd
