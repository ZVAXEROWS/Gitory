#!/usr/bin/env python3
"""Build script for creating a standalone portable version of Gitory."""
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"


def main() -> int:
    """Build the portable Gitory executable using PyInstaller."""
    print("Building Portable Gitory...")

    python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

    pyinstaller_cmd = [
        python_exe,
        "-m",
        "PyInstaller",
        "--name=Gitory",
        "--windowed",
        "--onedir",
        "--clean",
        "--noconfirm",
        f"--add-data={ROOT_DIR / 'src' / 'gitory' / 'themes' / '*.qss'}{os.pathsep}gitory/themes",
        "--paths=src",
        str(ROOT_DIR / "src" / "gitory" / "__main__.py"),
    ]

    print(f"Running command: {' '.join(pyinstaller_cmd)}")
    res = subprocess.run(pyinstaller_cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"Build failed with return code {res.returncode}")
        return res.returncode

    dist_dir = ROOT_DIR / "dist" / "Gitory"
    portable_data_dir = dist_dir / "gitory_data"
    portable_data_dir.mkdir(exist_ok=True)
    (dist_dir / "PORTABLE_MODE").write_text("PORTABLE=1\n", encoding="utf-8")

    readme_path = dist_dir / "PORTABLE_README.txt"
    readme_path.write_text(
        "Gitory - Git Visualizer (Portable Edition)\n"
        "==========================================\n\n"
        "To launch Gitory, execute Gitory.exe in this folder.\n\n"
        "All configuration and recent repository settings will be automatically saved "
        "inside the local 'gitory_data' folder located alongside this executable, "
        "ensuring that your app remains 100% portable on external drives or across folders.\n",
        encoding="utf-8",
    )

    print("\nPortable build completed successfully!")
    print(f"Portable folder created at: {dist_dir}")
    print(f"To run: {dist_dir / 'Gitory.exe'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
