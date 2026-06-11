#!/bin/bash
set -e

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
    echo "  2. Download models: https://github.com/tegaki/tegaki/releases"
    echo "  3. Place .model and .meta files in /usr/share/tegaki/models/zinnia/"
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
    local tmpdir
    tmpdir="$(mktemp -d)"
    cd "$tmpdir"
    if ! wget -q "$zip_url"; then
        echo "  ✗ Failed to download $lang model from GitHub."
        echo "    Manual download: https://github.com/tegaki/tegaki/releases/tag/v0.3"
        echo "    Place .model and .meta files in $model_dir"
        exit 1
    fi
    unzip -q "$zip_name"
    local extracted_dir="${zip_name%.zip}"
    mkdir -p "$model_dir"
    cp "$extracted_dir"/*.model "$model_dir/"
    cp "$extracted_dir"/*.meta "$model_dir/"
    cd /
    rm -rf "$tmpdir"
    echo "  ✓ $lang model installed"
}

install_debian() {
    apt update
    apt install -y python3-evdev tegaki-zinnia-simplified-chinese tegaki-zinnia-traditional-chinese
}

install_fedora() {
    dnf install -y python3-evdev zinnia zinnia-devel wget unzip
    download_model "zh_CN"
    download_model "zh_TW"
}

install_arch() {
    pacman -S --noconfirm python-evdev wget unzip
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
    zypper install -y python3-evdev zinnia zinnia-devel wget unzip
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
echo "=== Dependencies installed. Running install.sh... ==="
echo ""

if [ -f "./install.sh" ]; then
    SRC_DIR="$(pwd)"
else
    echo "Cloning repository..."
    SRC_DIR="$(mktemp -d)"
    git clone --depth 1 https://github.com/vinceyap88/ibus-handwrite-chinese.git "$SRC_DIR"
fi

cd "$SRC_DIR"
exec ./install.sh --skip-deps
