"""Branch view model.

Manages branch listing and operations for the sidebar.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from gitory.domain.models.branch import Branch
from gitory.domain.use_cases.manage_branches import ManageBranches
from gitory.infrastructure.git_executor import GitExecutor


class BranchViewModel(QObject):
    """ViewModel for branch management.

    Signals:
        branches_updated: Emitted with updated branch lists.
        error_occurred: Emitted with error message.
        action_completed: Emitted on successful branch operation.
    """

    branches_updated = Signal(list)
    error_occurred = Signal(str)
    action_completed = Signal(str)

    def __init__(self, executor: GitExecutor, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._branches_uc = ManageBranches(executor)
        self._branches: list[Branch] = []

    @property
    def local_branches(self) -> list[Branch]:
        """Local branches only."""
        return [b for b in self._branches if not b.is_remote]

    @property
    def remote_branches(self) -> list[Branch]:
        """Remote branches only."""
        return [b for b in self._branches if b.is_remote]

    @property
    def current_branch(self) -> Branch | None:
        """Currently checked-out branch, or None if detached."""
        return next((b for b in self._branches if b.is_current), None)

    def refresh(self) -> None:
        """Reload the branch list."""
        self._branches = self._branches_uc.list_branches()
        self.branches_updated.emit(self._branches)

    def create_branch(self, name: str, start_point: str = "") -> None:
        """Create a new branch."""
        success, error = self._branches_uc.create(name, start_point)
        if success:
            self.action_completed.emit(f"Created branch '{name}'")
            self.refresh()
        else:
            self.error_occurred.emit(error)

    def delete_branch(self, name: str, force: bool = False) -> None:
        """Delete a branch."""
        success, error = self._branches_uc.delete(name, force)
        if success:
            self.action_completed.emit(f"Deleted branch '{name}'")
            self.refresh()
        else:
            self.error_occurred.emit(error)

    def checkout(self, name: str) -> None:
        """Checkout a branch."""
        success, error = self._branches_uc.checkout(name)
        if success:
            self.action_completed.emit(f"Checked out '{name}'")
            self.refresh()
        else:
            self.error_occurred.emit(error)

    def merge(self, source: str) -> None:
        """Merge a branch into current."""
        success, error = self._branches_uc.merge(source)
        if success:
            self.action_completed.emit(f"Merged '{source}'")
            self.refresh()
        else:
            self.error_occurred.emit(error)

    def rebase(self, onto: str) -> None:
        """Rebase current branch onto another."""
        success, error = self._branches_uc.rebase(onto)
        if success:
            self.action_completed.emit(f"Rebased onto '{onto}'")
            self.refresh()
        else:
            self.error_occurred.emit(error)

    def reset(self, target: str, mode: str = "--mixed") -> None:
        """Reset current branch to a target."""
        success, error = self._branches_uc.reset(target, mode)
        if success:
            self.action_completed.emit(f"Reset to '{target[:7]}'")
            self.refresh()
        else:
            self.error_occurred.emit(error)
