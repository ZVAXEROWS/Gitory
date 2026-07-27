"""Stash domain model.

Represents Git stash entries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StashEntry:
    """Immutable representation of a Git stash entry.

    Attributes:
        index: Stash index number (0 = most recent).
        message: Stash description message.
        sha: Commit hash of the stash commit.
        branch: Branch name where the stash was created.
    """

    index: int
    message: str
    sha: str
    branch: str = ""

    @property
    def ref(self) -> str:
        """Git stash reference string (e.g., 'stash@{0}')."""
        return f"stash@{{{self.index}}}"

    @property
    def short_sha(self) -> str:
        """First 7 characters of the stash commit hash."""
        return self.sha[:7]

    @property
    def display_name(self) -> str:
        """User-friendly display string."""
        return f"{self.ref}: {self.message}"
