"""Graph domain models.

Represents the computed graph layout — nodes positioned in lanes and rows,
connected by edges. These models bridge the gap between raw Git data and
the visual QGraphicsScene items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from gitory.domain.models.commit import Commit


class NodeType(Enum):
    """Visual shape for a graph node."""

    COMMIT = auto()     # Circle — regular commit
    MERGE = auto()      # Diamond — merge commit (2+ parents)
    STASH = auto()      # Triangle — stash entry
    INITIAL = auto()    # Circle with ring — root commit (no parents)


# High-contrast color palette optimized for dark backgrounds.
# 12 colors chosen for maximum distinguishability.
BRANCH_COLORS: list[str] = [
    "#6BCB77",   # Green (current branch primary)
    "#4FC3F7",   # Light blue
    "#FF6B6B",   # Coral red
    "#FFD93D",   # Yellow
    "#BA68C8",   # Purple
    "#4DD0E1",   # Cyan
    "#FF8A65",   # Orange
    "#AED581",   # Light green
    "#F06292",   # Pink
    "#90A4AE",   # Blue grey
    "#DCE775",   # Lime
    "#80DEEA",   # Teal
]


@dataclass(slots=True)
class GraphNode:
    """A positioned node in the commit graph.

    Attributes:
        sha: Commit hash this node represents.
        commit: Full commit data.
        lane: Horizontal column index (0 = leftmost).
        row: Vertical row index (0 = newest commit at top).
        node_type: Visual shape to render.
        color: Hex color for this node and its branch line.
        tag_names: Tags pointing at this commit (displayed as labels).
        branch_names: Branches pointing at this commit.
        is_head: Whether this is the HEAD commit.
    """

    sha: str
    commit: Commit
    lane: int = 0
    row: int = 0
    node_type: NodeType = NodeType.COMMIT
    color: str = BRANCH_COLORS[0]
    tag_names: list[str] = field(default_factory=list)
    branch_names: list[str] = field(default_factory=list)
    is_head: bool = False


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """A directed edge connecting two nodes in the graph.

    Edges flow from child (newer) to parent (older).

    Attributes:
        child_sha: Hash of the child (newer) commit.
        parent_sha: Hash of the parent (older) commit.
        child_lane: Lane of the child node.
        parent_lane: Lane of the parent node.
        child_row: Row of the child node.
        parent_row: Row of the parent node.
        color: Hex color for the edge line.
        is_merge_edge: True if this connects a merge commit to a secondary parent.
    """

    child_sha: str
    parent_sha: str
    child_lane: int = 0
    parent_lane: int = 0
    child_row: int = 0
    parent_row: int = 0
    color: str = BRANCH_COLORS[0]
    is_merge_edge: bool = False


@dataclass(slots=True)
class GraphLayout:
    """Complete computed layout for a repository's commit graph.

    This is the output of the LayoutEngine and the input to the GraphScene.

    Attributes:
        nodes: Map from commit SHA to positioned GraphNode.
        edges: All edges connecting nodes.
        max_lane: Maximum lane index used (width of the graph).
        total_rows: Total number of rows (height of the graph).
    """

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    max_lane: int = 0
    total_rows: int = 0

    @property
    def node_count(self) -> int:
        """Number of nodes in the layout."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Number of edges in the layout."""
        return len(self.edges)
