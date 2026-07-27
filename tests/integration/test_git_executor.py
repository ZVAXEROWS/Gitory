"""Integration tests for GitExecutor running against real git repositories."""

from __future__ import annotations

from pathlib import Path

from gitory.infrastructure.git_executor import GitExecutor


def test_check_git_installed(qapp):
    """Test that git executable can be found and executed."""
    executor = GitExecutor()
    result = executor.check_git_installed()
    assert result.success is True
    assert "git version" in result.output.lower()


def test_is_git_repository_on_valid_repo(tmp_repo: Path, qapp):
    """Test repository detection on a valid repo."""
    executor = GitExecutor()
    assert executor.is_git_repository(tmp_repo) is True


def test_is_git_repository_on_non_repo(tmp_path: Path, qapp):
    """Test repository detection on an empty, non-repo folder."""
    executor = GitExecutor()
    assert executor.is_git_repository(tmp_path) is False


def test_run_command_in_repo(tmp_repo: Path, qapp):
    """Test executing a git status command in a repository."""
    executor = GitExecutor(repo_path=tmp_repo)
    result = executor.run("status", "--short")
    assert result.success is True
    assert result.output == ""  # Clean working tree right after commit in fixture


def test_signal_emission(tmp_repo: Path, qapp, qtmodeltester):
    """Test that command_executed and output_received signals are emitted."""
    executor = GitExecutor(repo_path=tmp_repo)

    commands = []
    outputs = []

    executor.command_executed.connect(commands.append)
    executor.output_received.connect(lambda text, is_error: outputs.append((text, is_error)))

    result = executor.run("rev-parse", "--abbrev-ref", "HEAD")
    assert result.success is True

    assert len(commands) == 1
    assert "git -C" in commands[0]
    assert len(outputs) == 1
    assert outputs[0][0] == result.output
    assert outputs[0][1] is False
