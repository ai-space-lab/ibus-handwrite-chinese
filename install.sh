#!/bin/bash
set -e

SKIP_DEPS=false
for arg in "$@"; do
    [ "$arg" = "--skip-deps" ] && SKIP_DEPS=true
done

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
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
    DEBIAN_FRONTEND=noninteractive apt install -y python3-evdev tegaki-zinnia-simplified-chinese wget unzip
    if ! DEBIAN_FRONTEND=noninteractive apt install -y tegaki-zinnia-traditional-chinese 2>/dev/null; then
        echo "  tegaki-zinnia-traditional-chinese not in apt (not available in this Debian release)"
        echo "  Downloading traditional model from GitHub..."
        tmpdir="$(mktemp -d)"
        prev_dir="$(pwd)"
        cd "$tmpdir"
        wget -q https://github.com/tegaki/tegaki/releases/download/v0.3/tegaki-zinnia-traditional-chinese-0.3.zip
        unzip -q tegaki-zinnia-traditional-chinese-0.3.zip
        mkdir -p /usr/share/tegaki/models/zinnia
        cp tegaki-zinnia-traditional-chinese-0.3/*.model /usr/share/tegaki/models/zinnia/
        cp tegaki-zinnia-traditional-chinese-0.3/*.meta /usr/share/tegaki/models/zinnia/
        cd "$prev_dir"
        rm -rf "$tmpdir"
        echo "  ✓ Traditional model installed from GitHub"
    fi
    echo "  Installing improved model (幽兰百合 Community) for Simplified Chinese..."
    DEBIAN_FRONTEND=noninteractive apt install -y p7zip 2>/dev/null || true
    tmpdir="$(mktemp -d)"
    prev_dir="$(pwd)"
    cd "$tmpdir"
    wget -q -O model.7z 'https://gitee.com/LZQingXi/handwriting-zh_CN_Community/releases/download/1.1.0/handwriting-zh_CN-%E7%A4%BE%E5%8C%BA%E7%89%88_V1.1.0.7z'
    7z x -y model.7z >/dev/null 2>&1
    mkdir -p /usr/local/share/ibus-handwrite-chinese/models
    cp ZJHandWriting-zh_CN.model /usr/local/share/ibus-handwrite-chinese/models/
    cd "$prev_dir"
    rm -rf "$tmpdir"
    echo "  ✓ 幽兰百合 model installed"
fi

echo "=== Installing Chinese Handwriting IBus Engine ==="
echo ""

echo "[2] Installing engine to /usr/local/bin..."
cp ibus-engine-handwrite-chinese /usr/local/bin/
chmod 755 /usr/local/bin/ibus-engine-handwrite-chinese
cp handwrite_evdev.py /usr/local/bin/
chmod 644 /usr/local/bin/handwrite_evdev.py

echo "[3] Registering IBus component..."
mkdir -p /usr/share/ibus/component
cp handwrite-chinese-simplified.xml handwrite-chinese-traditional.xml /usr/share/ibus/component/

echo "[4] Installing udev rule for touchpad access..."
mkdir -p /etc/udev/rules.d
cp 99-trackpad-handwrite.rules /etc/udev/rules.d/
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true

echo "[5] Installing restore script..."
mkdir -p /usr/local/share/ibus-handwrite-chinese
cp restore.sh /usr/local/share/ibus-handwrite-chinese/
chmod 755 /usr/local/share/ibus-handwrite-chinese/restore.sh

echo "【6】 Installing icons..."
mkdir -p /usr/local/share/ibus-handwrite-chinese/icons
cp handwrite-chinese-simplified.svg handwrite-chinese-traditional.svg /usr/local/share/ibus-handwrite-chinese/icons/

echo "【7】 Restarting IBus..."
ibus restart 2>/dev/null || ibus-daemon --replace --daemonize 2>/dev/null || true

echo ""
echo "=== Install complete ==="
echo "Switch to the engine:"
echo "  ibus engine handwrite-chinese-simplified   (Simplified)"
echo "  ibus engine handwrite-chinese-traditional  (Traditional)"
echo "Or select 'Chinese Handwriting (Simplified)' or 'Chinese Handwriting (Traditional)' from your IBus menu."
echo ""
echo "To uninstall: sudo /usr/local/share/ibus-handwrite-chinese/restore.sh"
