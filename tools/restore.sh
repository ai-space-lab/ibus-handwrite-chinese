#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo /usr/local/share/ibus-handwrite-chinese/restore.sh"
    exit 1
fi

echo "=== Uninstalling Chinese Handwriting IBus Engine ==="
echo ""

echo "[1] Removing engine files..."
rm -f /usr/local/bin/ibus-engine-handwrite-chinese
rm -f /usr/local/bin/handwrite_evdev.py
rm -f /usr/share/ibus/component/handwrite-chinese.xml
rm -f /etc/udev/rules.d/99-trackpad-handwrite.rules
rm -rf /usr/local/share/ibus-handwrite-chinese

echo "[2] Reloading udev..."
udevadm control --reload-rules 2>/dev/null || true

echo "[3] Restarting IBus..."
ibus restart 2>/dev/null || ibus-daemon --replace --daemonize 2>/dev/null || true

echo ""
echo "=== Uninstall complete ==="
