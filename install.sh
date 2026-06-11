#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
    exit 1
fi

if ! command -v apt &>/dev/null; then
    echo "This script requires apt (Debian/Ubuntu/Mint)"
    exit 1
fi

echo "=== Installing Chinese Handwriting IBus Engine ==="
echo ""

echo "[1] Installing dependencies..."
apt update
DEBIAN_FRONTEND=noninteractive apt install -y python3-evdev tegaki-zinnia-simplified-chinese

echo "[2] Installing engine to /usr/local/bin..."
cp ibus-engine-handwrite-chinese /usr/local/bin/
chmod 755 /usr/local/bin/ibus-engine-handwrite-chinese
cp handwrite_evdev.py /usr/local/bin/
chmod 644 /usr/local/bin/handwrite_evdev.py

echo "[3] Registering IBus component..."
mkdir -p /usr/share/ibus/component
cp handwrite-chinese.xml /usr/share/ibus/component/

echo "[4] Installing udev rule for touchpad access..."
cp 99-trackpad-handwrite.rules /etc/udev/rules.d/
udevadm control --reload-rules
udevadm trigger

echo "[5] Installing restore script..."
mkdir -p /usr/local/share/ibus-handwrite-chinese
cp restore.sh /usr/local/share/ibus-handwrite-chinese/
chmod 755 /usr/local/share/ibus-handwrite-chinese/restore.sh

echo "[6] Restarting IBus..."
ibus restart 2>/dev/null || ibus-daemon --replace --daemonize 2>/dev/null || true

echo ""
echo "=== Install complete ==="
echo "Switch to the engine: ibus engine handwrite-chinese"
echo "Or select 'Chinese Handwriting' from your IBus menu."
echo ""
echo "To uninstall: sudo /usr/local/share/ibus-handwrite-chinese/restore.sh"
