"""Edge item — curved QPainterPath connecting commit nodes."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from gitory.domain.models.graph import GraphEdge


class EdgeItem(QGraphicsPathItem):
    """Curved line connecting two commit nodes in the graph.

    Uses cubic Bézier curves for smooth branch lines.
    Straight vertical lines when nodes are in the same lane;
    S-curves when crossing between lanes.
    """

    def __init__(
        self,
        edge: GraphEdge,
        child_pos: QPointF,
        parent_pos: QPointF,
        line_width: float = 2.0,
        parent_item: QGraphicsItem | None = None,
    ) -> None:
        """Initialize an edge between two node positions.

        Args:
            edge: The graph edge data.
            child_pos: Center position of the child (newer) node.
            parent_pos: Center position of the parent (older) node.
            line_width: Width of the connecting line.
            parent_item: Parent QGraphicsItem.
        """
        super().__init__(parent_item)
        self._edge = edge

        # Build the path.
        path = self._build_path(child_pos, parent_pos)
        self.setPath(path)

        # Styling.
        color = QColor(edge.color)
        pen = QPen(color, line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        # Merge edges are slightly thinner and semi-transparent.
        if edge.is_merge_edge:
            color.setAlpha(180)
            pen = QPen(color, line_width * 0.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setStyle(Qt.PenStyle.SolidLine)

        self.setPen(pen)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setZValue(1)  # Below nodes.

    @property
    def edge(self) -> GraphEdge:
        """The underlying graph edge data."""
        return self._edge

    @staticmethod
    def _build_path(child_pos: QPointF, parent_pos: QPointF) -> QPainterPath:
        """Build a smooth path between child and parent positions.

        If both nodes are in the same lane (same X), draw a straight line.
        Otherwise, use a cubic Bézier curve that flows vertically first,
        then curves horizontally — producing the characteristic S-curve
        seen in tools like GitKraken.

        Args:
            child_pos: Starting position (newer commit).
            parent_pos: Ending position (older commit).

        Returns:
            QPainterPath for the edge.
        """
        path = QPainterPath()
        path.moveTo(child_pos)

        dx = abs(parent_pos.x() - child_pos.x())
        dy = parent_pos.y() - child_pos.y()

        if dx < 1.0:
            # Same lane — straight vertical line.
            path.lineTo(parent_pos)
        else:
            # Different lanes — S-curve.
            # Control points: maintain vertical flow then curve horizontally.
            # The curve breaks at the midpoint vertically.
            mid_y = child_pos.y() + dy * 0.5

            # First control point: go straight down from child.
            cp1 = QPointF(child_pos.x(), mid_y)
            # Second control point: go straight up to parent.
            cp2 = QPointF(parent_pos.x(), mid_y)

            path.cubicTo(cp1, cp2, parent_pos)

        return path
