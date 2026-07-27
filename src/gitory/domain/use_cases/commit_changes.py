"""Commit changes use case.

Handles staging, unstaging, committing, and amending.
"""

from __future__ import annotations

from gitory.domain.models.diff import StatusResult
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.git_parser import GitParser


class CommitChanges:
    """Manages the commit workflow: stage, unstage, commit, amend."""

    def __init__(self, executor: GitExecutor) -> None:
        self._executor = executor

    def get_status(self) -> StatusResult:
        """Get the current working tree and index status.

        Returns:
            StatusResult with staged, unstaged, and untracked files.
        """
        result = self._executor.run("status", "--porcelain=v2", "--branch")
        if result.success:
            return GitParser.parse_status(result.output)
        return StatusResult()

    def stage_all(self) -> tuple[bool, str]:
        """Stage all changes (git add -A)."""
        result = self._executor.run("add", "-A")
        return result.success, result.error_message

    def stage_files(self, paths: list[str]) -> tuple[bool, str]:
        """Stage specific files.

        Args:
            paths: List of file paths relative to repo root.
        """
        if not paths:
            return True, ""
        result = self._executor.run("add", "--", *paths)
        return result.success, result.error_message

    def unstage_all(self) -> tuple[bool, str]:
        """Unstage all staged changes (git reset HEAD)."""
        result = self._executor.run("reset", "HEAD")
        return result.success, result.error_message

    def unstage_files(self, paths: list[str]) -> tuple[bool, str]:
        """Unstage specific files.

        Args:
            paths: List of file paths relative to repo root.
        """
        if not paths:
            return True, ""
        result = self._executor.run("reset", "HEAD", "--", *paths)
        return result.success, result.error_message

    def commit(self, message: str) -> tuple[bool, str]:
        """Create a new commit with the staged changes.

        Args:
            message: Commit message (must not be empty).

        Returns:
            Tuple of (success, error_message).
        """
        if not message.strip():
            return False, "Commit message cannot be empty."

        result = self._executor.run("commit", "-m", message)
        return result.success, result.error_message

    def commit_and_push(self, message: str, remote: str = "origin", branch: str = "") -> tuple[bool, str]:
        """Commit staged changes and push to remote.

        Args:
            message: Commit message.
            remote: Remote name (default: origin).
            branch: Branch name (default: current branch).
        """
        success, error = self.commit(message)
        if not success:
            return False, error

        args = ["push", remote]
        if branch:
            args.append(branch)
        result = self._executor.run_network(*args)
        return result.success, result.error_message

    def amend(self, message: str | None = None) -> tuple[bool, str]:
        """Amend the most recent commit.

        Args:
            message: New commit message. If None, keeps the old message.
        """
        args = ["commit", "--amend"]
        if message is not None:
            args.extend(["-m", message])
        else:
            args.append("--no-edit")
        result = self._executor.run(*args)
        return result.success, result.error_message
