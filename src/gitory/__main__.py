"""Gitory entry point.

Usage:
    python -m gitory
    gitory  (if installed via pip/uv)
"""

from __future__ import annotations

import sys


def main() -> None:
    """Application entry point."""
    from gitory.app import run
    sys.exit(run())


if __name__ == "__main__":
    main()
