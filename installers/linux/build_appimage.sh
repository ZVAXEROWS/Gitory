#!/usr/bin/env bash
# build_appimage.sh — Automated script to compile Gitory into a Linux .AppImage
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
INSTALLERS_DIR="$DIST_DIR/installers"
APP_DIR="$DIST_DIR/Gitory.AppDir"

echo "================================================="
echo " Building Gitory Linux AppImage"
echo "================================================="

# Step 1: Ensure executable binaries are compiled with PyInstaller
echo "-> Step 1: Compiling Gitory binary with PyInstaller..."
cd "$PROJECT_ROOT"

PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
fi

"$PYTHON_CMD" -m PyInstaller \
    --name=Gitory \
    --windowed \
    --onedir \
    --clean \
    --noconfirm \
    --add-data="src/gitory/themes/*.qss:gitory/themes" \
    --paths=src \
    "src/gitory/__main__.py"

# Step 2: Assemble AppDir structure
echo "-> Step 2: Assembling AppDir directory structure..."
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin" "$APP_DIR/usr/share/applications" "$APP_DIR/usr/share/icons/hicolor/256x256/apps" "$INSTALLERS_DIR"

# Copy PyInstaller bundle into usr/bin/Gitory
cp -a "$DIST_DIR/Gitory/." "$APP_DIR/usr/bin/"

# Copy desktop entry
cp "$SCRIPT_DIR/gitory.desktop" "$APP_DIR/usr/share/applications/gitory.desktop"
cp "$SCRIPT_DIR/gitory.desktop" "$APP_DIR/gitory.desktop"

# Generate a high-quality SVG vector Git graph logo for the AppDir icon
cat <<EOF > "$APP_DIR/gitory.svg"
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" rx="64" fill="#7aa2f7"/>
  <circle cx="128" cy="80" r="24" fill="#1f2335"/>
  <circle cx="80" cy="176" r="24" fill="#1f2335"/>
  <circle cx="176" cy="176" r="24" fill="#1f2335"/>
  <line x1="128" y1="80" x2="80" y2="176" stroke="#1f2335" stroke-width="14" stroke-linecap="round"/>
  <line x1="128" y1="80" x2="176" y2="176" stroke="#1f2335" stroke-width="14" stroke-linecap="round"/>
</svg>
EOF
cp "$APP_DIR/gitory.svg" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/gitory.svg"
ln -s "gitory.svg" "$APP_DIR/.DirIcon" || true

# Create AppRun launcher script
cat <<'EOF' > "$APP_DIR/AppRun"
#!/usr/bin/env bash
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$SELF_DIR/usr/bin:$PATH"
exec "$SELF_DIR/usr/bin/Gitory" "$@"
EOF
chmod +x "$APP_DIR/AppRun"
chmod -R a+rx "$APP_DIR/usr/bin"

# Step 3: Download appimagetool and generate AppImage
echo "-> Step 3: Generating Gitory-1.0.0-x86_64.AppImage using appimagetool..."
APPIMAGETOOL="$DIST_DIR/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading static appimagetool..."
    curl -L -o "$APPIMAGETOOL" "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

ARCH=x86_64 "$APPIMAGETOOL" "$APP_DIR" "$INSTALLERS_DIR/Gitory-1.0.0-x86_64.AppImage"

echo "================================================="
echo " AppImage build successful!"
echo " Output: $INSTALLERS_DIR/Gitory-1.0.0-x86_64.AppImage"
echo "================================================="
