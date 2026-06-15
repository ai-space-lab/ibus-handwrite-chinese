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

LILY_URL="https://gitee.com/LZQingXi/handwriting-zh_CN_Community/releases/download/1.1.0/handwriting-zh_CN-%E7%A4%BE%E5%8C%BA%E7%89%88_V1.1.0.7z"
LILY_CACHE_FILE="models/handwriting-zh_CN-community.7z"
LILY_BACKUP_URL="${IBUS_HANDWRITE_MODEL_BACKUP_URL:-}"
LILY_BACKUP_FILE="${IBUS_HANDWRITE_MODEL_BACKUP_FILE:-}"

install_lily_model() {
    tmpdir="$(mktemp -d)"
    prev_dir="$(pwd)"
    model_file=""

    if wget -q --max-redirect=5 -O "$tmpdir/model.7z" "$LILY_URL"; then
        model_file="$tmpdir/model.7z"
        echo "  Downloaded 幽兰百合 model from Gitee"
    elif [ -f "$prev_dir/$LILY_CACHE_FILE" ]; then
        model_file="$prev_dir/$LILY_CACHE_FILE"
        echo "  Gitee failed, using local cache: $LILY_CACHE_FILE"
    elif [ -n "$LILY_BACKUP_URL" ]; then
        echo "  Gitee failed, downloading backup model from IBUS_HANDWRITE_MODEL_BACKUP_URL..."
        if ! wget -q --max-redirect=5 -O "$tmpdir/backup-model" "$LILY_BACKUP_URL"; then
            echo "  ⚠ Warning: Failed to download backup model."
            rm -rf "$tmpdir"
            return 1
        fi
        model_file="$tmpdir/backup-model"
    elif [ -n "$LILY_BACKUP_FILE" ] && [ -f "$LILY_BACKUP_FILE" ]; then
        model_file="$LILY_BACKUP_FILE"
        echo "  Gitee failed, using backup model: $LILY_BACKUP_FILE"
    else
        echo "  ⚠ Warning: Failed to download 幽兰百合 model from Gitee."
        echo "    No local cache or backup model configured."
        echo "    Manual download: https://gitee.com/LZQingXi/handwriting-zh_CN_Community"
        echo "    Optional fallback: set IBUS_HANDWRITE_MODEL_BACKUP_URL or IBUS_HANDWRITE_MODEL_BACKUP_FILE."
        rm -rf "$tmpdir"
        return 1
    fi

    mkdir -p /usr/local/share/ibus-handwrite-chinese/models
    case "$model_file" in
        *.model)
            cp "$model_file" /usr/local/share/ibus-handwrite-chinese/models/ZJHandWriting-zh_CN.model
            ;;
        *)
            if ! 7z x -y "$model_file" -o"$tmpdir/extracted" >/dev/null 2>&1; then
                echo "  ⚠ Warning: Failed to extract backup model archive."
                rm -rf "$tmpdir"
                return 1
            fi
            if [ ! -f "$tmpdir/extracted/ZJHandWriting-zh_CN.model" ]; then
                echo "  ⚠ Warning: Backup archive does not contain ZJHandWriting-zh_CN.model."
                rm -rf "$tmpdir"
                return 1
            fi
            cp "$tmpdir/extracted/ZJHandWriting-zh_CN.model" /usr/local/share/ibus-handwrite-chinese/models/ZJHandWriting-zh_CN.model
            ;;
    esac

    rm -rf "$tmpdir"
    echo "  ✓ 幽兰百合 model installed"
}

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
    DEBIAN_FRONTEND=noninteractive apt install -y p7zip-full 2>/dev/null || true
fi
if ! install_lily_model; then
    echo "  No 幽兰百合 model installed"
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
cp xml/handwrite-chinese-simplified.xml xml/handwrite-chinese-traditional.xml /usr/share/ibus/component/

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
cp icons/handwrite-chinese-simplified.svg icons/handwrite-chinese-traditional.svg /usr/local/share/ibus-handwrite-chinese/icons/

echo "【7】 Restarting IBus..."
if [ "$SKIP_RESTART" = true ]; then
    echo "  Skipping IBus restart"
else
    timeout 5s ibus restart 2>/dev/null || timeout 5s ibus-daemon --replace --daemonize 2>/dev/null || true
fi

echo ""
echo "=== Install complete ==="
echo "Switch to the engine:"
echo "  ibus engine handwrite-chinese-simplified   (Simplified)"
echo "  ibus engine handwrite-chinese-traditional  (Traditional)"
echo "Or select 'Chinese Handwriting (Simplified)' or 'Chinese Handwriting (Traditional)' from your IBus menu."
echo ""
echo "To uninstall: sudo /usr/local/share/ibus-handwrite-chinese/restore.sh"
