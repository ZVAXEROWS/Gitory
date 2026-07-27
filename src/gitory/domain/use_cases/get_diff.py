"""Get diff use case.

Retrieves diffs for commits and the working tree.
"""

from __future__ import annotations

from gitory.domain.models.diff import FileDiff
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.git_parser import GitParser


class GetDiff:
    """Retrieves diff information for commits and working tree changes."""

    def __init__(self, executor: GitExecutor) -> None:
        self._executor = executor

    def for_commit(self, sha: str) -> list[FileDiff]:
        """Get the diff introduced by a specific commit.

        Args:
            sha: Commit hash.

        Returns:
            List of FileDiff objects showing what the commit changed.
        """
        result = self._executor.run("diff-tree", "-p", "--no-commit-id", sha)
        if result.success:
            return GitParser.parse_diff(result.output)
        return []

    def working_tree(self) -> list[FileDiff]:
        """Get unstaged working tree changes (git diff)."""
        result = self._executor.run("diff")
        if result.success:
            return GitParser.parse_diff(result.output)
        return []

    def staged(self) -> list[FileDiff]:
        """Get staged changes (git diff --cached)."""
        result = self._executor.run("diff", "--cached")
        if result.success:
            return GitParser.parse_diff(result.output)
        return []

    def between_commits(self, from_sha: str, to_sha: str) -> list[FileDiff]:
        """Get diff between two commits.

        Args:
            from_sha: Base commit hash.
            to_sha: Target commit hash.
        """
        result = self._executor.run("diff", from_sha, to_sha)
        if result.success:
            return GitParser.parse_diff(result.output)
        return []
