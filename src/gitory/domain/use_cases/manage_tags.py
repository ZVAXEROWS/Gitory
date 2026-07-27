"""Tag management use case."""

from __future__ import annotations

from gitory.domain.models.tag import Tag
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.git_parser import GitParser

# Field separator for tag format parsing.
_FIELD_SEP = "\x1f"


class ManageTags:
    """Operations on Git tags: create, delete, list."""

    def __init__(self, executor: GitExecutor) -> None:
        self._executor = executor

    def list_tags(self) -> list[Tag]:
        """List all tags."""
        fmt = _FIELD_SEP.join(["%(refname:short)", "%(objectname:short)", "%(contents:subject)"])
        result = self._executor.run("tag", "-l", f"--format={fmt}")
        if result.success:
            return GitParser.parse_tags(result.output)
        return []

    def create(self, name: str, message: str = "", target: str = "HEAD") -> tuple[bool, str]:
        """Create a new tag.

        Args:
            name: Tag name.
            message: Annotation message (creates annotated tag if provided).
            target: Commit to tag (default: HEAD).
        """
        args = ["tag"]
        if message:
            args.extend(["-a", name, "-m", message])
        else:
            args.append(name)
        args.append(target)
        result = self._executor.run(*args)
        return result.success, result.error_message

    def delete(self, name: str) -> tuple[bool, str]:
        """Delete a tag."""
        result = self._executor.run("tag", "-d", name)
        return result.success, result.error_message
