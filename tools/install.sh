#!/bin/bash
set -e

SKIP_DEPS=false
SKIP_RESTART=false
for arg in "$@"; do
    [ "$arg" = "--skip-deps" ] && SKIP_DEPS=true
    [ "$arg" = "--no-restart" ] && SKIP_RESTART=true
done

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./tools/install.sh"
    exit 1
fi

if [ "$SKIP_DEPS" = false ]; then
    if ! command -v apt &>/dev/null; then
        echo "This script requires apt (Debian/Ubuntu/Mint)"
        echo "For other distros, use bootstrap.sh (see README)"
        exit 1
    fi
    echo "[1] Installing dependencies..."
    apt-get update || echo "  ⚠ apt update failed, attempting install anyway"
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3-evdev wget unzip || {
        echo "  ⚠ Failed to install system packages. Install manually:"
        echo "     sudo apt install python3-evdev wget unzip"
        echo "  Then re-run with: sudo ./tools/install.sh --skip-deps"
    }
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
    mkdir -p "$PPOCR_MODEL_DIR"
    tmpdir="$(mktemp -d)"
    ppocr_ok=true
    if [ ! -f "$PPOCR_MODEL_FILE" ]; then
        echo "  Downloading PP-OCRv6 ${PPOCR_TIER} recognition model..."
        if wget -q --timeout=30 -O "$tmpdir/inference.onnx" \
            "https://huggingface.co/PaddlePaddle/PP-OCRv6_${PPOCR_TIER}_rec_onnx/resolve/main/inference.onnx"; then
            cp "$tmpdir/inference.onnx" "$PPOCR_MODEL_FILE"
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
            cp "$tmpdir/dict.txt" "$PPOCR_DICT_FILE"
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

echo "[2] Installing engine to /usr/local/bin..."
cp src/handwrite_evdev.py /usr/local/bin/
chmod 644 /usr/local/bin/handwrite_evdev.py

# Create Python venv with onnxruntime (system GTK/evdev/IBus via --system-site-packages)
VENV_DIR="/usr/local/share/ibus-handwrite-chinese/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating Python virtual environment with onnxruntime..."
    python3 -m venv --system-site-packages "$VENV_DIR" || {
        echo "  ⚠ Failed to create venv. Will use system Python directly (may lack onnxruntime)."
        VENV_DIR=""
    }
fi
if [ -n "$VENV_DIR" ]; then
    echo "  Installing onnxruntime..."
    "$VENV_DIR/bin/pip" install onnxruntime 2>&1 | tail -5 || {
        echo "  ⚠ Failed to install onnxruntime in venv. Will use system Python directly."
        VENV_DIR=""
    }
fi

# Install wrapper script as the engine binary
# (points to venv Python if available, else directly runs the source)
cat > /usr/local/bin/ibus-engine-handwrite-chinese << 'WRAPPER'
#!/usr/bin/env bash
set -eu
VENV="/usr/local/share/ibus-handwrite-chinese/venv"
ENGINE_DIR="/usr/local/share/ibus-handwrite-chinese"
if [ -x "$VENV/bin/python3" ]; then
    exec "$VENV/bin/python3" "$ENGINE_DIR/ibus-engine-handwrite-chinese" "$@"
else
    exec /usr/bin/python3 "$ENGINE_DIR/ibus-engine-handwrite-chinese" "$@"
fi
WRAPPER
chmod 755 /usr/local/bin/ibus-engine-handwrite-chinese

# Install main engine script (not executable directly, but run via wrapper)
cp src/ibus-engine-handwrite-chinese /usr/local/share/ibus-handwrite-chinese/
chmod 644 /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese

echo "[3] Registering IBus component..."
mkdir -p /usr/share/ibus/component
cp xml/handwrite-chinese.xml /usr/share/ibus/component/

echo "[4] Installing udev rule for trackpad access..."
mkdir -p /etc/udev/rules.d
cp tools/99-trackpad-handwrite.rules /etc/udev/rules.d/
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true

echo "[5] Installing restore script..."
mkdir -p /usr/local/share/ibus-handwrite-chinese
cp tools/restore.sh /usr/local/share/ibus-handwrite-chinese/
chmod 755 /usr/local/share/ibus-handwrite-chinese/restore.sh

echo "【6】 Installing icons..."
mkdir -p /usr/local/share/ibus-handwrite-chinese/icons
cp icons/handwrite-chinese.svg /usr/local/share/ibus-handwrite-chinese/icons/

echo "【7】 Restarting IBus..."
if [ "$SKIP_RESTART" = true ]; then
    echo "  Skipping IBus restart"
else
    timeout 5s ibus restart 2>/dev/null || timeout 5s ibus-daemon --replace --daemonize 2>/dev/null || true
fi

echo ""
echo "=== Install complete ==="
echo "Switch to the engine:"
echo "  ibus engine handwrite-chinese"
echo "Or select 'Chinese Handwriting' from your IBus menu."
echo ""
echo "To uninstall: sudo /usr/local/share/ibus-handwrite-chinese/restore.sh"
