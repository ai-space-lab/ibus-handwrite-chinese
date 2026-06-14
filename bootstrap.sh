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
    echo "  1. Install python3-evdev and libzinnia (0.06+) for your distro"
    echo "  2. Download tegaki models: https://github.com/tegaki/tegaki/releases"
    echo "     and 幽兰百合 model: https://gitee.com/LZQingXi/handwriting-zh_CN_Community"
    echo "  3. Place .model files in /usr/share/tegaki/models/zinnia/"
    echo "     and /usr/local/share/ibus-handwrite-chinese/models/"
    echo "  4. Clone repo and run: sudo ./install.sh --skip-deps"
    exit 1
fi

echo "=== ibus-handwrite-chinese — Installing dependencies ==="
echo "Detected: $DISTRO ($DISTRO_FAMILY)"
echo ""

download_model() {
    local lang="$1"
    local model_dir="/usr/share/tegaki/models/zinnia"
    local model_file="$model_dir/handwriting-$lang.model"

    if [ -f "$model_file" ]; then
        echo "  ✓ $lang model already installed"
        return 0
    fi

    local zip_name="tegaki-zinnia-simplified-chinese-0.3.zip"
    [ "$lang" = "zh_TW" ] && zip_name="tegaki-zinnia-traditional-chinese-0.3.zip"

    local zip_url="https://github.com/tegaki/tegaki/releases/download/v0.3/$zip_name"

    echo "  Downloading $lang model..."
    local tmpdir prev_dir
    tmpdir="$(mktemp -d)"
    prev_dir="$(pwd)"
    cd "$tmpdir"
    if ! wget -q "$zip_url"; then
        echo "  ✗ Failed to download $lang model from GitHub."
        echo "    Manual download: https://github.com/tegaki/tegaki/releases/tag/v0.3"
        echo "    Place .model and .meta files in $model_dir"
        echo "    (zh_CN is used as fallback for the primary 幽兰百合 model)"
        cd "$prev_dir"
        rm -rf "$tmpdir"
        exit 1
    fi
    unzip -q "$zip_name"
    local extracted_dir="${zip_name%.zip}"
    mkdir -p "$model_dir"
    cp "$extracted_dir"/*.model "$model_dir/"
    cp "$extracted_dir"/*.meta "$model_dir/"
    cd "$prev_dir"
    rm -rf "$tmpdir"
    echo "  ✓ $lang model installed"
}

install_debian() {
    apt update
    apt install -y python3-evdev libzinnia0 tegaki-zinnia-simplified-chinese wget unzip p7zip-full git
    if ! apt install -y tegaki-zinnia-traditional-chinese 2>/dev/null; then
        echo "  tegaki-zinnia-traditional-chinese not in apt (not available in this Debian release)"
        echo "  Downloading traditional model from GitHub..."
        download_model "zh_TW"
    fi
}

install_fedora() {
    dnf install -y python3-evdev zinnia zinnia-devel wget unzip p7zip git
    download_model "zh_CN"
    download_model "zh_TW"
}

install_arch() {
    pacman -S --noconfirm python-evdev wget unzip p7zip
    if ! python3 -c "import ctypes; ctypes.CDLL('libzinnia.so')" 2>/dev/null && \
       ! python3 -c "import ctypes; ctypes.CDLL('libzinnia.so.0')" 2>/dev/null; then
        echo ""
        echo "zinnia library not found. Install it from AUR first:"
        echo "  yay -S zinnia"
        echo "  # or: paru -S zinnia"
        echo ""
        echo "Then re-run bootstrap.sh"
        exit 1
    fi
    echo "  ✓ zinnia library found"
    download_model "zh_CN"
    download_model "zh_TW"
}

install_suse() {
    zypper install -y python3-evdev zinnia zinnia-devel wget unzip p7zip
    download_model "zh_CN"
    download_model "zh_TW"
}

case "$DISTRO_FAMILY" in
    debian) install_debian ;;
    fedora) install_fedora ;;
    arch)   install_arch ;;
    suse)   install_suse ;;
esac

echo ""
echo "  Installing improved 幽兰百合 model for Simplified Chinese..."
LILY_MODEL="/usr/local/share/ibus-handwrite-chinese/models/ZJHandWriting-zh_CN.model"
if [ -f "$LILY_MODEL" ]; then
    echo "  ✓ 幽兰百合 model already installed"
else
    tmpdir="$(mktemp -d)"
    prev_dir="$(pwd)"
    cd "$tmpdir"
    LILY_URL="https://gitee.com/LZQingXi/handwriting-zh_CN_Community/releases/download/1.1.0/handwriting-zh_CN-%E7%A4%BE%E5%8C%BA%E7%89%88_V1.1.0.7z"
    echo "  Downloading from Gitee..."
    download_failed=false
    if ! wget -q --max-redirect=5 -O model.7z "$LILY_URL"; then
        CACHE_FILE="$prev_dir/models/handwriting-zh_CN-community.7z"
        if [ -f "$CACHE_FILE" ]; then
            echo "  Gitee failed, using local cache: models/handwriting-zh_CN-community.7z"
            cp "$CACHE_FILE" model.7z
        else
            echo "  ⚠ Warning: Failed to download 幽兰百合 model from Gitee (no local cache)."
            echo "    Manual download: https://gitee.com/LZQingXi/handwriting-zh_CN_Community"
            echo "    Place ZJHandWriting-zh_CN.model in /usr/local/share/ibus-handwrite-chinese/models/"
            download_failed=true
        fi
    fi
    if [ "$download_failed" != true ]; then
        echo "  Extracting..."
        7z x -y model.7z >/dev/null 2>&1
        mkdir -p /usr/local/share/ibus-handwrite-chinese/models
        cp ZJHandWriting-zh_CN.model "$LILY_MODEL"
        echo "  ✓ 幽兰百合 model installed (9374 characters)"
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
