"""Stash view model.

Manages stash listing and operations for the sidebar.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from gitory.domain.models.stash import StashEntry
from gitory.domain.use_cases.manage_stash import ManageStash
from gitory.infrastructure.git_executor import GitExecutor


class StashViewModel(QObject):
    """ViewModel for stash management.

    Signals:
        stashes_updated: Emitted with updated stash list.
        error_occurred: Emitted with error message.
        action_completed: Emitted on successful stash operation.
    """

    stashes_updated = Signal(list)
    error_occurred = Signal(str)
    action_completed = Signal(str)

    def __init__(self, executor: GitExecutor, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._stash_uc = ManageStash(executor)
        self._stashes: list[StashEntry] = []

    @property
    def stashes(self) -> list[StashEntry]:
        """Current stash list."""
        return list(self._stashes)

    def refresh(self) -> None:
        """Reload the stash list."""
        self._stashes = self._stash_uc.list_stashes()
        self.stashes_updated.emit(self._stashes)

    def create_stash(self, message: str = "") -> None:
        """Create a new stash."""
        success, error = self._stash_uc.create(message)
        if success:
            self.action_completed.emit("Stash created")
            self.refresh()
        else:
            self.error_occurred.emit(error)

    def apply_stash(self, index: int = 0) -> None:
        """Apply a stash without removing it."""
        success, error = self._stash_uc.apply(index)
        if success:
            self.action_completed.emit(f"Applied stash@{{{index}}}")
        else:
            self.error_occurred.emit(error)

    def pop_stash(self, index: int = 0) -> None:
        """Apply and remove a stash."""
        success, error = self._stash_uc.pop(index)
        if success:
            self.action_completed.emit(f"Popped stash@{{{index}}}")
            self.refresh()
        else:
            self.error_occurred.emit(error)

    def drop_stash(self, index: int = 0) -> None:
        """Remove a stash without applying."""
        success, error = self._stash_uc.drop(index)
        if success:
            self.action_completed.emit(f"Dropped stash@{{{index}}}")
            self.refresh()
        else:
            self.error_occurred.emit(error)

    def clear_stashes(self) -> None:
        """Remove all stashes."""
        success, error = self._stash_uc.clear()
        if success:
            self.action_completed.emit("All stashes cleared")
            self.refresh()
        else:
            self.error_occurred.emit(error)
