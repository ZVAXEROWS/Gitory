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
gitory
```

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
