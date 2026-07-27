"""Open repository use case.

Validates a path as a Git repository and loads its metadata.
"""

from __future__ import annotations

from pathlib import Path

from gitory.domain.models.repository import RepositoryInfo
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.git_parser import GitParser


class OpenRepository:
    """Opens and validates an existing Git repository.

    Loads basic repository metadata: current branch, HEAD SHA,
    remotes, and detached HEAD state.
    """

    def __init__(self, executor: GitExecutor) -> None:
        self._executor = executor

    def execute(self, path: Path) -> tuple[RepositoryInfo | None, str]:
        """Open a repository at the given path.

        Args:
            path: Path to the repository root (must contain .git).

        Returns:
            Tuple of (RepositoryInfo, error_message).
            On success, error_message is empty.
            On failure, RepositoryInfo is None.
        """
        path = path.resolve()

        # Validate the path exists.
        if not path.exists():
            return None, f"Path does not exist: {path}"

        if not path.is_dir():
            return None, f"Path is not a directory: {path}"

        # Check for .git directory.
        self._executor.repo_path = path
        if not self._executor.is_git_repository(path):
            return None, f"Not a Git repository: {path}"

        # Load repository info.
        info = RepositoryInfo(path=path)

        # Get current branch.
        result = self._executor.run("symbolic-ref", "--short", "HEAD")
        if result.success:
            info.current_branch, info.is_detached = GitParser.parse_current_branch(result.output)
        else:
            info.is_detached = True

        # Get HEAD SHA.
        result = self._executor.run("rev-parse", "HEAD")
        if result.success:
            info.head_sha = GitParser.parse_head_sha(result.output)

        # Get remotes.
        result = self._executor.run("remote", "-v")
        if result.success:
            info.remotes = GitParser.parse_remotes(result.output)
            info.remote_url = info.remotes.get("origin")

        return info, ""
