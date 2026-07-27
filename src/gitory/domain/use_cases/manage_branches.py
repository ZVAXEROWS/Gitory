"""Branch management use case.

Handles creating, deleting, renaming, checking out, merging, and rebasing branches.
"""

from __future__ import annotations

from gitory.domain.models.branch import Branch
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.git_parser import GitParser


class ManageBranches:
    """Operations on Git branches."""

    def __init__(self, executor: GitExecutor) -> None:
        self._executor = executor

    def list_branches(self) -> list[Branch]:
        """List all local and remote branches."""
        result = self._executor.run(
            "branch", "-a",
            "--format=%(refname:short) %(objectname:short) %(HEAD) %(upstream:short)",
        )
        if result.success:
            return GitParser.parse_branches(result.output)
        return []

    def create(self, name: str, start_point: str = "") -> tuple[bool, str]:
        """Create a new branch.

        Args:
            name: New branch name.
            start_point: Starting commit/branch (default: HEAD).
        """
        args = ["branch", name]
        if start_point:
            args.append(start_point)
        result = self._executor.run(*args)
        return result.success, result.error_message

    def delete(self, name: str, force: bool = False) -> tuple[bool, str]:
        """Delete a branch.

        Args:
            name: Branch name to delete.
            force: If True, use -D (force delete unmerged branches).
        """
        flag = "-D" if force else "-d"
        result = self._executor.run("branch", flag, name)
        return result.success, result.error_message

    def rename(self, old_name: str, new_name: str) -> tuple[bool, str]:
        """Rename a branch.

        Args:
            old_name: Current branch name.
            new_name: New branch name.
        """
        result = self._executor.run("branch", "-m", old_name, new_name)
        return result.success, result.error_message

    def checkout(self, name: str) -> tuple[bool, str]:
        """Checkout a branch or commit.

        Args:
            name: Branch name, tag name, or commit SHA.
        """
        result = self._executor.run("checkout", name)
        return result.success, result.error_message

    def merge(self, source: str, no_ff: bool = False) -> tuple[bool, str]:
        """Merge a branch into the current branch.

        Args:
            source: Branch name to merge from.
            no_ff: If True, always create a merge commit.
        """
        args = ["merge", source]
        if no_ff:
            args.append("--no-ff")
        result = self._executor.run(*args)
        return result.success, result.error_message

    def rebase(self, onto: str) -> tuple[bool, str]:
        """Rebase the current branch onto another.

        Args:
            onto: Branch or commit to rebase onto.
        """
        result = self._executor.run("rebase", onto)
        return result.success, result.error_message

    def reset(self, target: str, mode: str = "--mixed") -> tuple[bool, str]:
        """Reset the current branch to a commit.

        Args:
            target: Commit SHA or ref to reset to.
            mode: Reset mode (--soft, --mixed, or --hard).
        """
        result = self._executor.run("reset", mode, target)
        return result.success, result.error_message

    def cherry_pick(self, sha: str) -> tuple[bool, str]:
        """Cherry-pick a commit onto the current branch.

        Args:
            sha: Commit SHA to cherry-pick.
        """
        result = self._executor.run("cherry-pick", sha)
        return result.success, result.error_message
