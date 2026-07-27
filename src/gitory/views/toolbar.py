"""Toolbar — top action bar with git operation buttons.

Every button has an icon (using text emoji as placeholder), tooltip with
git command, explanation, and destructive action warnings.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QWidget


class Toolbar(QToolBar):
    """Application toolbar with all git operation buttons.

    Signals for each action are emitted when the corresponding button
    is clicked. The MainWindow connects these to ViewModels.
    """

    # Repository actions.
    open_repo_clicked = Signal()
    init_repo_clicked = Signal()

    # Commit actions.
    commit_clicked = Signal()
    commit_push_clicked = Signal()

    # Remote actions.
    push_clicked = Signal()
    pull_clicked = Signal()
    fetch_clicked = Signal()

    # Branch actions.
    branch_clicked = Signal()
    merge_clicked = Signal()
    rebase_clicked = Signal()
    checkout_clicked = Signal()
    reset_clicked = Signal()
    cherry_pick_clicked = Signal()

    # Stash / tag.
    stash_clicked = Signal()
    tag_clicked = Signal()

    # Utility.
    refresh_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Main Toolbar", parent)
        self.setObjectName("mainToolbar")
        self.setMovable(False)

        self._build_actions()

    def _build_actions(self) -> None:
        """Create all toolbar buttons with tooltips."""
        # --- Repository ---
        self._add_action(
            "📂 Open", "Open Repository",
            "Open an existing Git repository.\n\nBrowse to a folder containing a .git directory.",
            self.open_repo_clicked,
        )
        self._add_action(
            "🆕 Init", "Initialize Repository",
            "Create a new Git repository.\n\ngit init\n\nSets up a new .git directory in the selected folder.",
            self.init_repo_clicked,
        )

        self.addSeparator()

        # --- Commit ---
        self._add_action(
            "✅ Commit", "Commit",
            "Commit staged changes.\n\ngit commit -m \"message\"\n\nRecords staged changes as a new commit.",
            self.commit_clicked,
        )
        self._add_action(
            "📤 Commit+Push", "Commit & Push",
            "Commit and push in one step.\n\ngit commit + git push\n\nRecords changes and uploads to remote.",
            self.commit_push_clicked,
        )

        self.addSeparator()

        # --- Remote ---
        self._add_action(
            "⬆ Push", "Push",
            "Push commits to remote.\n\ngit push origin <branch>\n\nUploads local commits to the remote repository.",
            self.push_clicked,
        )
        self._add_action(
            "⬇ Pull", "Pull",
            "Pull from remote.\n\ngit pull origin <branch>\n\nDownloads and integrates remote changes.",
            self.pull_clicked,
        )
        self._add_action(
            "🔄 Fetch", "Fetch",
            "Fetch from all remotes.\n\ngit fetch --all --prune\n\nDownloads remote data without merging.",
            self.fetch_clicked,
        )

        self.addSeparator()

        # --- Branch ---
        self._add_action(
            "🌿 Branch", "Create Branch",
            "Create a new branch.\n\ngit branch <name>\n\nCreates a new branch pointer at the current commit.",
            self.branch_clicked,
        )
        self._add_action(
            "🔀 Merge", "Merge",
            "Merge a branch.\n\ngit merge <branch>\n\nIntegrates changes from another branch into the current one.",
            self.merge_clicked,
        )
        self._add_action(
            "📐 Rebase", "Rebase",
            "Rebase onto another branch.\n\ngit rebase <branch>\n\n⚠ WARNING: Rewrites commit history.\nDo not rebase published commits.",
            self.rebase_clicked,
        )
        self._add_action(
            "↩ Checkout", "Checkout",
            "Switch to a branch or commit.\n\ngit checkout <ref>\n\nUpdates the working tree to match the target.",
            self.checkout_clicked,
        )
        self._add_action(
            "⏪ Reset", "Reset",
            "Reset current branch.\n\ngit reset <mode> <target>\n\n⚠ WARNING: --hard discards ALL working directory changes.\nThis cannot be undone easily.",
            self.reset_clicked,
        )
        self._add_action(
            "🍒 Cherry Pick", "Cherry Pick",
            "Cherry-pick a commit.\n\ngit cherry-pick <sha>\n\nApplies changes from a specific commit onto the current branch.",
            self.cherry_pick_clicked,
        )

        self.addSeparator()

        # --- Stash / Tag ---
        self._add_action(
            "📦 Stash", "Stash",
            "Manage stashes.\n\ngit stash push\n\nTemporarily saves uncommitted changes.",
            self.stash_clicked,
        )
        self._add_action(
            "🏷 Tag", "Create Tag",
            "Manage tags.\n\ngit tag <name>\n\nCreates a named reference to a specific commit.",
            self.tag_clicked,
        )

        self.addSeparator()

        # --- Utility ---
        self._add_action(
            "🔃 Refresh", "Refresh",
            "Refresh the repository view.\n\nReloads all data from the git repository.",
            self.refresh_clicked,
        )
        self._add_action(
            "⚙ Settings", "Settings",
            "Application settings.\n\nConfigure theme, graph appearance, git executable path, etc.",
            self.settings_clicked,
        )

    def _add_action(
        self,
        text: str,
        name: str,
        tooltip: str,
        signal: Signal,
    ) -> QAction:
        """Create and add a toolbar action.

        Args:
            text: Button text with emoji icon.
            name: Action name for accessibility.
            tooltip: Rich tooltip text.
            signal: Signal to emit on click.

        Returns:
            The created QAction.
        """
        action = QAction(text, self)
        action.setObjectName(f"action{name.replace(' ', '')}")
        action.setToolTip(tooltip)
        action.setStatusTip(name)
        action.triggered.connect(signal.emit)
        self.addAction(action)
        return action
