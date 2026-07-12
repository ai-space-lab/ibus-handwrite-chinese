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

REAL_USER="${SUDO_USER:-${USER:-root}}"

echo "=== Uninstalling Chinese Handwriting IBus Engine ==="
echo ""

echo "[1] Removing engine files..."
sudo rm -f /usr/local/bin/ibus-engine-handwrite-chinese
sudo rm -f /usr/local/bin/handwrite_evdev.py
sudo rm -f /usr/share/ibus/component/handwrite-chinese.xml
sudo rm -f /etc/udev/rules.d/99-trackpad-handwrite.rules
sudo rm -rf /usr/local/share/ibus-handwrite-chinese

# Clean up user-local config and data (prompt to avoid data loss)
if [ -d "$HOME/.config/ibus-handwrite-chinese" ] || [ -d "$HOME/.local/share/ibus-handwrite-chinese" ]; then
    echo ""
    echo "  User data detected:"
    [ -d "$HOME/.config/ibus-handwrite-chinese" ] && \
        echo "    - $HOME/.config/ibus-handwrite-chinese/  (settings/config)"
    [ -d "$HOME/.local/share/ibus-handwrite-chinese" ] && \
        echo "    - $HOME/.local/share/ibus-handwrite-chinese/  (user dictionary)"
    echo "  Remove user data? [y/N] "
    read -r _confirm 2>/dev/null || _confirm=""
    if [ "$_confirm" = "y" ] || [ "$_confirm" = "Y" ]; then
        rm -rf "$HOME/.config/ibus-handwrite-chinese" 2>/dev/null && \
            echo "  OK User config removed"
        rm -rf "$HOME/.local/share/ibus-handwrite-chinese" 2>/dev/null && \
            echo "  OK User dictionary removed"
    else
        echo "  - User data preserved"
    fi
fi

echo "[2] Reloading udev..."
sudo udevadm control --reload-rules 2>/dev/null || true

echo "[3] Restarting IBus..."
# Run ibus commands as the original user (not root), so they connect
# to the user's D-Bus session bus instead of auto-launching a root one.
sudo -u "$REAL_USER" ibus restart 2>/dev/null || \
  sudo -u "$REAL_USER" ibus-daemon --replace --daemonize 2>/dev/null || true

echo ""
echo "=== Uninstall complete ==="
