"""Build graph use case.

Fetches commit history and computes the graph layout.
"""

from __future__ import annotations

from gitory.domain.models.graph import GraphLayout
from gitory.graph_engine.layout_engine import LayoutEngine
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.git_parser import GitParser


class BuildGraph:
    """Loads commit history and computes the visual graph layout."""

    def __init__(self, executor: GitExecutor, layout_engine: LayoutEngine) -> None:
        self._executor = executor
        self._layout_engine = layout_engine

    def execute(self, max_commits: int = 500) -> GraphLayout:
        """Build the graph layout for the current repository.

        Args:
            max_commits: Maximum number of commits to load.

        Returns:
            Computed GraphLayout with positioned nodes and edges.
        """
        # Get HEAD SHA for marking.
        head_result = self._executor.run("rev-parse", "HEAD")
        head_sha = GitParser.parse_head_sha(head_result.output) if head_result.success else ""

        # Fetch commit log.
        result = self._executor.run(
            "log",
            "--all",
            "--topo-order",
            f"--pretty=format:{GitParser.LOG_FORMAT}",
            f"--max-count={max_commits}",
        )

        if not result.success:
            return GraphLayout()

        # Parse commits.
        commits = GitParser.parse_log(result.output, head_sha)

        if not commits:
            return GraphLayout()

        # Compute layout.
        return self._layout_engine.compute(commits)
