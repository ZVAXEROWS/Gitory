"""Commit detail view model.

Manages the state of the right-side detail panel showing commit info.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from gitory.domain.models.commit import Commit
from gitory.domain.models.graph import GraphLayout
from gitory.domain.use_cases.get_diff import GetDiff
from gitory.domain.use_cases.manage_branches import ManageBranches
from gitory.infrastructure.git_executor import GitExecutor


class CommitDetailViewModel(QObject):
    """ViewModel for the commit detail panel.

    Signals:
        commit_loaded: Emitted when commit details are ready to display.
        diff_loaded: Emitted with list of FileDiff when diff is computed.
        error_occurred: Emitted with error message string.
        action_completed: Emitted when a commit action succeeds.
    """

    commit_loaded = Signal(Commit)
    diff_loaded = Signal(list)
    error_occurred = Signal(str)
    action_completed = Signal(str)

    def __init__(
        self,
        executor: GitExecutor,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._executor = executor
        self._get_diff = GetDiff(executor)
        self._branches = ManageBranches(executor)
        self._current_commit: Commit | None = None
        self._graph_layout: GraphLayout | None = None

    @property
    def current_commit(self) -> Commit | None:
        """Currently displayed commit."""
        return self._current_commit

    def set_graph_layout(self, layout: GraphLayout) -> None:
        """Update the graph layout reference for lookups."""
        self._graph_layout = layout

    def load_commit(self, sha: str) -> None:
        """Load commit details from the current graph layout.

        Args:
            sha: Commit hash to display.
        """
        if self._graph_layout and sha in self._graph_layout.nodes:
            node = self._graph_layout.nodes[sha]
            self._current_commit = node.commit
            self.commit_loaded.emit(node.commit)

    def load_diff(self, sha: str) -> None:
        """Load the diff for a commit.

        Args:
            sha: Commit hash to diff.
        """
        diffs = self._get_diff.for_commit(sha)
        self.diff_loaded.emit(diffs)

    def checkout_commit(self, sha: str) -> None:
        """Checkout the specified commit (detached HEAD)."""
        success, error = self._branches.checkout(sha)
        if success:
            self.action_completed.emit(f"Checked out {sha[:7]}")
        else:
            self.error_occurred.emit(error)

    def cherry_pick(self, sha: str) -> None:
        """Cherry-pick the specified commit."""
        success, error = self._branches.cherry_pick(sha)
        if success:
            self.action_completed.emit(f"Cherry-picked {sha[:7]}")
        else:
            self.error_occurred.emit(error)
