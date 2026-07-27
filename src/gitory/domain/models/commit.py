"""Commit domain model.

Represents a single Git commit with all associated metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Commit:
    """Immutable representation of a Git commit.

    Attributes:
        sha: Full 40-character commit hash.
        message: Complete commit message (subject + body).
        author_name: Author's display name.
        author_email: Author's email address.
        timestamp: Commit timestamp as a datetime object.
        parent_shas: List of parent commit hashes (empty for root commits,
            1 for normal commits, 2+ for merges).
        branches: Branch names pointing to this commit.
        tags: Tag names pointing to this commit.
        is_head: Whether HEAD points to this commit.
    """

    sha: str
    message: str
    author_name: str
    author_email: str
    timestamp: datetime
    parent_shas: list[str] = field(default_factory=list)
    branches: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    is_head: bool = False

    @property
    def short_sha(self) -> str:
        """First 7 characters of the commit hash."""
        return self.sha[:7]

    @property
    def subject(self) -> str:
        """First line of the commit message."""
        return self.message.split("\n", maxsplit=1)[0]

    @property
    def is_merge(self) -> bool:
        """True if this commit has more than one parent."""
        return len(self.parent_shas) > 1

    @property
    def is_root(self) -> bool:
        """True if this commit has no parents (initial commit)."""
        return len(self.parent_shas) == 0

    @property
    def relative_time(self) -> str:
        """Human-readable relative time since this commit.

        Returns a string like '2 hours ago', '3 days ago', etc.
        """
        now = datetime.now(tz=self.timestamp.tzinfo)
        delta = now - self.timestamp
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return "just now"
        if seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        if seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        if seconds < 2592000:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
        if seconds < 31536000:
            months = seconds // 2592000
            return f"{months} month{'s' if months != 1 else ''} ago"

        years = seconds // 31536000
        return f"{years} year{'s' if years != 1 else ''} ago"
