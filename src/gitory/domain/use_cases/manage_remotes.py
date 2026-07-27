"""Remote management use case."""

from __future__ import annotations

from gitory.infrastructure.git_executor import GitExecutor


class ManageRemotes:
    """Operations on Git remotes: add, remove, push, pull, fetch."""

    def __init__(self, executor: GitExecutor) -> None:
        self._executor = executor

    def add_remote(self, name: str, url: str) -> tuple[bool, str]:
        """Add a new remote."""
        result = self._executor.run("remote", "add", name, url)
        return result.success, result.error_message

    def remove_remote(self, name: str) -> tuple[bool, str]:
        """Remove a remote."""
        result = self._executor.run("remote", "remove", name)
        return result.success, result.error_message

    def push(
        self, remote: str = "origin", branch: str = "", force: bool = False,
    ) -> tuple[bool, str]:
        """Push to a remote."""
        args = ["push", remote]
        if branch:
            args.append(branch)
        if force:
            args.append("--force")
        result = self._executor.run_network(*args)
        return result.success, result.error_message

    def pull(self, remote: str = "origin", branch: str = "") -> tuple[bool, str]:
        """Pull from a remote."""
        args = ["pull", remote]
        if branch:
            args.append(branch)
        result = self._executor.run_network(*args)
        return result.success, result.error_message

    def fetch(self, remote: str = "", prune: bool = True) -> tuple[bool, str]:
        """Fetch from remote(s)."""
        args = ["fetch"]
        if remote:
            args.append(remote)
        else:
            args.append("--all")
        if prune:
            args.append("--prune")
        result = self._executor.run_network(*args)
        return result.success, result.error_message
