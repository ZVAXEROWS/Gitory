"""Tag domain model.

Represents lightweight and annotated Git tags.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Tag:
    """Immutable representation of a Git tag.

    Attributes:
        name: Tag name (e.g., 'v1.0.0').
        sha: Commit hash the tag points to.
        message: Annotation message for annotated tags, None for lightweight.
        is_annotated: True for annotated tags (created with -a or -m).
    """

    name: str
    sha: str
    message: str | None = None
    is_annotated: bool = False

    @property
    def short_sha(self) -> str:
        """First 7 characters of the tagged commit hash."""
        return self.sha[:7]

    @property
    def display_name(self) -> str:
        """Display name with tag indicator."""
        return f"Tag: {self.name}"
