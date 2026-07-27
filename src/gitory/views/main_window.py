"""Main window — the primary application window.

Assembles toolbar, sidebar, graph view, detail panel, and terminal
into a cohesive layout. Wires ViewModels to Views via signals/slots.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from gitory.domain.models.commit import Commit
from gitory.domain.models.graph import GraphLayout
from gitory.domain.models.repository import RepositoryInfo
from gitory.domain.use_cases.commit_changes import CommitChanges
from gitory.domain.use_cases.manage_tags import ManageTags
from gitory.graph_engine.layout_engine import LayoutEngine
from gitory.infrastructure.config_store import ConfigStore
from gitory.infrastructure.git_executor import GitExecutor
from gitory.infrastructure.repo_store import RepoStore
from gitory.viewmodels.branch_vm import BranchViewModel
from gitory.viewmodels.commit_detail_vm import CommitDetailViewModel
from gitory.viewmodels.graph_vm import GraphViewModel
from gitory.viewmodels.repository_vm import RepositoryViewModel
from gitory.viewmodels.settings_vm import SettingsViewModel
from gitory.viewmodels.stash_vm import StashViewModel
from gitory.views.commit_dialog import CommitDialog
from gitory.views.detail_panel import DetailPanel
from gitory.views.dialogs import (
    BranchDialog,
    ConfirmationDialog,
    RemoteDialog,
    SettingsDialog,
    TagDialog,
)
from gitory.views.diff_viewer import DiffViewer
from gitory.views.graph.graph_scene import GraphScene
from gitory.views.graph.graph_view import GraphView
from gitory.views.init_wizard import InitWizard
from gitory.views.sidebar import Sidebar
from gitory.views.terminal_panel import TerminalPanel
from gitory.views.toolbar import Toolbar
from gitory.views.welcome_view import WelcomeView


class MainWindow(QMainWindow):
    """The primary application window.

    Manages the full UI lifecycle:
    - Welcome view (no repo open)
    - Repository view (sidebar + graph + detail + terminal)

    Wires all ViewModels to Views and handles user interactions.
    """

    def __init__(
        self,
        executor: GitExecutor,
        config_store: ConfigStore,
        repo_store: RepoStore,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Gitory — Git Visualizer")
        self.setMinimumSize(1000, 700)

        # Services.
        self._executor = executor
        self._config_store = config_store
        self._repo_store = repo_store
        self._layout_engine = LayoutEngine(
            row_height=config_store.config.graph_row_height,
            lane_width=config_store.config.graph_lane_width,
        )

        # ViewModels.
        self._repo_vm = RepositoryViewModel(executor, repo_store, self)
        self._graph_vm = GraphViewModel(executor, self._layout_engine, self)
        self._detail_vm = CommitDetailViewModel(executor, self)
        self._branch_vm = BranchViewModel(executor, self)
        self._stash_vm = StashViewModel(executor, self)
        self._settings_vm = SettingsViewModel(config_store, self)

        # Build UI.
        self._build_ui()
        self._connect_signals()
        self._restore_window_state()

    def _build_ui(self) -> None:
        """Construct the window layout."""
        # Toolbar.
        self._toolbar = Toolbar(self)
        self.addToolBar(self._toolbar)

        # Status bar.
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        # Central stacked widget: welcome vs. repo view.
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # Page 0: Welcome view.
        self._welcome = WelcomeView()
        self._welcome.set_recent_repos(self._repo_store.entries)
        self._stack.addWidget(self._welcome)

        # Page 1: Repository view.
        self._repo_widget = QWidget()
        repo_layout = QVBoxLayout(self._repo_widget)
        repo_layout.setContentsMargins(0, 0, 0, 0)
        repo_layout.setSpacing(0)

        # Main horizontal splitter: sidebar | graph+detail.
        self._h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar.
        self._sidebar = Sidebar()
        self._h_splitter.addWidget(self._sidebar)

        # Graph view (center).
        self._graph_scene = GraphScene(self._layout_engine)
        self._graph_view = GraphView(self._graph_scene)
        self._h_splitter.addWidget(self._graph_view)

        # Detail panel (right).
        self._detail_panel = DetailPanel()
        self._h_splitter.addWidget(self._detail_panel)

        # Set splitter proportions: sidebar 20%, graph 55%, detail 25%.
        self._h_splitter.setStretchFactor(0, 2)
        self._h_splitter.setStretchFactor(1, 6)
        self._h_splitter.setStretchFactor(2, 2)

        # Vertical splitter: main area | terminal.
        self._v_splitter = QSplitter(Qt.Orientation.Vertical)
        self._v_splitter.addWidget(self._h_splitter)

        self._terminal = TerminalPanel()
        self._v_splitter.addWidget(self._terminal)

        # Terminal takes ~20% of height.
        self._v_splitter.setStretchFactor(0, 4)
        self._v_splitter.setStretchFactor(1, 1)

        repo_layout.addWidget(self._v_splitter)
        self._stack.addWidget(self._repo_widget)

        # Start on welcome.
        self._stack.setCurrentIndex(0)

    def _connect_signals(self) -> None:
        """Wire all signals between ViewModels and Views."""
        # Welcome view.
        self._welcome.open_clicked.connect(self._on_open_repo)
        self._welcome.init_clicked.connect(self._on_init_repo)
        self._welcome.recent_selected.connect(
            lambda path: self._repo_vm.open_repository(Path(path)),
        )

        # Toolbar.
        self._toolbar.open_repo_clicked.connect(self._on_open_repo)
        self._toolbar.init_repo_clicked.connect(self._on_init_repo)
        self._toolbar.commit_clicked.connect(self._on_commit)
        self._toolbar.commit_push_clicked.connect(self._on_commit)
        self._toolbar.push_clicked.connect(lambda: self._repo_vm.push())
        self._toolbar.pull_clicked.connect(lambda: self._repo_vm.pull())
        self._toolbar.fetch_clicked.connect(lambda: self._repo_vm.fetch())
        self._toolbar.branch_clicked.connect(self._on_create_branch)
        self._toolbar.merge_clicked.connect(self._on_merge)
        self._toolbar.rebase_clicked.connect(self._on_rebase)
        self._toolbar.checkout_clicked.connect(self._on_checkout)
        self._toolbar.reset_clicked.connect(self._on_reset)
        self._toolbar.cherry_pick_clicked.connect(self._on_cherry_pick)
        self._toolbar.stash_clicked.connect(lambda: self._stash_vm.create_stash())
        self._toolbar.tag_clicked.connect(self._on_create_tag)
        self._toolbar.refresh_clicked.connect(self._on_refresh)
        self._toolbar.settings_clicked.connect(self._on_settings)

        # Repository VM.
        self._repo_vm.repo_opened.connect(self._on_repo_opened)
        self._repo_vm.repo_closed.connect(self._on_repo_closed)
        self._repo_vm.error_occurred.connect(self._show_error)
        self._repo_vm.refresh_requested.connect(self._on_refresh)

        # Graph VM.
        self._graph_vm.graph_updated.connect(self._on_graph_updated)

        # Graph scene.
        self._graph_scene.node_clicked.connect(self._on_node_selected)

        # Detail panel.
        self._detail_vm.commit_loaded.connect(self._detail_panel.show_commit)
        self._detail_panel.show_diff_clicked.connect(self._on_show_diff)
        self._detail_panel.checkout_clicked.connect(self._detail_vm.checkout_commit)
        self._detail_panel.cherry_pick_clicked.connect(self._detail_vm.cherry_pick)
        self._detail_panel.copy_sha_clicked.connect(self._copy_sha)

        # Detail VM actions.
        self._detail_vm.action_completed.connect(
            lambda msg: (self._status_bar.showMessage(msg, 3000), self._on_refresh()),
        )
        self._detail_vm.error_occurred.connect(self._show_error)

        # Branch VM.
        self._branch_vm.branches_updated.connect(self._sidebar.update_branches)
        self._branch_vm.action_completed.connect(
            lambda msg: (self._status_bar.showMessage(msg, 3000), self._on_refresh()),
        )
        self._branch_vm.error_occurred.connect(self._show_error)

        # Stash VM.
        self._stash_vm.stashes_updated.connect(self._sidebar.update_stashes)
        self._stash_vm.action_completed.connect(
            lambda msg: self._status_bar.showMessage(msg, 3000),
        )
        self._stash_vm.error_occurred.connect(self._show_error)

        # Settings VM.
        self._settings_vm.theme_changed.connect(self._on_theme_changed)

        # Terminal.
        self._executor.command_executed.connect(self._terminal.append_command)
        self._executor.output_received.connect(self._terminal.append_output)
        self._terminal.command_entered.connect(self._on_terminal_command)

        # Sidebar.
        self._sidebar.branch_selected.connect(
            lambda name: self._branch_vm.checkout(name),
        )

    # ──────────────────────────────────────────────────────────────
    # Handlers
    # ──────────────────────────────────────────────────────────────

    def _on_open_repo(self) -> None:
        """Browse for a repository folder."""
        path = QFileDialog.getExistingDirectory(self, "Open Repository")
        if path:
            self._repo_vm.open_repository(Path(path))

    def _on_init_repo(self) -> None:
        """Show the init wizard dialog."""
        wizard = InitWizard(self)
        wizard.init_requested.connect(
            lambda path, name, readme, gitignore, license_: self._repo_vm.init_repository(
                path, name, readme, gitignore, license_,
            ),
        )
        wizard.exec()

    def _on_repo_opened(self, info: RepositoryInfo) -> None:
        """Handle successful repository open."""
        self._stack.setCurrentIndex(1)
        self._sidebar.update_repo_info(info)
        self.setWindowTitle(f"Gitory — {info.name}")
        self._status_bar.showMessage(f"Opened: {info.path}", 3000)
        self._terminal.append_info(f"Repository opened: {info.path}")

        # Load everything.
        self._on_refresh()

    def _on_repo_closed(self) -> None:
        """Handle repository close."""
        self._stack.setCurrentIndex(0)
        self._sidebar.clear()
        self._detail_panel.clear()
        self.setWindowTitle("Gitory — Git Visualizer")

    def _on_refresh(self) -> None:
        """Refresh all data from the repository."""
        if not self._repo_vm.is_repo_open:
            return

        self._graph_vm.load_graph(self._config_store.config.graph_max_commits)
        self._branch_vm.refresh()
        self._stash_vm.refresh()

        # Refresh tags.
        tag_uc = ManageTags(self._executor)
        tags = tag_uc.list_tags()
        self._sidebar.update_tags(tags)

    def _on_graph_updated(self, layout: GraphLayout) -> None:
        """Handle new graph layout."""
        node_radius = self._config_store.config.graph_node_radius
        self._graph_scene.build_from_layout(layout, node_radius)
        self._detail_vm.set_graph_layout(layout)
        self._status_bar.showMessage(
            f"Graph: {layout.node_count} commits, {layout.edge_count} edges",
            5000,
        )

    def _on_node_selected(self, sha: str) -> None:
        """Handle commit node click in the graph."""
        self._graph_vm.select_node(sha)
        self._detail_vm.load_commit(sha)

    def _on_commit(self) -> None:
        """Show the commit dialog."""
        commit_uc = CommitChanges(self._executor)
        status = commit_uc.get_status()

        dialog = CommitDialog(status, self)
        dialog.commit_requested.connect(self._do_commit)
        dialog.exec()

    def _do_commit(self, message: str, stage_all: bool, push_after: bool) -> None:
        """Execute the commit."""
        commit_uc = CommitChanges(self._executor)
        if stage_all:
            commit_uc.stage_all()

        if push_after:
            success, error = commit_uc.commit_and_push(message)
        else:
            success, error = commit_uc.commit(message)

        if success:
            self._status_bar.showMessage("Commit successful", 3000)
            self._on_refresh()
        else:
            self._show_error(error)

    def _on_create_branch(self) -> None:
        dialog = BranchDialog("Create Branch", self)
        dialog.branch_requested.connect(
            lambda name, start: self._branch_vm.create_branch(name, start),
        )
        dialog.exec()

    def _on_create_tag(self) -> None:
        dialog = TagDialog(self)
        dialog.tag_requested.connect(self._do_create_tag)
        dialog.exec()

    def _do_create_tag(self, name: str, message: str, target: str) -> None:
        tag_uc = ManageTags(self._executor)
        success, error = tag_uc.create(name, message, target)
        if success:
            self._status_bar.showMessage(f"Created tag '{name}'", 3000)
            self._on_refresh()
        else:
            self._show_error(error)

    def _on_merge(self) -> None:
        dialog = BranchDialog("Merge Branch", self)
        dialog.branch_requested.connect(
            lambda name, _: self._branch_vm.merge(name),
        )
        dialog.exec()

    def _on_rebase(self) -> None:
        if ConfirmationDialog.confirm(
            self,
            "Rebase",
            "Rebase rewrites commit history.\n\nAre you sure you want to continue?",
            "git rebase <branch>\n\nThis will rebase the current branch. "
            "Do NOT rebase commits that have been pushed to a shared remote.",
        ):
            dialog = BranchDialog("Rebase Onto", self)
            dialog.branch_requested.connect(
                lambda name, _: self._branch_vm.rebase(name),
            )
            dialog.exec()

    def _on_checkout(self) -> None:
        dialog = BranchDialog("Checkout", self)
        dialog.branch_requested.connect(
            lambda name, _: self._branch_vm.checkout(name),
        )
        dialog.exec()

    def _on_reset(self) -> None:
        if ConfirmationDialog.confirm(
            self,
            "Reset",
            "Reset will move the current branch pointer.\n\n"
            "⚠ --hard will DISCARD all uncommitted changes.\n\n"
            "Are you sure?",
            "git reset --hard <target>",
        ):
            dialog = BranchDialog("Reset To", self)
            dialog.branch_requested.connect(
                lambda target, _: self._branch_vm.reset(target, "--hard"),
            )
            dialog.exec()

    def _on_cherry_pick(self) -> None:
        if self._graph_vm.selected_sha:
            self._detail_vm.cherry_pick(self._graph_vm.selected_sha)

    def _on_show_diff(self, sha: str) -> None:
        """Open the diff viewer for a commit."""
        self._detail_vm.load_diff(sha)

        # Get diffs via use case.
        from gitory.domain.use_cases.get_diff import GetDiff
        diff_uc = GetDiff(self._executor)
        diffs = diff_uc.for_commit(sha)

        viewer = DiffViewer(self)
        viewer.set_diffs(diffs)
        viewer.setWindowTitle(f"Diff — {sha[:7]}")
        viewer.setWindowFlags(Qt.WindowType.Window)
        viewer.show()

    def _on_settings(self) -> None:
        dialog = SettingsDialog(self._config_store.config, self)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, settings: dict) -> None:
        """Apply changed settings."""
        cfg = self._config_store.config
        old_theme = cfg.theme

        cfg.theme = settings.get("theme", cfg.theme)
        cfg.animations_enabled = settings.get("animations_enabled", cfg.animations_enabled)
        cfg.graph_row_height = settings.get("graph_row_height", cfg.graph_row_height)
        cfg.graph_lane_width = settings.get("graph_lane_width", cfg.graph_lane_width)
        cfg.graph_node_radius = settings.get("graph_node_radius", cfg.graph_node_radius)
        cfg.graph_max_commits = settings.get("graph_max_commits", cfg.graph_max_commits)
        cfg.zoom_sensitivity = settings.get("zoom_sensitivity", cfg.zoom_sensitivity)
        cfg.git_executable = settings.get("git_executable", cfg.git_executable)

        self._config_store.save()

        # Update layout engine.
        self._layout_engine.row_height = cfg.graph_row_height
        self._layout_engine.lane_width = cfg.graph_lane_width
        self._graph_view.set_zoom_factor(cfg.zoom_sensitivity)

        # Update git binary.
        self._executor._git_binary = cfg.git_executable

        # Theme change.
        if cfg.theme != old_theme:
            self._settings_vm.set_theme(cfg.theme)

        # Reload graph.
        if self._repo_vm.is_repo_open:
            self._on_refresh()

    def _on_theme_changed(self, theme: str) -> None:
        """Apply new theme."""
        from gitory.themes.theme_manager import ThemeManager
        app = QGuiApplication.instance()
        if app:
            manager = ThemeManager(app)
            manager.apply_theme(theme)

    def _on_terminal_command(self, text: str) -> None:
        """Execute a manual terminal command."""
        if not self._repo_vm.is_repo_open:
            self._terminal.append_output("No repository open", is_error=True)
            return

        # Parse command — strip 'git' prefix if present.
        parts = text.strip().split()
        if not parts:
            return

        if parts[0] == "git":
            parts = parts[1:]

        result = self._executor.run(*parts)
        # Output is handled by the executor's signals.

        # Refresh if it was a state-changing command.
        state_commands = {"commit", "push", "pull", "fetch", "merge", "rebase",
                         "checkout", "branch", "tag", "stash", "reset", "cherry-pick"}
        if parts and parts[0] in state_commands:
            self._on_refresh()

    def _copy_sha(self, sha: str) -> None:
        """Copy SHA to clipboard."""
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(sha)
            self._status_bar.showMessage(f"Copied: {sha[:7]}", 2000)

    def _show_error(self, message: str) -> None:
        """Show an error message."""
        QMessageBox.warning(self, "Error", message)

    def _restore_window_state(self) -> None:
        """Restore window size and position from config."""
        cfg = self._config_store.config
        if cfg.window_maximized:
            self.showMaximized()
        else:
            self.resize(cfg.window_width, cfg.window_height)
            if cfg.window_x >= 0 and cfg.window_y >= 0:
                self.move(cfg.window_x, cfg.window_y)

    def closeEvent(self, event) -> None:
        """Save window state on close."""
        self._settings_vm.save_window_state(
            self.width(), self.height(),
            self.x(), self.y(),
            self.isMaximized(),
        )
        super().closeEvent(event)
