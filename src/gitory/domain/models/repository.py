"""Repository domain model.

Represents metadata about an opened Git repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RepositoryInfo:
    """Metadata about a Git repository.

    Attributes:
        path: Absolute path to the repository root (containing .git).
        name: Repository display name (derived from folder name).
        current_branch: Name of the currently checked-out branch.
        is_detached: True if HEAD is detached (not on a branch).
        head_sha: Commit hash that HEAD points to.
        remote_url: URL of the 'origin' remote, if configured.
        remotes: Dictionary mapping remote names to their URLs.
    """

    path: Path
    name: str = ""
    current_branch: str = ""
    is_detached: bool = False
    head_sha: str = ""
    remote_url: str | None = None
    remotes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Derive name from path if not provided."""
        if not self.name:
            self.name = self.path.name

    @property
    def git_dir(self) -> Path:
        """Path to the .git directory."""
        return self.path / ".git"

    @property
    def has_remote(self) -> bool:
        """True if at least one remote is configured."""
        return len(self.remotes) > 0

    @property
    def display_path(self) -> str:
        """Human-readable path string."""
        return str(self.path)
