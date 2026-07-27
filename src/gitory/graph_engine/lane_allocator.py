"""Lane allocator for the commit graph.

The core greedy lane-assignment algorithm that determines which horizontal
column (lane) each commit node occupies. This runs in O(n) time and produces
stable layouts suitable for interactive scrolling.

Algorithm overview:
1. Walk commits in topological order (newest first).
2. Maintain a list of "active lanes" — columns currently reserved for branch lines.
3. For each commit:
   a. If the commit is the first parent of an existing lane → inherit that lane.
   b. Otherwise → allocate the leftmost available lane.
4. For merge commits, secondary parents keep their own lanes.
5. When a branch terminates (its oldest commit is reached) → free the lane.
"""

from __future__ import annotations

from gitory.domain.models.commit import Commit
from gitory.domain.models.graph import BRANCH_COLORS


class LaneAllocator:
    """Assigns horizontal lanes (columns) to commits for graph visualization.

    Each branch occupies a lane. Lanes are reused when branches end.
    The algorithm prioritizes keeping a commit in the same lane as its
    first child to produce straight vertical lines for linear history.
    """

    def __init__(self) -> None:
        """Initialize the allocator with empty state."""
        # Maps SHA → assigned lane index.
        self._sha_to_lane: dict[str, int] = {}

        # Active lanes: index → SHA of the commit currently "owning" this lane.
        # None means the lane is free for reuse.
        self._lanes: list[str | None] = []

        # Maps SHA → color hex string.
        self._sha_to_color: dict[str, str] = {}

        # Maps lane → color (persists color per-lane for branch consistency).
        self._lane_colors: dict[int, str] = {}

        # Counter for color assignment.
        self._color_index = 0

    def allocate(self, commits: list[Commit]) -> dict[str, tuple[int, str]]:
        """Assign lanes and colors to all commits.

        Args:
            commits: Commits in topological order (newest/top first).

        Returns:
            Dictionary mapping SHA → (lane_index, color_hex).
        """
        self._reset()

        # Build a child map: for each SHA, which commits have it as a parent?
        # This helps us know when a lane should be inherited.
        children_of: dict[str, list[str]] = {}
        for commit in commits:
            for parent_sha in commit.parent_shas:
                children_of.setdefault(parent_sha, []).append(commit.sha)

        # Set of all SHAs for quick lookup (to handle missing parents gracefully).
        all_shas = {c.sha for c in commits}

        for commit in commits:
            lane = self._resolve_lane(commit, children_of)
            color = self._resolve_color(lane)

            self._sha_to_lane[commit.sha] = lane
            self._sha_to_color[commit.sha] = color

            # Reserve lanes for this commit's parents.
            # First parent inherits this commit's lane.
            for i, parent_sha in enumerate(commit.parent_shas):
                if parent_sha not in all_shas:
                    # Parent is outside our loaded range — skip.
                    continue
                if parent_sha in self._sha_to_lane:
                    # Parent already assigned (can happen with merge topology).
                    continue
                if i == 0:
                    # First parent: propagate this lane downward.
                    self._reserve_lane(lane, parent_sha)
                else:
                    # Secondary parent (merge source): allocate a new lane.
                    merge_lane = self._allocate_new_lane()
                    self._reserve_lane(merge_lane, parent_sha)
                    # Assign merge source color.
                    self._lane_colors[merge_lane] = self._next_color()

        return {
            sha: (self._sha_to_lane[sha], self._sha_to_color[sha])
            for sha in self._sha_to_lane
        }

    @property
    def max_lane(self) -> int:
        """Maximum lane index used (0-based)."""
        return max(len(self._lanes) - 1, 0)

    def _resolve_lane(self, commit: Commit, children_of: dict[str, list[str]]) -> int:
        """Determine the lane for a commit.

        Priority:
        1. If this SHA was pre-reserved by a child → use that lane.
        2. Otherwise → allocate a new lane.
        """
        # Check if a child already reserved a lane for us.
        for i, occupant in enumerate(self._lanes):
            if occupant == commit.sha:
                # Claim this lane — it was reserved by our child.
                return i

        # No reservation — allocate a new lane.
        lane = self._allocate_new_lane()
        self._lanes[lane] = commit.sha
        return lane

    def _allocate_new_lane(self) -> int:
        """Find or create the leftmost available lane.

        Returns:
            Index of the allocated lane.
        """
        # Try to reuse a freed lane.
        for i, occupant in enumerate(self._lanes):
            if occupant is None:
                return i

        # No free lane — extend.
        self._lanes.append(None)
        return len(self._lanes) - 1

    def _reserve_lane(self, lane: int, sha: str) -> None:
        """Reserve a lane for a future commit (parent).

        Args:
            lane: Lane index to reserve.
            sha: SHA of the commit that will occupy this lane.
        """
        # Ensure the lanes list is large enough.
        while len(self._lanes) <= lane:
            self._lanes.append(None)
        self._lanes[lane] = sha

    def _free_lane(self, lane: int) -> None:
        """Free a lane when its branch terminates."""
        if 0 <= lane < len(self._lanes):
            self._lanes[lane] = None

    def _resolve_color(self, lane: int) -> str:
        """Get or assign a persistent color for a lane."""
        if lane not in self._lane_colors:
            self._lane_colors[lane] = self._next_color()
        return self._lane_colors[lane]

    def _next_color(self) -> str:
        """Return the next color from the palette (round-robin)."""
        color = BRANCH_COLORS[self._color_index % len(BRANCH_COLORS)]
        self._color_index += 1
        return color

    def _reset(self) -> None:
        """Clear all state for a fresh allocation."""
        self._sha_to_lane.clear()
        self._lanes.clear()
        self._sha_to_color.clear()
        self._lane_colors.clear()
        self._color_index = 0
