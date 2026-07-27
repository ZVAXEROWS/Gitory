"""Merge node — diamond-shaped QGraphicsItem for merge commits."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF, QRadialGradient
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPolygonItem,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from gitory.domain.models.graph import GraphNode


class MergeNodeItem(QGraphicsPolygonItem):
    """Diamond-shaped graph node representing a merge commit."""

    def __init__(
        self,
        node: GraphNode,
        x: float,
        y: float,
        radius: float = 8.0,
        parent: QGraphicsItem | None = None,
    ) -> None:
        # Build diamond polygon.
        r = radius * 1.2  # Slightly larger than circle nodes.
        diamond = QPolygonF([
            QPointF(0, -r),      # Top
            QPointF(r, 0),       # Right
            QPointF(0, r),       # Bottom
            QPointF(-r, 0),      # Left
        ])
        super().__init__(diamond, parent)
        self.setPos(x, y)
        self._node = node
        self._radius = radius
        self._hovered = False

        self._color = QColor(node.color)
        self._setup_appearance()
        self._setup_label()
        self._setup_tooltip()

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setZValue(10)

    @property
    def node(self) -> GraphNode:
        return self._node

    @property
    def sha(self) -> str:
        return self._node.sha

    def _setup_appearance(self) -> None:
        gradient = QRadialGradient(0, -self._radius * 0.3, self._radius * 2)
        gradient.setColorAt(0, self._color.lighter(130))
        gradient.setColorAt(1, self._color)
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(self._color.darker(120), 1.5))

    def _setup_label(self) -> None:
        label = QGraphicsTextItem(self)
        subject = self._node.commit.subject
        if len(subject) > 60:
            subject = subject[:57] + "..."

        decorations: list[str] = []
        for branch in self._node.branch_names:
            decorations.append(f"[{branch}]")

        label_text = (" ".join(decorations) + "  " + subject) if decorations else subject
        label.setPlainText(label_text)
        label.setDefaultTextColor(QColor("#c0caf5"))
        font = label.font()
        font.setPointSize(8)
        label.setFont(font)
        label.setPos(self._radius + 10, -label.boundingRect().height() / 2)

    def _setup_tooltip(self) -> None:
        commit = self._node.commit
        parents = ", ".join(s[:7] for s in commit.parent_shas)
        lines = [
            f"<b>Merge: {commit.subject}</b>",
            f"<br/><code>{commit.sha}</code>",
            f"<br/>{commit.author_name}",
            f"<br/>{commit.relative_time}",
            f"<br/>Parents: {parents}",
        ]
        self.setToolTip("".join(lines))

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        if self._node.is_head:
            glow_color = QColor(self._color)
            glow_color.setAlpha(60)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QRectF(
                -self._radius * 2, -self._radius * 2,
                self._radius * 4, self._radius * 4,
            ))

        if self._hovered:
            hover_color = QColor(self._color)
            hover_color.setAlpha(40)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(hover_color))
            painter.drawEllipse(QRectF(
                -self._radius * 1.8, -self._radius * 1.8,
                self._radius * 3.6, self._radius * 3.6,
            ))

        super().paint(painter, option, widget)

        if self.isSelected():
            painter.setPen(QPen(QColor("#ffffff"), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            sel_r = self._radius * 1.2 + 3
            painter.drawEllipse(QRectF(-sel_r, -sel_r, sel_r * 2, sel_r * 2))

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)
