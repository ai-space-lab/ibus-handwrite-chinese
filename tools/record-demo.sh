#!/usr/bin/env bash
# tools/record-demo.sh — Interactive guide/launcher for recording launch demo assets.
#
# This script does NOT record anything itself. It walks the user (on their
# MacBook Pro) through producing the demo assets referenced by docs/index.md and
# README.md:
#   - docs/assets/demo.gif   (15s, 800x600)
#   - docs/assets/demo.mp4   (30s, 1280x720)
#   - docs/assets/*.png      (4-5 screenshots)
#
# Run it locally. It only prints instructions and waits for you to press ENTER
# between steps so you control the recording timing.
set -euo pipefail

# Resolve repo root from this script's own location (tools/ -> repo root).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS_DIR="$REPO_ROOT/docs/assets"

echo "=== IBus Handwrite Chinese — Demo Asset Recorder ==="
echo ""
echo "This is an interactive guide. It will NOT record anything for you."
echo "Follow each step, then press ENTER when you are ready to continue."
echo "Assets will be saved to: $ASSETS_DIR"
echo ""

# ---- Pre-flight: tool checks ----
echo "--- Checking required tools ---"
if command -v ffmpeg &>/dev/null; then
    echo "  ✓ ffmpeg found ($(ffmpeg -version 2>/dev/null | head -1))"
else
    echo "  ✗ ffmpeg is REQUIRED for MP4 recording and GIF conversion."
    echo "    Install:  macOS: brew install ffmpeg   |   Linux: sudo apt install ffmpeg"
fi

if command -v peek &>/dev/null; then
    echo "  ✓ peek found (recommended for GIF capture on Linux)"
else
    echo "  ⚠ peek not found — you can still make a GIF via ffmpeg MP4→GIF (see Step 2)."
    echo "    Install:  Linux: sudo apt install peek"
fi

if command -v import &>/dev/null; then
    echo "  ✓ ImageMagick 'import' found (used for screenshots on Linux)"
else
    echo "  ⚠ ImageMagick 'import' not found — screenshots on Linux will use 'import'."
    echo "    Install:  macOS: brew install imagemagick   |   Linux: sudo apt install imagemagick"
fi
echo ""

# ---- Create assets directory ----
mkdir -p "$ASSETS_DIR"
echo "  ✓ Ensured assets directory exists: $ASSETS_DIR"
echo ""

# Detect OS for platform-specific command hints.
if [ "$(uname)" = "Darwin" ]; then
    OS="macos"
    echo "  Detected platform: macOS"
else
    OS="linux"
    echo "  Detected platform: Linux"
fi
echo ""

# ---- Step 1: launch the standalone test window ----
echo "=== STEP 1: Launch the standalone test window ==="
echo ""
echo "  Run the engine in --test mode (standalone GTK window, no IBus daemon needed):"
echo ""
echo "    ibus-engine-handwrite-chinese --test"
echo ""
echo "  A dark floating panel appears. Draw a Chinese character on your trackpad"
echo "  (or with the mouse) and confirm candidates appear at the top."
echo ""
read -r -p "  Press ENTER once the window is open and working... "

# ---- Step 2: record the demo GIF ----
echo ""
echo "=== STEP 2: Record the 15s demo GIF (800x600) → docs/assets/demo.gif ==="
echo ""
echo "  Option A (Linux, easiest): use peek"
echo "    - Open peek, set size to 800x600, set format to GIF"
echo "    - Position the window over the handwriting panel"
echo "    - Click record, draw for ~15s, then stop"
echo "    - Save as: $ASSETS_DIR/demo.gif"
echo ""
echo "  Option B (any platform, ffmpeg): record an MP4 first, then convert:"
echo "    - Record 15s MP4 (see Step 3 command, use -t 15 -s 800x600)"
echo "    - Convert to GIF:"
if [ "$OS" = "macos" ]; then
    echo "        ffmpeg -i demo.mp4 -vf \"fps=15,scale=800:-1\" -loop 0 $ASSETS_DIR/demo.gif"
else
    echo "        ffmpeg -i demo.mp4 -vf \"fps=15,scale=800:-1\" -loop 0 $ASSETS_DIR/demo.gif"
fi
echo ""
read -r -p "  Press ENTER after you have saved docs/assets/demo.gif... "

# ---- Step 3: record the demo MP4 ----
echo ""
echo "=== STEP 3: Record the 30s demo MP4 (1280x720) → docs/assets/demo.mp4 ==="
echo ""
echo "  List available capture devices first (optional but recommended):"
if [ "$OS" = "macos" ]; then
    echo "    ffmpeg -f avfoundation -list_devices true -i \"\""
    echo ""
    echo "  Record (macOS, avfoundation — \"1\" is typically the screen device):"
    echo "    ffmpeg -f avfoundation -i \"1\" -t 30 -s 1280x720 \"$ASSETS_DIR/demo.mp4\""
else
    echo "    ffmpeg -f x11grab -list_devices true -i \"\""
    echo ""
    echo "  Record (Linux/X11):"
    echo "    ffmpeg -f x11grab -s 1280x720 -t 30 -i :0.0 \"$ASSETS_DIR/demo.mp4\""
fi
echo ""
echo "  Tip: draw a character, let candidates appear, tap to select, then press ESC."
echo ""
read -r -p "  Press ENTER after you have saved docs/assets/demo.mp4... "

# ---- Step 4: capture screenshots ----
echo ""
echo "=== STEP 4: Capture 4-5 screenshots → docs/assets/ ==="
echo ""
echo "  Save each screenshot with the EXACT filename below:"
echo "    main-panel.png          — the floating handwriting panel with candidates"
echo "    trackpad-drawing.png    — mid-stroke drawing on the trackpad"
echo "    preference-dialog.png   — the 6-tab preference dialog (ibus-engine-handwrite-chinese --setup)"
echo "    model-download.png      — the Model tab / download progress"
echo "    shortcuts-tab.png       — the Shortcuts tab of the preference dialog"
echo "    user-dict.png           — the User Dictionary tab"
echo ""
if [ "$OS" = "macos" ]; then
    echo "  macOS: use 'screencapture -i' for an interactive selection, e.g."
    echo "    screencapture -i $ASSETS_DIR/main-panel.png"
    echo "  (repeat for each filename above)"
else
    echo "  Linux: use ImageMagick 'import' for an interactive selection, e.g."
    echo "    import $ASSETS_DIR/main-panel.png"
    echo "  (repeat for each filename above)"
fi
echo ""
read -r -p "  Press ENTER after you have saved the screenshots... "

# ---- Summary ----
echo ""
echo "=== Done — saved files ==="
echo ""
if [ -d "$ASSETS_DIR" ]; then
    saved=0
    for f in demo.gif demo.mp4 main-panel.png trackpad-drawing.png \
             preference-dialog.png model-download.png shortcuts-tab.png user-dict.png; do
        if [ -f "$ASSETS_DIR/$f" ]; then
            echo "  ✓ $f"
            saved=$((saved + 1))
        else
            echo "  ✗ $f  (missing)"
        fi
    done
    echo ""
    echo "  $saved file(s) present in $ASSETS_DIR"
else
    echo "  (assets directory not found — nothing saved)"
fi
echo ""
echo "Next: tell Atlas \"assets are in\" to deploy + verify."
