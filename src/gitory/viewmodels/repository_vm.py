"""Repository view model.

Manages the state of the currently open repository and coordinates
between the UI and the domain use cases.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from gitory.domain.models.repository import RepositoryInfo
from gitory.domain.use_cases.commit_changes import CommitChanges
from gitory.domain.use_cases.init_repository import InitRepository
from gitory.domain.use_cases.manage_remotes import ManageRemotes
from gitory.domain.use_cases.open_repository import OpenRepository
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.repo_store import RepoStore


class RepositoryViewModel(QObject):
    """ViewModel for the overall repository state.

    Signals:
        repo_opened: Emitted when a repository is successfully opened/initialized.
        repo_closed: Emitted when the repository is closed.
        error_occurred: Emitted with an error message string.
        status_changed: Emitted when the working tree status changes.
        refresh_requested: Emitted when the UI should refresh all views.
    """

    repo_opened = Signal(RepositoryInfo)
    repo_closed = Signal()
    error_occurred = Signal(str)
    status_changed = Signal()
    refresh_requested = Signal()

    def __init__(
        self,
        executor: GitExecutor,
        repo_store: RepoStore,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._executor = executor
        self._repo_store = repo_store
        self._repo_info: RepositoryInfo | None = None

        # Use cases.
        self._open_uc = OpenRepository(executor)
        self._init_uc = InitRepository(executor)
        self._remote_uc = ManageRemotes(executor)
        self._commit_uc = CommitChanges(executor)

    @property
    def repo_info(self) -> RepositoryInfo | None:
        """Currently open repository info, or None if no repo is open."""
        return self._repo_info

    @property
    def is_repo_open(self) -> bool:
        """Whether a repository is currently open."""
        return self._repo_info is not None

    @property
    def recent_repos(self) -> list:
        """List of recently opened repository entries."""
        return self._repo_store.entries

    def open_repository(self, path: Path) -> None:
        """Open a repository at the given path.

        Emits repo_opened on success, error_occurred on failure.
        """
        info, error = self._open_uc.execute(path)
        if info:
            self._repo_info = info
            self._repo_store.add(path, info.name)
            self.repo_opened.emit(info)
        else:
            self.error_occurred.emit(error)

    def init_repository(
        self,
        path: Path,
        name: str = "",
        create_readme: bool = True,
        create_gitignore: bool = True,
        create_license: bool = False,
    ) -> None:
        """Initialize a new repository.

        Emits repo_opened on success, error_occurred on failure.
        """
        success, error = self._init_uc.execute(
            path, name, create_readme, create_gitignore, create_license,
        )
        if success:
            self.open_repository(path)
        else:
            self.error_occurred.emit(error)

    def add_remote(self, name: str, url: str) -> None:
        """Add a remote to the current repository."""
        success, error = self._remote_uc.add_remote(name, url)
        if success:
            self.refresh_requested.emit()
        else:
            self.error_occurred.emit(error)

    def push(self, remote: str = "origin", branch: str = "", force: bool = False) -> None:
        """Push to remote."""
        success, error = self._remote_uc.push(remote, branch, force)
        if success:
            self.refresh_requested.emit()
        else:
            self.error_occurred.emit(error)

    def pull(self, remote: str = "origin", branch: str = "") -> None:
        """Pull from remote."""
        success, error = self._remote_uc.pull(remote, branch)
        if success:
            self.refresh_requested.emit()
        else:
            self.error_occurred.emit(error)

    def fetch(self) -> None:
        """Fetch from all remotes."""
        success, error = self._remote_uc.fetch()
        if success:
            self.refresh_requested.emit()
        else:
            self.error_occurred.emit(error)

    def refresh(self) -> None:
        """Refresh the repository state."""
        if self._repo_info:
            # Re-open to refresh metadata.
            info, _ = self._open_uc.execute(self._repo_info.path)
            if info:
                self._repo_info = info
            self.refresh_requested.emit()

    def close_repository(self) -> None:
        """Close the current repository."""
        self._repo_info = None
        self._executor.repo_path = None
        self.repo_closed.emit()
