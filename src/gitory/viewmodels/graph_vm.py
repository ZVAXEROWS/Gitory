"""Graph view model.

Manages the commit graph state, layout computation, and node selection.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from gitory.domain.models.graph import GraphLayout
from gitory.domain.use_cases.build_graph import BuildGraph
from gitory.graph_engine.layout_engine import LayoutEngine
from gitory.infrastructure.git_executor import GitExecutor


class GraphViewModel(QObject):
    """ViewModel for the interactive commit graph.

    Signals:
        graph_updated: Emitted when the graph layout has been recomputed.
        node_selected: Emitted when a commit node is selected (SHA string).
        node_deselected: Emitted when selection is cleared.
        loading_started: Emitted when graph loading begins.
        loading_finished: Emitted when graph loading completes.
    """

    graph_updated = Signal(GraphLayout)
    node_selected = Signal(str)
    node_deselected = Signal()
    loading_started = Signal()
    loading_finished = Signal()

    def __init__(
        self,
        executor: GitExecutor,
        layout_engine: LayoutEngine,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._executor = executor
        self._layout_engine = layout_engine
        self._build_graph = BuildGraph(executor, layout_engine)
        self._layout: GraphLayout | None = None
        self._selected_sha: str | None = None
        self._max_commits = 500

    @property
    def layout(self) -> GraphLayout | None:
        """Current graph layout, or None if not loaded."""
        return self._layout

    @property
    def selected_sha(self) -> str | None:
        """SHA of the currently selected node, or None."""
        return self._selected_sha

    @property
    def layout_engine(self) -> LayoutEngine:
        """Access the layout engine for coordinate calculations."""
        return self._layout_engine

    def load_graph(self, max_commits: int | None = None) -> None:
        """Load and compute the graph layout.

        Args:
            max_commits: Override the default commit limit.
        """
        if max_commits is not None:
            self._max_commits = max_commits

        self.loading_started.emit()

        layout = self._build_graph.execute(self._max_commits)
        self._layout = layout
        self.graph_updated.emit(layout)

        self.loading_finished.emit()

    def select_node(self, sha: str) -> None:
        """Select a commit node in the graph.

        Args:
            sha: Commit hash to select.
        """
        self._selected_sha = sha
        self.node_selected.emit(sha)

    def deselect_node(self) -> None:
        """Clear the current node selection."""
        self._selected_sha = None
        self.node_deselected.emit()

    def refresh(self) -> None:
        """Reload the graph with the current settings."""
        self.load_graph()
