"""Recent repositories store.

Persists a list of recently opened repositories to a JSON file
in the user's config directory.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum number of recent repositories to remember.
MAX_RECENT = 20


def _default_config_dir() -> Path:
    """Return the default configuration directory.

    In portable mode (when a 'PORTABLE_MODE' marker file exists next to the executable
    or GITORY_PORTABLE=1 is set), configuration is saved in a local 'gitory_data' folder.
    Otherwise (when installed via Wizard installer or AppImage), it is stored in ~/.gitory.
    """
    import os
    import sys

    if os.environ.get("GITORY_PORTABLE") == "1":
        return Path.cwd() / "gitory_data"

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        if (exe_dir / "PORTABLE_MODE").exists():
            return exe_dir / "gitory_data"

    return Path.home() / ".gitory"


@dataclass(slots=True)
class RecentEntry:
    """A single recent repository entry.

    Attributes:
        path: Absolute path to the repository root.
        name: Display name of the repository.
        last_opened: ISO-8601 timestamp of last access.
    """

    path: str
    name: str
    last_opened: str = ""


class RepoStore:
    """Manages the list of recently opened repositories.

    Persists to ~/.gitory/recent.json.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the store.

        Args:
            config_dir: Directory for config files. Defaults to ~/.gitory.
        """
        self._config_dir = config_dir or _default_config_dir()
        self._file = self._config_dir / "recent.json"
        self._entries: list[RecentEntry] = []
        self._load()

    @property
    def entries(self) -> list[RecentEntry]:
        """Ordered list of recent repositories (most recent first)."""
        return list(self._entries)

    def add(self, path: Path, name: str = "") -> None:
        """Add or promote a repository in the recent list.

        If the repository already exists, it's moved to the top.
        The list is capped at MAX_RECENT entries.

        Args:
            path: Path to the repository root.
            name: Display name (defaults to folder name).
        """
        from datetime import datetime

        path_str = str(path.resolve())
        name = name or path.name

        # Remove existing entry with same path.
        self._entries = [e for e in self._entries if e.path != path_str]

        # Add to the front.
        self._entries.insert(0, RecentEntry(
            path=path_str,
            name=name,
            last_opened=datetime.now(tz=UTC).isoformat(),
        ))

        # Trim to max.
        self._entries = self._entries[:MAX_RECENT]
        self._save()

    def remove(self, path: Path) -> None:
        """Remove a repository from the recent list.

        Args:
            path: Path to remove.
        """
        path_str = str(path.resolve())
        self._entries = [e for e in self._entries if e.path != path_str]
        self._save()

    def clear(self) -> None:
        """Clear all recent repositories."""
        self._entries.clear()
        self._save()

    def _load(self) -> None:
        """Load entries from disk."""
        if not self._file.exists():
            return

        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            self._entries = [RecentEntry(**entry) for entry in data]
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning("Failed to load recent repositories: %s", e)
            self._entries = []

    def _save(self) -> None:
        """Persist entries to disk."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        data = [asdict(entry) for entry in self._entries]
        self._file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
