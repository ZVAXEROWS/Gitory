"""Tests for the graph layout engine and lane allocator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gitory.domain.models.commit import Commit
from gitory.graph_engine.lane_allocator import LaneAllocator
from gitory.graph_engine.layout_engine import LayoutEngine


def _make_commit(
    sha: str,
    parents: list[str] | None = None,
    message: str = "test",
    branches: list[str] | None = None,
    is_head: bool = False,
) -> Commit:
    """Helper to create a test commit."""
    return Commit(
        sha=sha,
        message=message,
        author_name="Test",
        author_email="test@test.com",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        parent_shas=parents or [],
        branches=branches or [],
        is_head=is_head,
    )


class TestLaneAllocator:
    """Tests for the greedy lane assignment algorithm."""

    def test_empty(self):
        allocator = LaneAllocator()
        result = allocator.allocate([])
        assert result == {}

    def test_single_commit(self):
        commits = [_make_commit("aaa")]
        allocator = LaneAllocator()
        result = allocator.allocate(commits)
        assert len(result) == 1
        lane, color = result["aaa"]
        assert lane == 0

    def test_linear_history(self):
        """Linear A -> B -> C should all be in lane 0."""
        commits = [
            _make_commit("c", parents=["b"]),
            _make_commit("b", parents=["a"]),
            _make_commit("a"),
        ]
        allocator = LaneAllocator()
        result = allocator.allocate(commits)

        assert result["c"][0] == 0
        assert result["b"][0] == 0
        assert result["a"][0] == 0

    def test_branch_gets_new_lane(self):
        """A branch should be assigned a different lane.

        Graph:
            c1 (main) -> a
            c2 (feat) -> a
        """
        commits = [
            _make_commit("c1", parents=["a"]),
            _make_commit("c2", parents=["a"]),
            _make_commit("a"),
        ]
        allocator = LaneAllocator()
        result = allocator.allocate(commits)

        # c1 and c2 should be in different lanes.
        assert result["c1"][0] != result["c2"][0]

    def test_merge_commit(self):
        """Merge commits should display connections from multiple lanes.

        Graph:
            m (merge c1 + c2) -> c1, c2
            c1 -> a
            c2 -> a
            a
        """
        commits = [
            _make_commit("m", parents=["c1", "c2"]),
            _make_commit("c1", parents=["a"]),
            _make_commit("c2", parents=["a"]),
            _make_commit("a"),
        ]
        allocator = LaneAllocator()
        result = allocator.allocate(commits)

        # All commits should have lanes assigned.
        assert len(result) == 4
        # c1 and c2 should have different lanes since one is a merge source.
        lanes = {sha: lane for sha, (lane, _) in result.items()}
        assert lanes["c1"] != lanes["c2"] or lanes["m"] == lanes["c1"]

    def test_no_overlapping_lanes(self):
        """No two commits in the same row should share a lane."""
        commits = [
            _make_commit("e", parents=["c", "d"]),
            _make_commit("d", parents=["b"]),
            _make_commit("c", parents=["b"]),
            _make_commit("b", parents=["a"]),
            _make_commit("a"),
        ]
        allocator = LaneAllocator()
        result = allocator.allocate(commits)

        # Since commits are in topo order, each has a unique row.
        # But parallel branches (c and d) should not share a lane.
        assert result["c"][0] != result["d"][0]


class TestLayoutEngine:
    """Tests for the full layout engine."""

    def test_empty(self):
        engine = LayoutEngine()
        layout = engine.compute([])
        assert layout.node_count == 0
        assert layout.edge_count == 0

    def test_single_commit(self):
        commits = [_make_commit("aaa", is_head=True)]
        engine = LayoutEngine()
        layout = engine.compute(commits)

        assert layout.node_count == 1
        assert layout.edge_count == 0
        assert layout.nodes["aaa"].is_head is True

    def test_linear_produces_edges(self):
        commits = [
            _make_commit("b", parents=["a"]),
            _make_commit("a"),
        ]
        engine = LayoutEngine()
        layout = engine.compute(commits)

        assert layout.node_count == 2
        assert layout.edge_count == 1
        assert layout.edges[0].child_sha == "b"
        assert layout.edges[0].parent_sha == "a"

    def test_merge_produces_two_edges(self):
        commits = [
            _make_commit("m", parents=["a", "b"]),
            _make_commit("a"),
            _make_commit("b"),
        ]
        engine = LayoutEngine()
        layout = engine.compute(commits)

        assert layout.edge_count == 2
        merge_edges = [e for e in layout.edges if e.is_merge_edge]
        assert len(merge_edges) == 1

    def test_node_positions_increase(self):
        """Row indices should increase for each commit (newer = lower row number)."""
        commits = [
            _make_commit("c", parents=["b"]),
            _make_commit("b", parents=["a"]),
            _make_commit("a"),
        ]
        engine = LayoutEngine()
        layout = engine.compute(commits)

        assert layout.nodes["c"].row == 0
        assert layout.nodes["b"].row == 1
        assert layout.nodes["a"].row == 2

    def test_coordinate_calculations(self):
        engine = LayoutEngine(row_height=50, lane_width=30)
        assert engine.node_x(0) == 15.0  # 0 * 30 + 15
        assert engine.node_x(1) == 45.0  # 1 * 30 + 15
        assert engine.node_y(0) == 25.0  # 0 * 50 + 25
        assert engine.node_y(1) == 75.0  # 1 * 50 + 25
