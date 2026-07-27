"""Tests for GitParser — parsing git CLI output into domain models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gitory.infrastructure.git_parser import GitParser


class TestParseLog:
    """Tests for GitParser.parse_log()."""

    def test_empty_input(self):
        assert GitParser.parse_log("") == []

    def test_single_commit(self):
        # Build a log entry using the same separator.
        sep = "\x1f"
        rec_sep = "\x1e"
        raw = sep.join([
            "abc1234567890abcdef1234567890abcdef123456",
            "",  # No parents (root commit)
            "Test Author",
            "test@example.com",
            "1700000000",
            "Initial commit",
            "HEAD -> main",
        ]) + rec_sep

        commits = GitParser.parse_log(raw)
        assert len(commits) == 1

        c = commits[0]
        assert c.sha == "abc1234567890abcdef1234567890abcdef123456"
        assert c.short_sha == "abc1234"
        assert c.author_name == "Test Author"
        assert c.author_email == "test@example.com"
        assert c.subject == "Initial commit"
        assert c.is_root is True
        assert c.is_merge is False
        assert c.is_head is True
        assert "main" in c.branches

    def test_merge_commit(self):
        sep = "\x1f"
        rec_sep = "\x1e"
        sha_a = "a" * 40
        sha_b = "b" * 40
        sha_c = "c" * 40
        raw = sep.join([
            sha_a,
            sha_b + " " + sha_c,
            "Author",
            "a@b.com",
            "1700000000",
            "Merge branch feature",
            "",
        ]) + rec_sep

        commits = GitParser.parse_log(raw)
        assert len(commits) == 1
        assert commits[0].is_merge is True
        assert len(commits[0].parent_shas) == 2

    def test_tag_detection(self):
        sep = "\x1f"
        rec_sep = "\x1e"
        raw = sep.join([
            "d" * 40,
            "e" * 40,
            "Author",
            "a@b.com",
            "1700000000",
            "Tagged commit",
            "tag: v1.0.0, main",
        ]) + rec_sep

        commits = GitParser.parse_log(raw)
        assert "v1.0.0" in commits[0].tags
        assert "main" in commits[0].branches

    def test_multiple_commits(self):
        sep = "\x1f"
        rec_sep = "\x1e"
        # Use hex characters to create valid-looking SHAs.
        hex_chars = "0123456789abcdef"
        lines = []
        for i in range(5):
            sha = hex_chars[i] * 40
            parent = hex_chars[i - 1] * 40 if i > 0 else ""
            line = sep.join([sha, parent, "Author", "a@b.com", "1700000000", f"Commit {i}", ""])
            lines.append(line)
        raw = rec_sep.join(lines) + rec_sep

        commits = GitParser.parse_log(raw)
        assert len(commits) == 5


class TestParseBranches:
    """Tests for GitParser.parse_branches()."""

    def test_empty(self):
        assert GitParser.parse_branches("") == []

    def test_local_branch(self):
        raw = "main abc1234 * origin/main\n"
        branches = GitParser.parse_branches(raw)
        assert len(branches) == 1
        assert branches[0].name == "main"
        assert branches[0].is_current is True
        assert branches[0].tracking == "origin/main"


class TestParseStatus:
    """Tests for GitParser.parse_status()."""

    def test_empty(self):
        result = GitParser.parse_status("")
        assert result.is_clean is True

    def test_branch_info(self):
        raw = (
            "# branch.oid abc1234\n"
            "# branch.head main\n"
            "# branch.upstream origin/main\n"
            "# branch.ab +2 -1\n"
        )
        result = GitParser.parse_status(raw)
        assert result.branch == "main"
        assert result.upstream == "origin/main"
        assert result.ahead == 2
        assert result.behind == 1

    def test_untracked_file(self):
        raw = "? new_file.py\n"
        result = GitParser.parse_status(raw)
        assert len(result.untracked_entries) == 1
        assert result.untracked_entries[0].path == "new_file.py"


class TestParseStashList:
    """Tests for GitParser.parse_stash_list()."""

    def test_empty(self):
        assert GitParser.parse_stash_list("") == []

    def test_single_stash(self):
        raw = "stash@{0}|abc1234567890abcdef1234567890abcdef123456|On main: WIP\n"
        stashes = GitParser.parse_stash_list(raw)
        assert len(stashes) == 1
        assert stashes[0].index == 0
        assert stashes[0].branch == "main"
        assert stashes[0].ref == "stash@{0}"


class TestParseDiff:
    """Tests for GitParser.parse_diff()."""

    def test_empty(self):
        assert GitParser.parse_diff("") == []

    def test_simple_addition(self):
        raw = (
            "diff --git a/file.py b/file.py\n"
            "new file mode 100644\n"
            "index 0000000..abc1234\n"
            "--- /dev/null\n"
            "+++ b/file.py\n"
            "@@ -0,0 +1,3 @@\n"
            "+line 1\n"
            "+line 2\n"
            "+line 3\n"
        )
        diffs = GitParser.parse_diff(raw)
        assert len(diffs) == 1
        assert diffs[0].status.name == "ADDED"
        assert diffs[0].additions == 3
