"""Stash node — triangle-shaped QGraphicsItem for stash entries."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPolygonItem,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from gitory.domain.models.graph import GraphNode


class StashNodeItem(QGraphicsPolygonItem):
    """Triangle-shaped graph node for stash entries."""

    def __init__(
        self,
        node: GraphNode,
        x: float,
        y: float,
        radius: float = 8.0,
        parent: QGraphicsItem | None = None,
    ) -> None:
        r = radius * 1.2
        triangle = QPolygonF([
            QPointF(0, -r),             # Top
            QPointF(r, r * 0.7),        # Bottom right
            QPointF(-r, r * 0.7),       # Bottom left
        ])
        super().__init__(triangle, parent)
        self.setPos(x, y)
        self._node = node
        self._radius = radius
        self._hovered = False

        self._color = QColor("#FF8A65")  # Stash orange.
        self.setBrush(QBrush(self._color))
        self.setPen(QPen(self._color.darker(120), 1.5))

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setZValue(10)

        label = QGraphicsTextItem(self)
        label.setPlainText(node.commit.subject[:40])
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
