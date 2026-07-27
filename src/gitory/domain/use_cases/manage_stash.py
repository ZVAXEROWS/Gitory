"""Stash management use case."""

from __future__ import annotations

from gitory.domain.models.stash import StashEntry
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.git_parser import GitParser


class ManageStash:
    """Operations on Git stash: create, apply, pop, drop, clear."""

    def __init__(self, executor: GitExecutor) -> None:
        self._executor = executor

    def list_stashes(self) -> list[StashEntry]:
        """List all stash entries."""
        result = self._executor.run("stash", "list", "--format=%gd|%H|%gs")
        if result.success:
            return GitParser.parse_stash_list(result.output)
        return []

    def create(self, message: str = "") -> tuple[bool, str]:
        """Create a new stash."""
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])
        result = self._executor.run(*args)
        return result.success, result.error_message

    def apply(self, index: int = 0) -> tuple[bool, str]:
        """Apply a stash without removing it."""
        result = self._executor.run("stash", "apply", f"stash@{{{index}}}")
        return result.success, result.error_message

    def pop(self, index: int = 0) -> tuple[bool, str]:
        """Apply and remove a stash."""
        result = self._executor.run("stash", "pop", f"stash@{{{index}}}")
        return result.success, result.error_message

    def drop(self, index: int = 0) -> tuple[bool, str]:
        """Remove a stash without applying."""
        result = self._executor.run("stash", "drop", f"stash@{{{index}}}")
        return result.success, result.error_message

    def clear(self) -> tuple[bool, str]:
        """Remove all stashes."""
        result = self._executor.run("stash", "clear")
        return result.success, result.error_message
