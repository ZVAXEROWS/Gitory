# Gitory

**A professional, cross-platform desktop Git visualizer.**

Gitory helps you *visualize*, *understand*, and *control* Git repositories through an interactive commit graph and an intuitive graphical interface. Built with Python and PySide6 (Qt6).

## Features

- **Interactive Commit Graph** — zoom, pan, and explore your repository's history as a beautiful DAG
- **Git CLI Wrapper** — every operation executes official `git` commands under the hood
- **Branch Management** — create, rename, delete, checkout, merge, rebase with visual feedback
- **Commit Workflow** — stage, unstage, commit, amend with a clean UI
- **Remote Operations** — push, pull, fetch with progress display
- **Stash & Tag Management** — full stash and tag lifecycle
- **Side-by-Side Diff Viewer** — syntax-highlighted diff comparison
- **Integrated Terminal** — see every git command executed, or type your own
- **Dark & Light Themes** — modern IDE-style appearance

## Requirements

- Python 3.12+
- Git (on PATH)
- Windows or Linux

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/gitory.git
cd gitory

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux

# Install in development mode
pip install -e ".[dev]"

# Run
gitory-gui  # or: python -m gitory
```

## Installation & Distribution

Gitory includes automated scripts to compile self-contained native installers and portable packages for both Windows and Linux without requiring target machines to have Python installed.

### Windows Setup Wizard (.exe)
To generate a professional Windows Setup Installation Wizard complete with Start Menu shortcuts and uninstaller integration (requires [Inno Setup 6](https://jrsoftware.org/isdl.php) installed on PATH or default Windows application directories):

```powershell
.venv\Scripts\python.exe build_all_installers.py
```

- **Compiled Output:** `dist/installers/Gitory-Setup-1.0.0.exe`
- **Behavior:** Configured with lowest privilege requirements (installs safely for standard users without forcing Administrator elevation prompts). Saves configurations cleanly in `~/.gitory`.

### Windows Standalone Portable Edition
If you prefer running Gitory from a USB flash drive, external hard drive, or cloud directory without installation:

```powershell
.venv\Scripts\python.exe build_portable.py
```

- **Compiled Output:** `dist/Gitory/Gitory.exe`
- **Behavior:** All app settings and recent repositories are automatically saved inside a local `gitory_data/` folder immediately beside the executable (activated by the bundled `PORTABLE_MODE` flag file).

### Linux AppImage (.AppImage)
To compile a standalone, self-contained single-file `.AppImage` directly on any Linux distribution (or WSL2/VM):

```bash
chmod +x installers/linux/build_appimage.sh
python3 build_all_installers.py
```

- **Compiled Output:** `dist/installers/Gitory-1.0.0-x86_64.AppImage`
- **How to Install and Run:**
  ```bash
  chmod +x dist/installers/Gitory-1.0.0-x86_64.AppImage
  ./dist/installers/Gitory-1.0.0-x86_64.AppImage
  ```
  *Note: On Linux, an AppImage is a complete portable application bundle. "Installing" simply means giving the file execution permissions (`chmod +x`) and running it or placing it into `/usr/local/bin/` or your Applications directory.*

### Automated Cloud Builds (GitHub Actions CI/CD)
Even if you are developing solely on Windows, you can generate ready-to-run Linux `.AppImage` packages and Windows Setup Wizards automatically using GitHub cloud runners:

1. Push your repository code to GitHub.
2. Open your repository on **GitHub.com** and navigate to the **Actions** tab.
3. On the left sidebar, click **Build Cross-Platform Installers**, then click **Run workflow**.
4. Within minutes, concurrent Windows and Ubuntu cloud runners will compile both the Windows Setup Wizard (`.exe`) and the Linux AppImage (`.AppImage`).
5. Download your compiled packages directly from the workflow Artifacts or Release attachments.

## Architecture

Gitory follows **Clean Architecture** with the **MVVM** pattern:

```
src/gitory/
├── domain/          # Pure business logic (no Qt dependency)
│   ├── models/      # Data classes: Commit, Branch, Tag, etc.
│   └── use_cases/   # Application business rules
├── infrastructure/  # Git CLI subprocess wrapper, config persistence
├── graph_engine/    # DAG layout algorithm (greedy lane assignment)
├── viewmodels/      # State management, Qt Signals
├── views/           # PySide6 widgets and dialogs
└── themes/          # QSS stylesheets
```

## License

MIT
