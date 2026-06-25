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
    apt update
    DEBIAN_FRONTEND=noninteractive apt install -y python3-evdev wget unzip
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
cp src/ibus-engine-handwrite-chinese /usr/local/bin/
chmod 755 /usr/local/bin/ibus-engine-handwrite-chinese
cp src/handwrite_evdev.py /usr/local/bin/
chmod 644 /usr/local/bin/handwrite_evdev.py

echo "[3] Registering IBus component..."
mkdir -p /usr/share/ibus/component
cp xml/handwrite-chinese.xml /usr/share/ibus/component/

echo "[4] Installing udev rule for touchpad access..."
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
