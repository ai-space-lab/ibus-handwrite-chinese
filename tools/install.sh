#!/bin/bash
set -euo pipefail

SKIP_DEPS=false
SKIP_RESTART=false
SET_ENGINE=true
for arg in "$@"; do
    [ "$arg" = "--skip-deps" ] && SKIP_DEPS=true
    [ "$arg" = "--no-restart" ] && SKIP_RESTART=true
    [ "$arg" = "--no-set-engine" ] && SET_ENGINE=false
done

# Pre-flight: sudo wrapper — when running as root (e.g. Docker CI), defined as a no-op
if [ "$(id -u)" -eq 0 ]; then
    sudo() { "$@"; }
else
    # sudo must be available and accessible
    if ! command -v sudo &>/dev/null; then
        echo "Error: sudo is required but not installed."
        echo "Install sudo or run the script as root."
        exit 1
    fi
    if ! sudo -n true 2>/dev/null && ! sudo -v 2>/dev/null; then
        echo "Error: You do not have sudo access."
        echo "Ensure your user has sudo privileges or run as root."
        exit 1
    fi
fi

REAL_USER="${SUDO_USER:-${USER:-root}}"

if [ "$SKIP_DEPS" = false ]; then
    if ! command -v apt &>/dev/null; then
        echo "  ⚠ Not a Debian-based system — skipping apt dependency install."
        echo "  Install python3-evdev manually for your distro, then re-run with --skip-deps"
    else
        echo "[1] Installing dependencies..."
        sudo apt-get update || echo "  ⚠ apt update failed, attempting install anyway"
        sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y python3-evdev wget unzip python3-venv || {
            echo "  ⚠ Failed to install system packages. Install manually:"
            echo "     apt install python3-evdev wget unzip python3-venv"
            echo "  Then re-run with: ./tools/install.sh --skip-deps [--no-restart] [--no-set-engine]"
        }
    fi
fi
echo "[PP-OCR] Downloading PP-OCRv6 recognition model..."
PPOCR_TIER="${IBUS_HANDWRITE_PPOCR_MODEL:-small}"
case "$PPOCR_TIER" in
    tiny|small|medium) ;;
    *)
        echo "  ⚠ Warning: Invalid PP-OCR model tier '$PPOCR_TIER'. Valid: tiny, small, medium. Defaulting to small."
        PPOCR_TIER="small"
        ;;
esac
PPOCR_MODEL_DIR="/usr/local/share/ibus-handwrite-chinese/models"
PPOCR_MODEL_FILE="$PPOCR_MODEL_DIR/ppocrv6_${PPOCR_TIER}_rec.onnx"
PPOCR_DICT_FILE="$PPOCR_MODEL_DIR/dict_v6.txt"
if [ -f "$PPOCR_MODEL_FILE" ] && [ -f "$PPOCR_DICT_FILE" ]; then
    echo "  ✓ PP-OCRv6 ${PPOCR_TIER} model already installed"
else
    sudo mkdir -p "$PPOCR_MODEL_DIR"
    tmpdir="$(mktemp -d)"
    ppocr_ok=true
    if [ ! -f "$PPOCR_MODEL_FILE" ]; then
        echo "  Downloading PP-OCRv6 ${PPOCR_TIER} recognition model..."
        if wget -q --timeout=30 -O "$tmpdir/inference.onnx" \
            "https://huggingface.co/PaddlePaddle/PP-OCRv6_${PPOCR_TIER}_rec_onnx/resolve/main/inference.onnx"; then
            sudo cp "$tmpdir/inference.onnx" "$PPOCR_MODEL_FILE"
            echo "  ✓ PP-OCRv6 ${PPOCR_TIER} model downloaded"
        else
            echo "  ⚠ Warning: Failed to download PP-OCRv6 ${PPOCR_TIER} model"
            ppocr_ok=false
        fi
    fi
    if [ ! -f "$PPOCR_DICT_FILE" ]; then
        echo "  Downloading PP-OCRv6 dictionary..."
        if wget -q --timeout=30 -O "$tmpdir/dict.txt" \
            "https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt"; then
            sudo cp "$tmpdir/dict.txt" "$PPOCR_DICT_FILE"
            echo "  ✓ PP-OCRv6 dictionary downloaded"
        else
            echo "  ⚠ Warning: Failed to download PP-OCRv6 dictionary"
            ppocr_ok=false
        fi
    fi
    rm -rf "$tmpdir"
    if [ "$ppocr_ok" = true ]; then
        echo "  ✓ PP-OCRv6 ${PPOCR_TIER} model installed"
    fi
fi

echo "=== Installing Chinese Handwriting IBus Engine ==="
echo ""

echo "[2] Installing engine files..."
sudo cp src/handwrite_evdev.py /usr/local/bin/
sudo chmod 644 /usr/local/bin/handwrite_evdev.py

# Create Python venv with onnxruntime (system GTK/evdev/IBus via --system-site-packages)
VENV_DIR="/usr/local/share/ibus-handwrite-chinese/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating Python virtual environment with onnxruntime..."
    sudo python3 -m venv --system-site-packages "$VENV_DIR" || {
        echo "  ⚠ Failed to create venv. Will use system Python directly (may lack onnxruntime)."
        VENV_DIR=""
    }
fi
if [ -n "$VENV_DIR" ]; then
    echo "  Installing onnxruntime..."
    sudo "$VENV_DIR/bin/pip" install onnxruntime 2>&1 | tail -5 || {
        echo "  ⚠ Failed to install onnxruntime in venv. Will use system Python directly."
        VENV_DIR=""
    }
fi

# Install wrapper script as the engine binary
# (points to venv Python if available, else directly runs the source)
sudo tee /usr/local/bin/ibus-engine-handwrite-chinese > /dev/null << 'WRAPPER'
#!/usr/bin/env bash
set -eu
VENV="/usr/local/share/ibus-handwrite-chinese/venv"
ENGINE_DIR="/usr/local/share/ibus-handwrite-chinese"

# If the 'input' group is not active in this session, re-exec under 'sg input'
if ! groups | grep -q '\binput\b'; then
    exec sg input -c "exec $0 $*" 2>/dev/null || true
fi

if [ -x "$VENV/bin/python3" ]; then
    exec "$VENV/bin/python3" "$ENGINE_DIR/ibus-engine-handwrite-chinese" "$@"
else
    exec /usr/bin/python3 "$ENGINE_DIR/ibus-engine-handwrite-chinese" "$@"
fi
WRAPPER
sudo chmod 755 /usr/local/bin/ibus-engine-handwrite-chinese

# Install main engine script (not executable directly, but run via wrapper)
sudo cp src/ibus-engine-handwrite-chinese /usr/local/share/ibus-handwrite-chinese/
sudo chmod 644 /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese

# Symlink handwrite_evdev.py into engine dir (so import handwrite_evdev finds it)
sudo ln -sf /usr/local/bin/handwrite_evdev.py /usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py

sudo cp tools/diagnose_trackpad.sh /usr/local/share/ibus-handwrite-chinese/ 2>/dev/null || true
sudo chmod 755 /usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh

echo "[3] Registering IBus component..."
sudo mkdir -p /usr/share/ibus/component
sudo cp xml/handwrite-chinese.xml /usr/share/ibus/component/

echo "[4] Installing udev rule for trackpad access..."
sudo mkdir -p /etc/udev/rules.d
sudo cp tools/99-trackpad-handwrite.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules 2>/dev/null || true
sudo udevadm trigger 2>/dev/null || true

echo "[5] Adding user '$REAL_USER' to input group for evdev access..."
sudo usermod -a -G input "$REAL_USER" || echo "  ⚠ Could not add user to input group"
# Detect if udev ACL gave immediate access (systemd-logind)
if command -v getfacl &>/dev/null; then
    if getfacl /dev/input/event* 2>/dev/null | grep -q "user:$USER"; then
        echo "  ✓ udev ACL active (immediate trackpad access)"
    else
        echo "  ⚠ udev ACL not applied (non-systemd?). sg fallback in wrapper script."
    fi
fi
echo "  NOTE: You must LOG OUT and BACK IN for group change to take effect."
echo "  Or run: newgrp input  (applies to current shell only)"

echo "[6] Installing restore script..."
sudo mkdir -p /usr/local/share/ibus-handwrite-chinese
sudo cp tools/restore.sh /usr/local/share/ibus-handwrite-chinese/
sudo chmod 755 /usr/local/share/ibus-handwrite-chinese/restore.sh

echo "【7】 Installing icons..."
sudo mkdir -p /usr/local/share/ibus-handwrite-chinese/icons
sudo cp icons/handwrite-chinese.svg /usr/local/share/ibus-handwrite-chinese/icons/

echo "【7.5】 Ensuring IBus is installed..."
if ! command -v ibus &>/dev/null; then
    echo "  Installing IBus..."
    if command -v apt &>/dev/null; then
        sudo apt-get install -y ibus ibus-gtk3 || echo "  ⚠ Failed to install ibus via apt"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y ibus || echo "  ⚠ Failed to install ibus via dnf"
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm ibus || echo "  ⚠ Failed to install ibus via pacman"
    elif command -v zypper &>/dev/null; then
        sudo zypper install -y ibus || echo "  ⚠ Failed to install ibus via zypper"
    fi
else
    echo "  ✓ IBus already installed"
fi

echo "【8】 Killing stale root ibus-daemon..."
if pgrep -x ibus-daemon >/dev/null 2>&1 && pgrep -u root ibus-daemon >/dev/null 2>&1; then
    sudo pkill -u root ibus-daemon 2>/dev/null || true
    sleep 1
    echo "  ✓ Stale root ibus-daemon killed"
else
    echo "  ✓ No stale root ibus-daemon found"
fi
# Post-kill: warn if root daemon survived
if pgrep -u root ibus-daemon > /dev/null 2>&1; then
    echo "  ⚠ WARNING: Could not kill root ibus-daemon. ESC may not work."
    echo "    Manual: sudo pkill -9 -u root ibus-daemon"
fi

echo "【9】 Restarting IBus..."
DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}"
export DBUS_SESSION_BUS_ADDRESS
if [ "$SKIP_RESTART" = true ]; then
    echo "  Skipping IBus restart (--no-restart flag)"
    SET_ENGINE=false
elif [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "  No display detected — IBus will be available after next login"
    SET_ENGINE=false
elif [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
    echo "  No D-Bus session — IBus restart skipped (will be available after next login)"
    SET_ENGINE=false
else
    echo "  Restarting IBus daemon..."
    { if [ "$(id -u)" -eq 0 ] && [ "$REAL_USER" != "root" ]; then
        su -c "ibus-daemon --daemonize --replace 2>/dev/null || true" "$REAL_USER"
      else
        ibus-daemon --daemonize --replace 2>/dev/null || true
      fi; } || true
    # Poll for ibus-daemon readiness before activating engine
    for _ in 1 2 3 4 5; do
        timeout 1 ibus engine >/dev/null 2>&1 && break
        sleep 1
    done
    sleep 1
    pgrep -u "$REAL_USER" ibus-daemon >/dev/null 2>&1 \
        && echo "  ✓ User ibus-daemon confirmed running" \
        || echo "  ⚠ User ibus-daemon not confirmed — run: ibus-daemon --daemonize --replace"
fi

echo ""
echo "=== Install complete ==="

if [ "$SET_ENGINE" = true ]; then
    echo "  Activating Chinese Handwriting IME..."
    # Run as the real user so ibus connects to the user's D-Bus session
    if [ "$(id -u)" -eq 0 ] && [ "$REAL_USER" != "root" ]; then
        SWITCH_CMD="su -c 'ibus engine handwrite-chinese' \"$REAL_USER\""
    else
        SWITCH_CMD="ibus engine handwrite-chinese"
    fi
    if timeout 3s bash -c "$SWITCH_CMD" 2>/dev/null; then
        echo "  ✓ Chinese Handwriting set as engine (verify in IBus menu)"
    else
        echo "  ! Could not switch engine. Try manually:"
        echo "    ibus engine handwrite-chinese"
    fi
else
    echo "Switch to the engine:"
    echo "  ibus engine handwrite-chinese"
fi
echo "Or select 'Chinese Handwriting' from your IBus menu."
echo ""
echo "To uninstall: /usr/local/share/ibus-handwrite-chinese/restore.sh"
echo ""
echo "⚠ IMPORTANT: You must LOG OUT and BACK IN for input group access to take effect."
echo "  Otherwise the engine cannot read the trackpad device."
