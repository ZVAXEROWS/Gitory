"""Branch domain model.

Represents local and remote Git branches.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Branch:
    """Immutable representation of a Git branch.

    Attributes:
        name: Branch name (e.g., 'main', 'feature/login').
        tip_sha: Commit hash at the tip of this branch.
        is_remote: True for remote-tracking branches (e.g., 'origin/main').
        is_current: True if this is the currently checked-out branch.
        tracking: Upstream branch name, if configured (e.g., 'origin/main').
        remote_name: Remote name extracted from remote branches (e.g., 'origin').
    """

    name: str
    tip_sha: str = ""
    is_remote: bool = False
    is_current: bool = False
    tracking: str | None = None
    remote_name: str | None = None

    @property
    def short_name(self) -> str:
        """Branch name without remote prefix.

        For remote branches like 'origin/main', returns 'main'.
        For local branches, returns the name as-is.
        """
        if self.is_remote and "/" in self.name:
            return self.name.split("/", maxsplit=1)[1]
        return self.name

    @property
    def display_name(self) -> str:
        """User-friendly display name with remote prefix if applicable."""
        if self.is_remote and self.remote_name:
            return f"{self.remote_name}/{self.short_name}"
        return self.name
