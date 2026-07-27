"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a temporary Git repository for testing.

    Returns:
        Path to the repository root.
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo.
    subprocess.run(["git", "init"], cwd=str(repo_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(repo_path), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(repo_path), capture_output=True, check=True,
    )

    # Create initial commit.
    readme = repo_path / "README.md"
    readme.write_text("# Test\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(repo_path), capture_output=True, check=True,
    )

    return repo_path
