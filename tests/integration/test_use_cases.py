"""Integration tests for Domain Use Cases against real git repositories."""

from __future__ import annotations

from pathlib import Path

from gitory.domain.use_cases.build_graph import BuildGraph
from gitory.domain.use_cases.commit_changes import CommitChanges
from gitory.domain.use_cases.get_diff import GetDiff
from gitory.domain.use_cases.init_repository import InitRepository
from gitory.domain.use_cases.manage_branches import ManageBranches
from gitory.domain.use_cases.open_repository import OpenRepository
from gitory.graph_engine.layout_engine import LayoutEngine
from gitory.infrastructure.git_executor import GitExecutor


def test_open_repository(tmp_repo: Path, qapp):
    """Test opening an existing repository."""
    executor = GitExecutor()
    open_uc = OpenRepository(executor)

    info, error_msg = open_uc.execute(tmp_repo)
    assert error_msg == ""
    assert info is not None
    assert info.path == tmp_repo
    assert len(info.head_sha) == 40


def test_init_repository(tmp_path: Path, qapp):
    """Test initializing a new repository from scratch."""
    new_repo_dir = tmp_path / "my_new_repo"
    new_repo_dir.mkdir()

    executor = GitExecutor()
    init_uc = InitRepository(executor)

    success, error_msg = init_uc.execute(
        path=new_repo_dir,
        name="Test Repo",
        create_readme=True,
        create_gitignore=True,
        create_license=False,
    )
    assert success is True, f"Failed: {error_msg}"
    assert (new_repo_dir / ".git").exists()
    assert (new_repo_dir / "README.md").exists()
    assert (new_repo_dir / ".gitignore").exists()


def test_manage_branches(tmp_repo: Path, qapp):
    """Test branch listing and branch creation."""
    executor = GitExecutor(repo_path=tmp_repo)
    branch_uc = ManageBranches(executor)

    branches = branch_uc.list_branches()
    assert len(branches) >= 1
    current = next((b for b in branches if b.is_current), None)
    assert current is not None

    # Create new branch
    success, error = branch_uc.create("feature/login")
    assert success is True, error

    branches_after = branch_uc.list_branches()
    assert len(branches_after) == len(branches) + 1
    assert any(b.name == "feature/login" for b in branches_after)


def test_commit_and_diff_use_cases(tmp_repo: Path, qapp):
    """Test staging changes, creating a commit, and checking git diffs."""
    executor = GitExecutor(repo_path=tmp_repo)
    commit_uc = CommitChanges(executor)
    diff_uc = GetDiff(executor)

    # Modify README.md in working tree
    readme = tmp_repo / "README.md"
    readme.write_text("# Updated Content\n", encoding="utf-8")

    status_before = commit_uc.get_status()
    assert not status_before.is_clean
    assert len(status_before.unstaged_entries) == 1

    # Stage and commit
    success_stage, error_stage = commit_uc.stage_all()
    assert success_stage is True, error_stage
    success, error = commit_uc.commit("Second commit message")
    assert success is True, error

    status_after = commit_uc.get_status()
    assert status_after.is_clean

    # Test BuildGraph to verify 2 commits exist in history
    layout_engine = LayoutEngine()
    build_uc = BuildGraph(executor, layout_engine)
    layout = build_uc.execute()

    assert layout.node_count == 2
    assert layout.edge_count == 1

    # Check diff for newest commit
    newest_sha = next(sha for sha, node in layout.nodes.items() if node.is_head)
    diffs = diff_uc.for_commit(newest_sha)
    assert len(diffs) == 1
    assert diffs[0].display_path == "README.md"
