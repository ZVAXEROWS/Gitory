"""Diff domain models.

Represents file diffs, hunks, and individual diff lines with their types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class DiffStatus(Enum):
    """Status of a file in a diff."""

    ADDED = auto()
    MODIFIED = auto()
    DELETED = auto()
    RENAMED = auto()
    COPIED = auto()
    UNTRACKED = auto()


class LineType(Enum):
    """Type of a single line in a diff hunk."""

    CONTEXT = auto()    # Unchanged line (shown for context)
    ADDITION = auto()   # Added line (prefixed with +)
    DELETION = auto()   # Deleted line (prefixed with -)
    HEADER = auto()     # Hunk header line (@@ ... @@)


class FileStatus(Enum):
    """Working tree / index status for a file (from git status --porcelain=v2)."""

    UNMODIFIED = "."
    MODIFIED = "M"
    TYPE_CHANGED = "T"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNMERGED = "U"
    UNTRACKED = "?"
    IGNORED = "!"


@dataclass(frozen=True, slots=True)
class DiffLine:
    """A single line within a diff hunk.

    Attributes:
        type: Whether this line is context, addition, or deletion.
        content: The text content of the line (without +/- prefix).
        old_line_no: Line number in the old file, None for additions.
        new_line_no: Line number in the new file, None for deletions.
    """

    type: LineType
    content: str
    old_line_no: int | None = None
    new_line_no: int | None = None


@dataclass(frozen=True, slots=True)
class DiffHunk:
    """A contiguous section of changes within a file diff.

    Attributes:
        old_start: Starting line number in the old file.
        old_count: Number of lines from the old file.
        new_start: Starting line number in the new file.
        new_count: Number of lines in the new file.
        header: Optional section header (function name, etc.).
        lines: Individual diff lines within this hunk.
    """

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header: str = ""
    lines: list[DiffLine] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FileDiff:
    """Diff information for a single file.

    Attributes:
        old_path: Path of the file in the old version.
        new_path: Path of the file in the new version (differs for renames).
        status: Type of change (added, modified, deleted, renamed).
        hunks: List of change hunks within this file.
        additions: Total number of added lines.
        deletions: Total number of deleted lines.
        is_binary: True if the file is binary.
    """

    old_path: str
    new_path: str
    status: DiffStatus
    hunks: list[DiffHunk] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    is_binary: bool = False

    @property
    def display_path(self) -> str:
        """Path to display — shows rename arrow if paths differ."""
        if self.old_path != self.new_path and self.old_path and self.new_path:
            return f"{self.old_path} → {self.new_path}"
        return self.new_path or self.old_path

    @property
    def total_changes(self) -> int:
        """Total number of changed lines (additions + deletions)."""
        return self.additions + self.deletions


@dataclass(slots=True)
class StatusEntry:
    """A single entry from git status --porcelain=v2.

    Attributes:
        path: File path relative to repo root.
        index_status: Status in the staging area.
        worktree_status: Status in the working tree.
        old_path: Previous path if renamed/copied.
    """

    path: str
    index_status: FileStatus
    worktree_status: FileStatus
    old_path: str | None = None

    @property
    def is_staged(self) -> bool:
        """True if the file has staged changes."""
        return self.index_status != FileStatus.UNMODIFIED

    @property
    def is_unstaged(self) -> bool:
        """True if the file has unstaged working tree changes."""
        return self.worktree_status not in (FileStatus.UNMODIFIED, FileStatus.UNTRACKED)

    @property
    def is_untracked(self) -> bool:
        """True if the file is untracked."""
        return self.worktree_status == FileStatus.UNTRACKED


@dataclass(slots=True)
class StatusResult:
    """Complete result of a git status operation.

    Attributes:
        branch: Current branch name.
        upstream: Upstream tracking branch name.
        ahead: Number of commits ahead of upstream.
        behind: Number of commits behind upstream.
        entries: Individual file status entries.
    """

    branch: str = ""
    upstream: str = ""
    ahead: int = 0
    behind: int = 0
    entries: list[StatusEntry] = field(default_factory=list)

    @property
    def staged_entries(self) -> list[StatusEntry]:
        """Files with staged changes."""
        return [e for e in self.entries if e.is_staged]

    @property
    def unstaged_entries(self) -> list[StatusEntry]:
        """Files with unstaged working tree changes."""
        return [e for e in self.entries if e.is_unstaged]

    @property
    def untracked_entries(self) -> list[StatusEntry]:
        """Untracked files."""
        return [e for e in self.entries if e.is_untracked]

    @property
    def is_clean(self) -> bool:
        """True if working tree and index are clean."""
        return len(self.entries) == 0
