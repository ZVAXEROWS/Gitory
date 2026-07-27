"""Graph scene — QGraphicsScene that builds items from GraphLayout."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Signal
from PySide6.QtWidgets import QGraphicsScene

from gitory.domain.models.graph import GraphLayout, NodeType
from gitory.graph_engine.layout_engine import LayoutEngine
from gitory.views.graph.commit_node import CommitNodeItem
from gitory.views.graph.edge_item import EdgeItem
from gitory.views.graph.merge_node import MergeNodeItem
from gitory.views.graph.stash_node import StashNodeItem


class GraphScene(QGraphicsScene):
    """Custom QGraphicsScene that renders a GraphLayout.

    Builds QGraphicsItems (nodes and edges) from the computed layout
    and handles selection signals.

    Signals:
        node_clicked: Emitted with the SHA when a node is selected.
    """

    node_clicked = Signal(str)

    def __init__(self, layout_engine: LayoutEngine, parent=None) -> None:
        """Initialize the graph scene.

        Args:
            layout_engine: Layout engine for coordinate calculations.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._layout_engine = layout_engine
        self._node_items: dict[str, CommitNodeItem | MergeNodeItem | StashNodeItem] = {}
        self._edge_items: list[EdgeItem] = []

        # Connect selection change to our handler.
        self.selectionChanged.connect(self._on_selection_changed)

    @property
    def node_items(self) -> dict:
        """Map of SHA → node QGraphicsItem."""
        return self._node_items

    def build_from_layout(self, layout: GraphLayout, node_radius: float = 8.0) -> None:
        """Clear the scene and rebuild from a new GraphLayout.

        Args:
            layout: The computed graph layout.
            node_radius: Radius of commit nodes in pixels.
        """
        self.clear()
        self._node_items.clear()
        self._edge_items.clear()

        if not layout.nodes:
            return

        # Build nodes first so we have positions for edges.
        for node in layout.nodes.values():
            x = self._layout_engine.node_x(node.lane)
            y = self._layout_engine.node_y(node.row)

            if node.node_type == NodeType.MERGE:
                item = MergeNodeItem(node, x, y, node_radius)
            elif node.node_type == NodeType.STASH:
                item = StashNodeItem(node, x, y, node_radius)
            else:
                item = CommitNodeItem(node, x, y, node_radius)

            self.addItem(item)
            self._node_items[node.sha] = item

        # Build edges.
        for edge in layout.edges:
            child_item = self._node_items.get(edge.child_sha)
            parent_item = self._node_items.get(edge.parent_sha)

            if not child_item or not parent_item:
                continue

            child_pos = QPointF(child_item.pos())
            parent_pos = QPointF(parent_item.pos())

            edge_item = EdgeItem(edge, child_pos, parent_pos)
            self.addItem(edge_item)
            self._edge_items.append(edge_item)

        # Set scene rect with some padding.
        padding = 100
        rect = self.itemsBoundingRect()
        rect.adjust(-padding, -padding, padding + 400, padding)
        self.setSceneRect(rect)

    def select_node(self, sha: str) -> None:
        """Programmatically select a node by SHA.

        Args:
            sha: Commit hash to select.
        """
        self.clearSelection()
        item = self._node_items.get(sha)
        if item:
            item.setSelected(True)

    def center_on_node(self, sha: str) -> QPointF | None:
        """Get the position of a node for centering the view.

        Args:
            sha: Commit hash.

        Returns:
            Position of the node, or None if not found.
        """
        item = self._node_items.get(sha)
        if item:
            return item.pos()
        return None

    def _on_selection_changed(self) -> None:
        """Handle selection changes and emit node_clicked."""
        selected = self.selectedItems()
        if selected:
            item = selected[0]
            if hasattr(item, "sha"):
                self.node_clicked.emit(item.sha)
