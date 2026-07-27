"""Git output parser.

Transforms raw git CLI output strings into domain model objects.
All parsing methods are stateless (static/class methods) — they receive
raw text and return typed domain objects.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from gitory.domain.models.branch import Branch
from gitory.domain.models.commit import Commit
from gitory.domain.models.diff import (
    DiffHunk,
    DiffLine,
    DiffStatus,
    FileDiff,
    FileStatus,
    LineType,
    StatusEntry,
    StatusResult,
)
from gitory.domain.models.stash import StashEntry
from gitory.domain.models.tag import Tag

# Separator used in --pretty=format strings to split fields.
_FIELD_SEP = "\x1f"  # ASCII Unit Separator (non-printable, safe delimiter)
_RECORD_SEP = "\x1e"  # ASCII Record Separator


class GitParser:
    """Static methods to parse git CLI output into domain models.

    The parser is designed to work with specific --pretty=format strings
    that use ASCII control characters as delimiters, avoiding conflicts
    with user content (commit messages, branch names, etc.).
    """

    # The format string that git_executor should use for `git log`.
    LOG_FORMAT = _FIELD_SEP.join([
        "%H",   # Full hash
        "%P",   # Parent hashes (space-separated)
        "%an",  # Author name
        "%ae",  # Author email
        "%at",  # Author timestamp (unix epoch)
        "%s",   # Subject (first line of message)
        "%D",   # Ref names (branches, tags, HEAD)
    ]) + _RECORD_SEP

    @staticmethod
    def parse_log(raw: str, head_sha: str = "") -> list[Commit]:
        """Parse output of `git log --pretty=format:LOG_FORMAT`.

        Args:
            raw: Raw stdout from git log.
            head_sha: SHA of the current HEAD commit (to mark is_head).

        Returns:
            List of Commit objects, ordered as git log returned them
            (typically newest first in topo order).
        """
        commits: list[Commit] = []
        if not raw.strip():
            return commits

        records = raw.strip().split(_RECORD_SEP)
        for record in records:
            record = record.strip()
            if not record:
                continue

            fields = record.split(_FIELD_SEP)
            if len(fields) < 7:
                continue

            sha = fields[0].strip()
            parent_str = fields[1].strip()
            author_name = fields[2].strip()
            author_email = fields[3].strip()
            timestamp_str = fields[4].strip()
            subject = fields[5].strip()
            refs_str = fields[6].strip()

            # Parse parents.
            parent_shas = parent_str.split() if parent_str else []

            # Parse timestamp.
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)
            except (ValueError, OSError):
                timestamp = datetime.now(tz=timezone.utc)

            # Parse ref decorations (branches, tags, HEAD).
            branches: list[str] = []
            tags: list[str] = []
            is_head = sha == head_sha

            if refs_str:
                for ref in refs_str.split(","):
                    ref = ref.strip()
                    if not ref:
                        continue
                    if ref == "HEAD":
                        is_head = True
                    elif ref.startswith("HEAD -> "):
                        is_head = True
                        branch_name = ref.removeprefix("HEAD -> ")
                        branches.append(branch_name)
                    elif ref.startswith("tag: "):
                        tags.append(ref.removeprefix("tag: "))
                    else:
                        branches.append(ref)

            commits.append(Commit(
                sha=sha,
                message=subject,
                author_name=author_name,
                author_email=author_email,
                timestamp=timestamp,
                parent_shas=parent_shas,
                branches=branches,
                tags=tags,
                is_head=is_head,
            ))

        return commits

    @staticmethod
    def parse_branches(raw: str) -> list[Branch]:
        """Parse output of `git branch -a --format='...'`.

        Expected format per line:
            %(refname:short) %(objectname:short) %(HEAD) %(upstream:short)

        Args:
            raw: Raw stdout from git branch.

        Returns:
            List of Branch objects (local and remote).
        """
        branches: list[Branch] = []
        if not raw.strip():
            return branches

        for line in raw.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            name = parts[0]
            tip_sha = parts[1]
            is_current = parts[2] == "*"
            tracking = parts[3] if len(parts) > 3 else None

            is_remote = name.startswith("origin/") or "/" in name
            remote_name = name.split("/")[0] if is_remote else None

            # Skip HEAD pointer in remote branches.
            if name == "origin/HEAD":
                continue

            branches.append(Branch(
                name=name,
                tip_sha=tip_sha,
                is_remote=is_remote,
                is_current=is_current,
                tracking=tracking,
                remote_name=remote_name,
            ))

        return branches

    @staticmethod
    def parse_tags(raw: str) -> list[Tag]:
        """Parse output of `git tag -l --format='...'`.

        Expected format per line:
            %(refname:short) %(objectname:short) %(*objectname:short) %(contents:subject)

        Args:
            raw: Raw stdout from git tag.

        Returns:
            List of Tag objects.
        """
        tags: list[Tag] = []
        if not raw.strip():
            return tags

        for line in raw.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            # Use the field separator format.
            parts = line.split(_FIELD_SEP) if _FIELD_SEP in line else line.split(maxsplit=2)

            if len(parts) < 2:
                continue

            name = parts[0].strip()
            sha = parts[1].strip()
            message = parts[2].strip() if len(parts) > 2 else None

            # If the tag has a dereferenced object (*objectname), it's annotated.
            is_annotated = bool(message)

            tags.append(Tag(
                name=name,
                sha=sha,
                message=message if message else None,
                is_annotated=is_annotated,
            ))

        return tags

    @staticmethod
    def parse_stash_list(raw: str) -> list[StashEntry]:
        """Parse output of `git stash list --format='%gd|%H|%gs'`.

        Args:
            raw: Raw stdout from git stash list.

        Returns:
            List of StashEntry objects.
        """
        stashes: list[StashEntry] = []
        if not raw.strip():
            return stashes

        for line in raw.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            parts = line.split("|", maxsplit=2)
            if len(parts) < 3:
                continue

            ref = parts[0].strip()      # e.g., "stash@{0}"
            sha = parts[1].strip()
            message = parts[2].strip()

            # Extract index from ref string.
            match = re.search(r"\{(\d+)\}", ref)
            index = int(match.group(1)) if match else 0

            # Extract branch from message if available.
            branch = ""
            branch_match = re.match(r"On (\S+):", message)
            if branch_match:
                branch = branch_match.group(1)

            stashes.append(StashEntry(
                index=index,
                message=message,
                sha=sha,
                branch=branch,
            ))

        return stashes

    @staticmethod
    def parse_status(raw: str) -> StatusResult:
        """Parse output of `git status --porcelain=v2 --branch`.

        Porcelain v2 format reference:
            # branch.oid <sha>
            # branch.head <name>
            # branch.upstream <name>
            # branch.ab +<ahead> -<behind>
            1 <XY> ... <path>
            2 <XY> ... <path>\t<origPath>
            ? <path>
            ! <path>

        Args:
            raw: Raw stdout from git status --porcelain=v2.

        Returns:
            StatusResult with branch info and file entries.
        """
        result = StatusResult()
        if not raw.strip():
            return result

        for line in raw.strip().splitlines():
            line = line.rstrip()
            if not line:
                continue

            if line.startswith("# branch.head "):
                result.branch = line.removeprefix("# branch.head ").strip()
            elif line.startswith("# branch.upstream "):
                result.upstream = line.removeprefix("# branch.upstream ").strip()
            elif line.startswith("# branch.ab "):
                ab = line.removeprefix("# branch.ab ").strip()
                parts = ab.split()
                if len(parts) >= 2:
                    result.ahead = int(parts[0].lstrip("+"))
                    result.behind = abs(int(parts[1].lstrip("-")))
            elif line.startswith("1 ") or line.startswith("2 "):
                # Ordinary or rename/copy entry.
                parts = line.split(maxsplit=8)
                if len(parts) >= 9:
                    xy = parts[1]
                    index_status = FileStatus(xy[0]) if xy[0] in FileStatus._value2member_map_ else FileStatus.UNMODIFIED
                    worktree_status = FileStatus(xy[1]) if xy[1] in FileStatus._value2member_map_ else FileStatus.UNMODIFIED

                    path_part = parts[8]
                    old_path = None
                    if "\t" in path_part:
                        path, old_path = path_part.split("\t", maxsplit=1)
                    else:
                        path = path_part

                    result.entries.append(StatusEntry(
                        path=path,
                        index_status=index_status,
                        worktree_status=worktree_status,
                        old_path=old_path,
                    ))
            elif line.startswith("? "):
                # Untracked file.
                path = line[2:].strip()
                result.entries.append(StatusEntry(
                    path=path,
                    index_status=FileStatus.UNMODIFIED,
                    worktree_status=FileStatus.UNTRACKED,
                ))
            elif line.startswith("! "):
                # Ignored file — typically not shown, but handle gracefully.
                pass

        return result

    @staticmethod
    def parse_diff(raw: str) -> list[FileDiff]:
        """Parse unified diff output from `git diff` or `git diff-tree -p`.

        Args:
            raw: Raw unified diff output.

        Returns:
            List of FileDiff objects, one per changed file.
        """
        files: list[FileDiff] = []
        if not raw.strip():
            return files

        # Split into per-file sections (each starts with 'diff --git').
        sections = re.split(r"(?=^diff --git )", raw, flags=re.MULTILINE)

        for section in sections:
            section = section.strip()
            if not section.startswith("diff --git"):
                continue

            # Parse file paths from the diff header.
            header_match = re.match(r"diff --git a/(.*?) b/(.*?)$", section, re.MULTILINE)
            if not header_match:
                continue

            old_path = header_match.group(1)
            new_path = header_match.group(2)

            # Determine status from diff metadata.
            is_binary = "Binary files" in section
            status = DiffStatus.MODIFIED

            if "new file mode" in section:
                status = DiffStatus.ADDED
            elif "deleted file mode" in section:
                status = DiffStatus.DELETED
            elif "rename from" in section:
                status = DiffStatus.RENAMED

            # Parse hunks.
            hunks: list[DiffHunk] = []
            additions = 0
            deletions = 0

            hunk_pattern = re.compile(
                r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$",
                re.MULTILINE,
            )

            hunk_starts = list(hunk_pattern.finditer(section))
            for i, match in enumerate(hunk_starts):
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                header = match.group(5).strip()

                # Get lines until next hunk or end of section.
                start_pos = match.end()
                end_pos = hunk_starts[i + 1].start() if i + 1 < len(hunk_starts) else len(section)
                hunk_text = section[start_pos:end_pos]

                lines: list[DiffLine] = []
                old_line = old_start
                new_line = new_start

                for raw_line in hunk_text.splitlines():
                    if not raw_line:
                        continue

                    if raw_line.startswith("+"):
                        lines.append(DiffLine(
                            type=LineType.ADDITION,
                            content=raw_line[1:],
                            old_line_no=None,
                            new_line_no=new_line,
                        ))
                        new_line += 1
                        additions += 1
                    elif raw_line.startswith("-"):
                        lines.append(DiffLine(
                            type=LineType.DELETION,
                            content=raw_line[1:],
                            old_line_no=old_line,
                            new_line_no=None,
                        ))
                        old_line += 1
                        deletions += 1
                    elif raw_line.startswith(" "):
                        lines.append(DiffLine(
                            type=LineType.CONTEXT,
                            content=raw_line[1:],
                            old_line_no=old_line,
                            new_line_no=new_line,
                        ))
                        old_line += 1
                        new_line += 1
                    elif raw_line.startswith("\\"):
                        # "\ No newline at end of file" — skip.
                        pass

                hunks.append(DiffHunk(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    header=header,
                    lines=lines,
                ))

            files.append(FileDiff(
                old_path=old_path,
                new_path=new_path,
                status=status,
                hunks=hunks,
                additions=additions,
                deletions=deletions,
                is_binary=is_binary,
            ))

        return files

    @staticmethod
    def parse_head_sha(raw: str) -> str:
        """Parse output of `git rev-parse HEAD`.

        Returns:
            The HEAD commit SHA, or empty string if parsing fails.
        """
        return raw.strip()[:40] if raw.strip() else ""

    @staticmethod
    def parse_current_branch(raw: str) -> tuple[str, bool]:
        """Parse output of `git symbolic-ref --short HEAD` or `git branch --show-current`.

        Returns:
            Tuple of (branch_name, is_detached). If detached, branch_name
            is empty and is_detached is True.
        """
        branch = raw.strip()
        if not branch or "HEAD" in branch:
            return ("", True)
        return (branch, False)

    @staticmethod
    def parse_remote_url(raw: str) -> str | None:
        """Parse output of `git remote get-url origin`.

        Returns:
            Remote URL string, or None if not configured.
        """
        url = raw.strip()
        return url if url else None

    @staticmethod
    def parse_remotes(raw: str) -> dict[str, str]:
        """Parse output of `git remote -v`.

        Returns:
            Dictionary mapping remote names to their fetch URLs.
        """
        remotes: dict[str, str] = {}
        for line in raw.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2 and "(fetch)" in line:
                remotes[parts[0]] = parts[1]
        return remotes
