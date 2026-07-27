#!/usr/bin/env python3
"""Unified cross-platform installer generator for Gitory.

On Windows: Compiles the application via PyInstaller and generates a modern Setup Wizard
            installer (Gitory-Setup-1.0.0.exe) using Inno Setup Compiler (ISCC.exe).
On Linux:   Executes build_appimage.sh to compile a self-contained AppImage package
            (Gitory-1.0.0-x86_64.AppImage).
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"


def find_iscc() -> Path | None:
    """Locate Inno Setup Compiler (ISCC.exe) across standard Windows locations."""
    iscc_on_path = shutil.which("ISCC")
    if iscc_on_path:
        return Path(iscc_on_path)

    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
    ]

    for cand in candidates:
        if cand.exists():
            return cand
    return None


def build_windows_installer() -> int:
    """Build Windows standalone binary and Inno Setup installation wizard."""
    print("=================================================")
    print(" Building Gitory Windows Setup Wizard Installer  ")
    print("=================================================")

    python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

    print("Step 1: Compiling standalone binary via PyInstaller...")
    pyi_cmd = [
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
    res = subprocess.run(pyi_cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"Error: PyInstaller compilation failed (code {res.returncode})")
        return res.returncode

    print("Step 2: Locating Inno Setup Compiler (ISCC.exe)...")
    iscc_exe = find_iscc()
    if not iscc_exe:
        print(
            "Error: ISCC.exe not found! Please install Inno Setup 6 from https://jrsoftware.org/isdl.php "
            "or run: winget install JRSoftware.InnoSetup --silent"
        )
        return 1

    print(f"Found Inno Setup Compiler at: {iscc_exe}")
    iss_path = ROOT_DIR / "installers" / "windows" / "gitory_setup.iss"

    print("Step 3: Compiling Gitory-Setup-1.0.0.exe installation wizard...")
    iscc_cmd = [str(iscc_exe), str(iss_path)]
    res = subprocess.run(iscc_cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"Error: Inno Setup compilation failed (code {res.returncode})")
        return res.returncode

    output_exe = ROOT_DIR / "dist" / "installers" / "Gitory-Setup-1.0.0.exe"
    print("=================================================")
    print(" Windows Setup Wizard installer build complete!")
    print(f" Output Installer: {output_exe}")
    print("=================================================")
    return 0


def build_linux_installer() -> int:
    """Build Linux AppImage using build_appimage.sh."""
    print("=================================================")
    print(" Building Gitory Linux AppImage Installer        ")
    print("=================================================")

    sh_script = ROOT_DIR / "installers" / "linux" / "build_appimage.sh"
    if not sh_script.exists():
        print(f"Error: Linux build script not found at {sh_script}")
        return 1

    # Ensure executable permission
    os.chmod(sh_script, 0o755)
    res = subprocess.run([str(sh_script)], cwd=str(ROOT_DIR))
    return res.returncode


def main() -> int:
    system = platform.system().lower()
    if "win" in system or "nt" in system:
        return build_windows_installer()
    elif "linux" in system:
        return build_linux_installer()
    else:
        print(f"Unsupported operating system for automated installer packaging: {platform.system()}")
        print("Please build directly with PyInstaller on this platform.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
