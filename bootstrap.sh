#!/bin/bash
set -e

echo "=============================================="
echo "  ibus-handwrite-chinese — v0.1.0 Beta"
echo "  ⚠️  Not yet widely tested on real hardware."
echo "  Please report issues at:"
echo "  https://github.com/ai-space-lab/ibus-handwrite-chinese/issues"
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
    apt install -y python3-evdev wget unzip p7zip-full git python3-venv
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
