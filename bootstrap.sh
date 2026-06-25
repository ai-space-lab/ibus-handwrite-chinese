#!/bin/bash
set -e

echo "=============================================="
echo "  ibus-handwrite-chinese — v0.1.0 Beta"
echo "  ⚠️  Not yet widely tested on real hardware."
echo "  Please report issues at:"
echo "  https://github.com/vinceyap88/ibus-handwrite-chinese/issues"
echo "=============================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./bootstrap.sh"
    exit 1
fi

# --- Distro detection ---
DISTRO=""
DISTRO_FAMILY=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$ID"
    case "$ID" in
        debian|ubuntu|linuxmint|pop|elementary|zorin|kali|neon|deepin)
            DISTRO_FAMILY="debian" ;;
        fedora|rhel|centos|almalinux|rocky)
            DISTRO_FAMILY="fedora" ;;
        arch|manjaro|endeavouros|garuda|artix|arcolinux)
            DISTRO_FAMILY="arch" ;;
        opensuse*|suse|sles)
            DISTRO_FAMILY="suse" ;;
    esac
fi

if [ -z "$DISTRO_FAMILY" ]; then
    echo "Unsupported distribution${DISTRO:+: $DISTRO}"
    echo ""
    echo "Manual install:"
    echo "  1. Install python3-evdev for your distro"
    echo "  2. Clone repo and run: sudo ./install.sh --skip-deps"
    echo "  3. The ONNX recognition model (PP-OCRv6) will be downloaded automatically"
    exit 1
fi

echo "=== ibus-handwrite-chinese — Installing dependencies ==="
echo "Detected: $DISTRO ($DISTRO_FAMILY)"
echo ""

install_debian() {
    apt update
    apt install -y python3-evdev wget unzip p7zip-full git
}

install_fedora() {
    dnf install -y python3-evdev wget unzip p7zip git
}

install_arch() {
    pacman -S --noconfirm python-evdev wget unzip p7zip
}

install_suse() {
    zypper install -y python3-evdev wget unzip p7zip
}

case "$DISTRO_FAMILY" in
    debian) install_debian ;;
    fedora) install_fedora ;;
    arch)   install_arch ;;
    suse)   install_suse ;;
esac

echo ""
echo "  Downloading PP-OCRv6 model for text recognition..."
PPOCR_TIER="${IBUS_HANDWRITE_PPOCR_MODEL:-small}"
case "$PPOCR_TIER" in
    tiny|small|medium) ;;
    *)
        echo "  ⚠ Warning: Unknown PP-OCRv6 model tier '$PPOCR_TIER'. Valid: tiny, small, medium. Defaulting to 'small'."
        PPOCR_TIER="small"
        ;;
esac

PPOCR_DIR="/usr/local/share/ibus-handwrite-chinese/models"
PPOCR_MODEL="$PPOCR_DIR/ppocrv6_${PPOCR_TIER}_rec.onnx"
PPOCR_DICT="$PPOCR_DIR/dict_v6.txt"

if [ -f "$PPOCR_MODEL" ] && [ -f "$PPOCR_DICT" ]; then
    echo "  ✓ PP-OCRv6 ($PPOCR_TIER) model already installed"
else
    tmpdir="$(mktemp -d)"
    prev_dir="$(pwd)"
    cd "$tmpdir"

    MODEL_URL="https://huggingface.co/PaddlePaddle/PP-OCRv6_${PPOCR_TIER}_rec_onnx/resolve/main/inference.onnx"
    DICT_URL="https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt"

    echo "  Downloading PP-OCRv6 ($PPOCR_TIER) ONNX model from HuggingFace..."
    download_ok=true

    if ! wget -q --timeout=30 "$MODEL_URL" -O inference.onnx; then
        echo "  ⚠ Warning: Failed to download PP-OCRv6 model from HuggingFace."
        echo "    Manual download: $MODEL_URL"
        echo "    Place the file in $PPOCR_DIR"
        download_ok=false
    fi

    if ! wget -q --timeout=30 "$DICT_URL" -O dict.txt; then
        echo "  ⚠ Warning: Failed to download PP-OCRv6 dict from PaddleOCR GitHub."
        echo "    Manual download: $DICT_URL"
        echo "    Place the file in $PPOCR_DIR"
        download_ok=false
    fi

    if [ "$download_ok" = true ]; then
        mkdir -p "$PPOCR_DIR"
        cp inference.onnx "$PPOCR_MODEL"
        cp dict.txt "$PPOCR_DICT"
        echo "  ✓ PP-OCRv6 ($PPOCR_TIER) model installed"
    fi

    cd "$prev_dir"
    rm -rf "$tmpdir"
fi

echo ""
echo "=== Dependencies installed. Running install.sh... ==="
echo ""

if [ -f "./tools/install.sh" ]; then
    SRC_DIR="$(pwd)"
else
    echo "Cloning repository..."
    SRC_DIR="$(mktemp -d)"
    git clone --depth 1 https://github.com/vinceyap88/ibus-handwrite-chinese.git "$SRC_DIR"
fi

cd "$SRC_DIR"
exec ./tools/install.sh --skip-deps
