"""Layout engine for the commit graph.

Orchestrates the full pipeline:
    commits → topological ordering → lane assignment → coordinate mapping → GraphLayout

This module produces the final GraphLayout that the view layer renders.
"""

from __future__ import annotations

from gitory.domain.models.commit import Commit
from gitory.domain.models.graph import GraphEdge, GraphLayout, GraphNode, NodeType
from gitory.graph_engine.lane_allocator import LaneAllocator


class LayoutEngine:
    """Computes the visual layout of a commit graph.

    Takes a list of commits (in topological order) and produces a
    GraphLayout with positioned nodes and edges.

    The layout uses:
    - X axis: lanes (horizontal columns for parallel branches)
    - Y axis: rows (vertical position, row 0 = newest at top)
    """

    def __init__(
        self,
        row_height: int = 50,
        lane_width: int = 30,
    ) -> None:
        """Initialize the layout engine.

        Args:
            row_height: Vertical spacing between rows in pixels.
            lane_width: Horizontal spacing between lanes in pixels.
        """
        self._row_height = row_height
        self._lane_width = lane_width
        self._allocator = LaneAllocator()

    @property
    def row_height(self) -> int:
        """Current row height in pixels."""
        return self._row_height

    @row_height.setter
    def row_height(self, value: int) -> None:
        self._row_height = max(20, min(200, value))

    @property
    def lane_width(self) -> int:
        """Current lane width in pixels."""
        return self._lane_width

    @lane_width.setter
    def lane_width(self, value: int) -> None:
        self._lane_width = max(15, min(100, value))

    def compute(self, commits: list[Commit]) -> GraphLayout:
        """Compute the full graph layout for a list of commits.

        Args:
            commits: Commits in topological order (newest first).
                This is the natural output of `git log --topo-order`.

        Returns:
            Complete GraphLayout with nodes and edges positioned.
        """
        if not commits:
            return GraphLayout()

        # Step 1: Assign lanes and colors.
        lane_data = self._allocator.allocate(commits)

        # Step 2: Build nodes with row positions.
        layout = GraphLayout()
        sha_to_row: dict[str, int] = {}

        for row, commit in enumerate(commits):
            lane, color = lane_data.get(commit.sha, (0, "#6BCB77"))

            node_type = self._determine_node_type(commit)

            node = GraphNode(
                sha=commit.sha,
                commit=commit,
                lane=lane,
                row=row,
                node_type=node_type,
                color=color,
                tag_names=list(commit.tags),
                branch_names=list(commit.branches),
                is_head=commit.is_head,
            )

            layout.nodes[commit.sha] = node
            sha_to_row[commit.sha] = row

        # Step 3: Build edges from each commit to its parents.
        for commit in commits:
            node = layout.nodes.get(commit.sha)
            if not node:
                continue

            for i, parent_sha in enumerate(commit.parent_shas):
                parent_node = layout.nodes.get(parent_sha)
                if not parent_node:
                    # Parent is outside the loaded range — skip.
                    continue

                # Edge color: use child's color for first parent (same branch),
                # use parent's color for merge edges (cross-branch).
                edge_color = node.color if i == 0 else parent_node.color

                edge = GraphEdge(
                    child_sha=commit.sha,
                    parent_sha=parent_sha,
                    child_lane=node.lane,
                    parent_lane=parent_node.lane,
                    child_row=node.row,
                    parent_row=parent_node.row,
                    color=edge_color,
                    is_merge_edge=i > 0,
                )
                layout.edges.append(edge)

        # Step 4: Set layout metadata.
        layout.max_lane = self._allocator.max_lane
        layout.total_rows = len(commits)

        return layout

    def node_x(self, lane: int) -> float:
        """Calculate pixel X coordinate for a lane.

        Args:
            lane: Lane index (0-based).

        Returns:
            X coordinate in pixels (center of the lane).
        """
        return lane * self._lane_width + self._lane_width / 2

    def node_y(self, row: int) -> float:
        """Calculate pixel Y coordinate for a row.

        Args:
            row: Row index (0 = top/newest).

        Returns:
            Y coordinate in pixels (center of the row).
        """
        return row * self._row_height + self._row_height / 2

    @staticmethod
    def _determine_node_type(commit: Commit) -> NodeType:
        """Determine the visual node type based on commit properties.

        Args:
            commit: The commit to classify.

        Returns:
            Appropriate NodeType for rendering.
        """
        if commit.is_merge:
            return NodeType.MERGE
        if commit.is_root:
            return NodeType.INITIAL
        return NodeType.COMMIT
