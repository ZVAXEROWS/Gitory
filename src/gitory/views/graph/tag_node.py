"""Tag node — square-shaped QGraphicsItem for tagged commits (future use).

Note: Tags are currently displayed as labels on regular CommitNodeItems.
This standalone TagNodeItem is reserved for potential future use where
tags might be visualized as separate graph nodes.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from gitory.domain.models.graph import GraphNode


class TagNodeItem(QGraphicsRectItem):
    """Square-shaped graph node for tagged commits."""

    def __init__(
        self,
        node: GraphNode,
        x: float,
        y: float,
        radius: float = 7.0,
        parent: QGraphicsItem | None = None,
    ) -> None:
        size = radius * 2
        super().__init__(-radius, -radius, size, size, parent)
        self.setPos(x, y)
        self._node = node
        self._radius = radius
        self._hovered = False

        self._color = QColor("#FFD93D")  # Tag yellow.
        self.setBrush(QBrush(self._color))
        self.setPen(QPen(self._color.darker(120), 1.5))

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setZValue(10)

        # Label.
        label = QGraphicsTextItem(self)
        tag_text = ", ".join(node.tag_names) if node.tag_names else node.commit.subject[:30]
        label.setPlainText(f"🏷 {tag_text}")
        label.setDefaultTextColor(QColor("#c0caf5"))
        font = label.font()
        font.setPointSize(8)
        label.setFont(font)
        label.setPos(radius + 8, -label.boundingRect().height() / 2)

    @property
    def node(self) -> GraphNode:
        return self._node

    @property
    def sha(self) -> str:
        return self._node.sha

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        if self._hovered:
            hover_color = QColor(self._color)
            hover_color.setAlpha(40)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(hover_color))
            hover_r = self._radius * 1.6
            painter.drawEllipse(QRectF(-hover_r, -hover_r, hover_r * 2, hover_r * 2))
        super().paint(painter, option, widget)

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)
