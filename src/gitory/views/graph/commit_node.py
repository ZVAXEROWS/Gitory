"""Commit node — circle-shaped QGraphicsItem for regular commits."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from gitory.domain.models.graph import GraphNode


class CommitNodeItem(QGraphicsEllipseItem):
    """Circle-shaped graph node representing a regular commit.

    Displays the commit subject as a label to the right and shows
    detailed information on hover via tooltip.
    """

    def __init__(
        self,
        node: GraphNode,
        x: float,
        y: float,
        radius: float = 8.0,
        parent: QGraphicsItem | None = None,
    ) -> None:
        """Initialize a commit node.

        Args:
            node: The graph node data.
            x: Center X coordinate.
            y: Center Y coordinate.
            radius: Circle radius in pixels.
            parent: Parent QGraphicsItem.
        """
        super().__init__(
            -radius, -radius, radius * 2, radius * 2,
            parent,
        )
        self.setPos(x, y)
        self._node = node
        self._radius = radius
        self._selected = False
        self._hovered = False

        # Visual properties.
        self._color = QColor(node.color)
        self._setup_appearance()
        self._setup_label()
        self._setup_tooltip()

        # Interaction flags.
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setZValue(10)  # Nodes above edges.

    @property
    def node(self) -> GraphNode:
        """The underlying graph node data."""
        return self._node

    @property
    def sha(self) -> str:
        """Commit SHA."""
        return self._node.sha

    def _setup_appearance(self) -> None:
        """Configure pen and brush for the node circle."""
        # Gradient fill for depth.
        gradient = QRadialGradient(0, -self._radius * 0.3, self._radius * 1.5)
        lighter = QColor(self._color)
        lighter.setAlpha(255)
        gradient.setColorAt(0, lighter.lighter(130))
        gradient.setColorAt(1, self._color)

        self.setBrush(QBrush(gradient))
        self.setPen(QPen(self._color.darker(120), 1.5))

    def _setup_label(self) -> None:
        """Create the commit message label to the right of the node."""
        label = QGraphicsTextItem(self)
        subject = self._node.commit.subject
        # Truncate long messages.
        if len(subject) > 60:
            subject = subject[:57] + "..."

        label_text = subject

        # Prepend branch/tag labels.
        decorations: list[str] = []
        for branch in self._node.branch_names:
            decorations.append(f"[{branch}]")
        for tag in self._node.tag_names:
            decorations.append(f"🏷{tag}")

        if decorations:
            label_text = " ".join(decorations) + "  " + label_text

        label.setPlainText(label_text)
        label.setDefaultTextColor(QColor("#c0caf5"))
        font = label.font()
        font.setPointSize(8)
        label.setFont(font)
        label.setPos(self._radius + 8, -label.boundingRect().height() / 2)
        label.setZValue(11)

    def _setup_tooltip(self) -> None:
        """Build a rich tooltip with commit details."""
        commit = self._node.commit
        lines = [
            f"<b>{commit.subject}</b>",
            f"<br/><code>{commit.sha}</code>",
            f"<br/>{commit.author_name} &lt;{commit.author_email}&gt;",
            f"<br/>{commit.relative_time}",
        ]
        if self._node.branch_names:
            lines.append(f"<br/>Branch: {', '.join(self._node.branch_names)}")
        if self._node.tag_names:
            lines.append(f"<br/>Tags: {', '.join(self._node.tag_names)}")
        if commit.is_merge:
            lines.append("<br/>Merge commit")

        self.setToolTip("".join(lines))

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Paint the commit circle with hover and selection effects."""
        # HEAD glow effect.
        if self._node.is_head:
            glow_color = QColor(self._color)
            glow_color.setAlpha(60)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_color))
            glow_radius = self._radius * 2.0
            painter.drawEllipse(QRectF(
                -glow_radius, -glow_radius,
                glow_radius * 2, glow_radius * 2,
            ))

        # Hover highlight.
        if self._hovered:
            hover_color = QColor(self._color)
            hover_color.setAlpha(40)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(hover_color))
            hover_r = self._radius * 1.6
            painter.drawEllipse(QRectF(-hover_r, -hover_r, hover_r * 2, hover_r * 2))

        # Main circle.
        super().paint(painter, option, widget)

        # Selection ring.
        if self.isSelected():
            painter.setPen(QPen(QColor("#ffffff"), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            sel_r = self._radius + 3
            painter.drawEllipse(QRectF(-sel_r, -sel_r, sel_r * 2, sel_r * 2))

    def hoverEnterEvent(self, event) -> None:
        """Highlight on mouse enter."""
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Remove highlight on mouse leave."""
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)
