#!/bin/bash
set -e

# Pre-flight: sudo must be available and accessible
if ! command -v sudo &>/dev/null; then
    echo "Error: sudo is required but not installed."
    exit 1
fi
if ! sudo -n true 2>/dev/null && ! sudo -v 2>/dev/null; then
    echo "Error: You do not have sudo access."
    exit 1
fi

echo "=============================================="
echo "  ibus-handwrite-chinese — v0.1.0 Beta"
echo "  ⚠️  Not yet widely tested on real hardware."
echo "  Please report issues at:"
echo "  https://github.com/ai-space-lab/ibus-handwrite-chinese/issues"
echo "=============================================="
echo ""

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
    sudo apt update
    sudo apt install -y python3-evdev wget unzip p7zip-full git python3-venv
}

install_fedora() {
    sudo dnf install -y python3-evdev wget unzip p7zip git
}

install_arch() {
    sudo pacman -S --noconfirm python-evdev wget unzip p7zip
}

install_suse() {
    sudo zypper --no-gpg-checks refresh 2>/dev/null || true
    sudo zypper install -y python3-evdev wget unzip p7zip || {
        echo "⚠ zypper install failed (transient repo timeout). Retrying with --no-gpg-checks..."
        sudo zypper --no-gpg-checks install -y python3-evdev wget unzip p7zip || true
    }
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

if [ -f "./tools/install.sh" ]; then
    SRC_DIR="$(pwd)"
else
    echo "Cloning repository..."
    SRC_DIR="$(mktemp -d)"
    git clone --depth 1 https://github.com/ai-space-lab/ibus-handwrite-chinese.git "$SRC_DIR"
fi

cd "$SRC_DIR"
exec ./tools/install.sh --skip-deps
