"""Graph view — QGraphicsView with zoom, pan, and interaction controls.

This is the heart of the application — the interactive canvas that displays
the commit graph.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView

from gitory.views.graph.graph_scene import GraphScene


class GraphView(QGraphicsView):
    """Interactive canvas for the commit graph.

    Provides:
    - Smooth zoom via mouse wheel (anchored under cursor)
    - Pan via middle mouse drag or Ctrl+drag
    - Node selection via click
    - Double-click to center on a node
    - Fit-to-view button support

    Signals:
        zoom_changed: Emitted with the new zoom factor.
    """

    zoom_changed = Signal(float)

    # Zoom limits.
    ZOOM_MIN = 0.1
    ZOOM_MAX = 5.0

    def __init__(self, scene: GraphScene, parent=None) -> None:
        """Initialize the graph view.

        Args:
            scene: The GraphScene to display.
            parent: Parent widget.
        """
        super().__init__(scene, parent)
        self._graph_scene = scene
        self._zoom_factor = 1.15
        self._current_zoom = 1.0
        self._panning = False
        self._pan_start = QPointF()

        self._setup_view()

    def _setup_view(self) -> None:
        """Configure view properties for smooth rendering."""
        # Rendering quality.
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # Zoom anchors under mouse cursor.
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Smooth scrolling.
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Viewport updates.
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Drag mode — rubber band for selection by default.
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        # Background.
        self.setStyleSheet("QGraphicsView { border: none; }")

    @property
    def current_zoom(self) -> float:
        """Current zoom level (1.0 = 100%)."""
        return self._current_zoom

    def set_zoom_factor(self, factor: float) -> None:
        """Update the per-tick zoom factor.

        Args:
            factor: Zoom multiplier per scroll tick (e.g., 1.15).
        """
        self._zoom_factor = max(1.01, min(2.0, factor))

    def fit_graph(self) -> None:
        """Auto-zoom to fit the entire graph in the viewport."""
        self.fitInView(self.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        # Update tracked zoom level.
        transform = self.transform()
        self._current_zoom = transform.m11()
        self.zoom_changed.emit(self._current_zoom)

    def center_on_node(self, sha: str) -> None:
        """Smoothly center the view on a specific node.

        Args:
            sha: Commit hash to center on.
        """
        pos = self._graph_scene.center_on_node(sha)
        if pos:
            self.centerOn(pos)

    def wheelEvent(self, event) -> None:
        """Zoom on mouse wheel scroll."""
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return

        if delta > 0:
            factor = self._zoom_factor
        else:
            factor = 1.0 / self._zoom_factor

        # Clamp zoom level.
        new_zoom = self._current_zoom * factor
        if new_zoom < self.ZOOM_MIN or new_zoom > self.ZOOM_MAX:
            return

        self._current_zoom = new_zoom
        self.scale(factor, factor)
        self.zoom_changed.emit(self._current_zoom)

    def mousePressEvent(self, event) -> None:
        """Start panning on middle mouse button or Ctrl+left click."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._start_pan(event)
        elif event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._start_pan(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Pan the view while dragging."""
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - delta.x())
            )
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - delta.y())
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Stop panning."""
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            if self._panning:
                self._panning = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
                return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """Center on double-clicked node."""
        item = self.itemAt(event.pos())
        if item and hasattr(item, "sha"):
            self.centerOn(item.pos())
        elif item and hasattr(item, "parentItem") and item.parentItem() and hasattr(item.parentItem(), "sha"):
            # Clicked on a label child item.
            self.centerOn(item.parentItem().pos())
        else:
            super().mouseDoubleClickEvent(event)

    def _start_pan(self, event) -> None:
        """Begin a pan operation."""
        self._panning = True
        self._pan_start = event.position()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def drawBackground(self, painter: QPainter, rect) -> None:
        """Draw the graph background with subtle dot grid."""
        # Solid background.
        painter.fillRect(rect, self.palette().window().color())

        # Subtle dot pattern for spatial awareness.
        if self._current_zoom > 0.3:
            from PySide6.QtGui import QColor, QPen

            dot_color = QColor("#292e42")
            painter.setPen(QPen(dot_color, 1))

            spacing = 30
            left = int(rect.left()) - (int(rect.left()) % spacing)
            top = int(rect.top()) - (int(rect.top()) % spacing)

            x = left
            while x < rect.right():
                y = top
                while y < rect.bottom():
                    painter.drawPoint(int(x), int(y))
                    y += spacing
                x += spacing
