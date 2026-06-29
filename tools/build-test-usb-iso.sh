#!/usr/bin/env bash
# ============================================================================
# Build custom Linux Mint 22 live ISO with ibus-handwrite-chinese pre-installed
# ============================================================================
# Usage:
#   sudo bash tools/build-test-usb-iso.sh                    # auto-download Mint ISO
#   sudo bash tools/build-test-usb-iso.sh /path/to/linuxmint.iso  # use local ISO
#
# Output:
#   ./ibus-handwrite-chinese-test-v0.3.0.iso
#
# Requirements:
#   - root (for chroot, mounting)
#   - ~10GB free temp space
#   - internet connection (first run: downloads Mint ISO + engine + model)
#
# Flash to USB:
#   sudo dd if=ibus-handwrite-chinese-test-v0.3.0.iso of=/dev/sdX bs=4M status=progress conv=fsync
# ============================================================================
set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORK_DIR="/tmp/ibus-handwrite-usb-build-$$"
EXTRACT_CD="$WORK_DIR/extract-cd"      # extracted ISO contents
EDIT_DIR="$WORK_DIR/edit"              # unsquashed root filesystem
ISO_MOUNT="$WORK_DIR/iso_mount"        # where we mount the original ISO

OUTPUT_ISO="$(pwd)/ibus-handwrite-chinese-test-v0.3.0.iso"
ENGINE_VERSION="v0.3.0"
ENGINE_TARBALL="https://github.com/ai-space-lab/ibus-handwrite-chinese/archive/refs/tags/v0.3.0.tar.gz"
PPOCR_MODEL_URL="https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/main/inference.onnx"
PPOCR_DICT_URL="https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt"

# Mint 22 (Wilma) Cinnamon ISO - default download URL
DEFAULT_ISO_URL="https://mirrors.kernel.org/linuxmint/isos/stable/22/linuxmint-22-cinnamon-64bit.iso"
DEFAULT_ISO_FILENAME="linuxmint-22-cinnamon-64bit.iso"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Cleanup handler ────────────────────────────────────────────────────────
cleanup() {
    local ec=$?
    info "Cleaning up..."
    # Unmount chroot binds
    if mountpoint -q "$EDIT_DIR/proc" 2>/dev/null; then umount -lf "$EDIT_DIR/proc" 2>/dev/null || true; fi
    if mountpoint -q "$EDIT_DIR/sys"  2>/dev/null; then umount -lf "$EDIT_DIR/sys"  2>/dev/null || true; fi
    if mountpoint -q "$EDIT_DIR/dev"  2>/dev/null; then umount -lf "$EDIT_DIR/dev"  2>/dev/null || true; fi
    # Unmount ISO
    if mountpoint -q "$ISO_MOUNT" 2>/dev/null; then umount -lf "$ISO_MOUNT" 2>/dev/null || true; fi
    # Remove temp dir
    rm -rf "$WORK_DIR" 2>/dev/null || true
    if [ $ec -eq 0 ]; then
        ok "Build complete. Output: $OUTPUT_ISO"
    else
        err "Build failed at step $CURRENT_STEP. See errors above."
    fi
    exit $ec
}
trap cleanup EXIT

# ── Step tracking ──────────────────────────────────────────────────────────
CURRENT_STEP=""
step() {
    CURRENT_STEP="$1"
    echo ""
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Step: $*${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
}

# ── Pre-flight checks ─────────────────────────────────────────────────────
preflight() {
    step "Pre-flight checks"

    if [ "$EUID" -ne 0 ]; then
        err "This script must be run as root (for chroot + mounting)."
        echo "  pkexec bash $0 $*"
        exit 1
    fi

    local tools=("wget" "7z" "squashfs-tools" "xorriso" "isolinux")
    local missing=()
    for t in "${tools[@]}"; do
        if ! command -v "$t" &>/dev/null && ! dpkg -s "$t" &>/dev/null 2>&1; then
            missing+=("$t")
        fi
    done

    # On Ubuntu/Mint, individual tool check
    for cmd in wget 7z unsquashfs xorriso; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    # Check isohdpfx.bin for isolinux
    if [ ! -f /usr/lib/ISOLINUX/isohdpfx.bin ] && [ ! -f /usr/share/syslinux/isohdpfx.bin ]; then
        missing+=("isolinux (isohdpfx.bin)")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        info "Installing missing build dependencies..."
        apt-get update -qq
        apt-get install -y -qq squashfs-tools xorriso isolinux p7zip-full wget
        ok "Dependencies installed"
    else
        ok "All build tools found"
    fi

    # Check available space in /tmp
    local avail
    avail=$(df --output=avail /tmp 2>/dev/null | tail -1)
    if [ "$avail" -lt 10485760 ]; then  # 10GB in KB
        warn "Only $((avail / 1024))MB free in /tmp. Need ~10GB. Consider setting TMPDIR."
    fi
}

# ── Resolve ISO file ───────────────────────────────────────────────────────
resolve_iso() {
    step "Resolve Linux Mint ISO"

    local iso_path=""
    if [ $# -ge 1 ] && [ -f "$1" ]; then
        iso_path="$1"
        info "Using provided ISO: $iso_path"
    else
        local download_dir="$WORK_DIR/download"
        mkdir -p "$download_dir"
        iso_path="$download_dir/$DEFAULT_ISO_FILENAME"
        if [ -f "$iso_path" ]; then
            info "Using cached ISO: $iso_path"
        else
            info "Downloading Linux Mint 22 Cinnamon ISO..."
            info "  URL: $DEFAULT_ISO_URL"
            echo ""
            wget -O "$iso_path" "$DEFAULT_ISO_URL"
            ok "ISO downloaded: $iso_path"
        fi
    fi

    ISO_FILE="$iso_path"
}

# ── Extract ISO ────────────────────────────────────────────────────────────
extract_iso() {
    step "Extract ISO contents"

    mkdir -p "$ISO_MOUNT" "$EXTRACT_CD"

    info "Mounting ISO..."
    mount -o loop,ro "$ISO_FILE" "$ISO_MOUNT"

    info "Copying ISO contents to working directory (this may take a minute)..."
    rsync -a --exclude='casper/filesystem.squashfs' "$ISO_MOUNT/" "$EXTRACT_CD/"
    # Copy squashfs separately so we can track it
    cp -a "$ISO_MOUNT/casper/filesystem.squashfs" "$EXTRACT_CD/casper/filesystem.squashfs"

    umount "$ISO_MOUNT"

    # Verify
    if [ ! -f "$EXTRACT_CD/casper/filesystem.squashfs" ]; then
        err "filesystem.squashfs not found in ISO. Is this a valid Linux Mint ISO?"
        exit 1
    fi
    ok "ISO extracted to $EXTRACT_CD"
}

# ── Unsquash filesystem ────────────────────────────────────────────────────
unsquash_fs() {
    step "Unsquash root filesystem"

    mkdir -p "$EDIT_DIR"

    info "Unsquashing (may take a few minutes)..."
    unsquashfs -d "$EDIT_DIR" -f "$EXTRACT_CD/casper/filesystem.squashfs"

    local file_count
    file_count=$(find "$EDIT_DIR" -maxdepth 1 -type d | wc -l)
    if [ "$file_count" -lt 5 ]; then
        err "Unsquashfs produced too few directories — something went wrong."
        exit 1
    fi
    ok "Root filesystem unsquashed to $EDIT_DIR"
}

# ── Chroot customization ───────────────────────────────────────────────────
customize_chroot() {
    step "Customize live filesystem (chroot)"

    # Bind mount system directories
    mount --bind /dev "$EDIT_DIR/dev"
    mount --bind /proc "$EDIT_DIR/proc"
    mount --bind /sys "$EDIT_DIR/sys"
    # Ensure /dev/pts is available for apt
    mkdir -p "$EDIT_DIR/dev/pts"
    mount --bind /dev/pts "$EDIT_DIR/dev/pts"

    # Network access inside chroot
    cp -L /etc/resolv.conf "$EDIT_DIR/etc/resolv.conf" 2>/dev/null || true

    # ── Prepare the customization script ──
    # This runs INSIDE the chroot
    cat > "$EDIT_DIR/tmp/customize.sh" << 'CHROOT_SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

# Make dpkg non-interactive
export DEBIAN_FRONTEND=noninteractive
export HOME=/root

echo "  [chroot] Updating package lists..."
apt-get update -qq

echo "  [chroot] Installing handwriting engine dependencies..."
apt-get install -y -qq \
    python3-evdev \
    python3-gi \
    python3-gi-cairo \
    python3-numpy \
    python3-pip \
    ibus \
    ibus-gtk3 \
    wget \
    unzip \
    libgirepository1.0-dev \
    gobject-introspection

echo "  [chroot] Installing ONNX Runtime..."
pip3 install onnxruntime --break-system-packages

echo "  [chroot] Downloading handwriting engine v0.3.0..."
cd /tmp
wget -q https://github.com/ai-space-lab/ibus-handwrite-chinese/archive/refs/tags/v0.3.0.tar.gz
tar -xzf v0.3.0.tar.gz
cd ibus-handwrite-chinese-0.3.0

echo "  [chroot] Installing handwriting engine..."
bash tools/install.sh --skip-deps --no-restart

echo "  [chroot] Pre-downloading PP-OCRv6 ONNX model..."
mkdir -p /usr/local/share/ibus-handwrite-chinese/models
wget -q --timeout=120 -O /usr/local/share/ibus-handwrite-chinese/models/ppocrv6_small_rec.onnx \
    https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/main/inference.onnx || \
    echo "  [chroot] WARNING: ONNX model download failed (will be downloaded at runtime)"

wget -q --timeout=120 -O /usr/local/share/ibus-handwrite-chinese/models/dict_v6.txt \
    https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt || \
    echo "  [chroot] WARNING: Dict download failed (will be downloaded at runtime)"

echo "  [chroot] Model files:"
ls -la /usr/local/share/ibus-handwrite-chinese/models/ 2>/dev/null || echo "    (empty)"

# ── Clean up chroot ──
echo "  [chroot] Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
rm -f /etc/resolv.conf
rm -f /var/lib/dbus/machine-id
rm -f /sbin/initctl
dpkg-divert --rename --remove /sbin/initctl 2>/dev/null || true

echo "  [chroot] Customization complete."
CHROOT_SCRIPT

    chmod +x "$EDIT_DIR/tmp/customize.sh"

    info "Running chroot customization (downloading packages + model, ~5-15 min)..."
    chroot "$EDIT_DIR" /tmp/customize.sh

    # Clean up the customization script from chroot
    rm -f "$EDIT_DIR/tmp/customize.sh"

    ok "Chroot customization complete"
}

# ── Repack squashfs ────────────────────────────────────────────────────────
repack_squashfs() {
    step "Repack compressed filesystem"

    # Remove old squashfs
    rm -f "$EXTRACT_CD/casper/filesystem.squashfs"

    info "Creating new filesystem.squashfs (xz compression, ~5 min)..."
    mksquashfs "$EDIT_DIR" "$EXTRACT_CD/casper/filesystem.squashfs" \
        -comp xz -noappend -always-use-fragments

    # Check result
    local sq_size
    sq_size=$(stat -c%s "$EXTRACT_CD/casper/filesystem.squashfs" 2>/dev/null || echo 0)
    if [ "$sq_size" -lt 104857600 ]; then  # less than 100MB is suspicious
        warn "New squashfs is only $((sq_size / 1048576))MB — might be too small."
    else
        ok "New squashfs: $((sq_size / 1048576))MB"
    fi

    # Update filesystem.size (needed by installer)
    info "Updating filesystem.size..."
    local fs_size
    fs_size=$(du -sx --block-size=1 "$EDIT_DIR" | cut -f1)
    echo "$fs_size" > "$EXTRACT_CD/casper/filesystem.size"

    # Update filesystem.manifest if present
    if [ -f "$EXTRACT_CD/casper/filesystem.manifest" ]; then
        info "Updating filesystem.manifest..."
        chroot "$EDIT_DIR" dpkg-query -W --showformat='${Package} ${Version}\n' \
            > "$EXTRACT_CD/casper/filesystem.manifest" 2>/dev/null || true
        # Also create manifest-desktop if it exists
        if [ -f "$EXTRACT_CD/casper/filesystem.manifest-desktop" ]; then
            cp "$EXTRACT_CD/casper/filesystem.manifest" \
               "$EXTRACT_CD/casper/filesystem.manifest-desktop"
        fi
    fi

    ok "Filesystem repacked"
}

# ── Rebuild ISO ────────────────────────────────────────────────────────────
rebuild_iso() {
    step "Rebuild bootable ISO"

    # Determine isohdpfx.bin path
    local mbr_bin=""
    if [ -f /usr/lib/ISOLINUX/isohdpfx.bin ]; then
        mbr_bin="/usr/lib/ISOLINUX/isohdpfx.bin"
    elif [ -f /usr/share/syslinux/isohdpfx.bin ]; then
        mbr_bin="/usr/share/syslinux/isohdpfx.bin"
    else
        err "isohdpfx.bin not found. Install isolinux package."
        exit 1
    fi

    # Go to the extracted ISO root
    cd "$EXTRACT_CD"

    # Regenerate md5sum.txt
    info "Regenerating md5sums..."
    rm -f md5sum.txt
    find . -type f -not -path './isolinux/boot.cat' -not -path './md5sum.txt' \
        -exec md5sum {} + > md5sum.txt 2>/dev/null

    # Determine volume label from original ISO or use default
    local vol_label
    vol_label=$(blkid -s LABEL -o value "$ISO_FILE" 2>/dev/null || echo "Linux Mint 22 Cinnamon")

    info "Building ISO with xorriso..."
    xorriso -as mkisofs \
        -r -V "$vol_label" \
        -J -l \
        -b isolinux/isolinux.bin \
        -c isolinux/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -eltorito-alt-boot -e boot/grub/efi.img \
        -no-emul-boot -isohybrid-gpt-basdat \
        -isohybrid-mbr "$mbr_bin" \
        -o "$OUTPUT_ISO" \
        . 2>&1 | grep -v "^xorriso :" || true

    cd "$PROJECT_ROOT"

    # Verify output
    if [ ! -f "$OUTPUT_ISO" ]; then
        err "ISO creation failed — output file not found."
        ls -la "$(dirname "$OUTPUT_ISO")" || true
        exit 1
    fi

    local iso_size
    iso_size=$(stat -c%s "$OUTPUT_ISO" 2>/dev/null || echo 0)
    ok "ISO built: $OUTPUT_ISO ($((iso_size / 1048576))MB)"
}

# ── Verify ─────────────────────────────────────────────────────────────────
verify_iso() {
    step "Verify output ISO"

    if [ ! -f "$OUTPUT_ISO" ]; then
        err "Output ISO not found at $OUTPUT_ISO"
        exit 1
    fi

    local iso_size
    iso_size=$(stat -c%s "$OUTPUT_ISO" 2>/dev/null || echo 0)
    local iso_size_mb=$((iso_size / 1048576))

    info "ISO size: ${iso_size_mb}MB"

    if [ "$iso_size_mb" -lt 2000 ]; then
        warn "ISO is under 2GB — this might be too small for a complete Mint ISO"
    fi

    # Quick sanity check: verify it has an MBR
    if dd if="$OUTPUT_ISO" bs=512 count=1 2>/dev/null | file - | grep -qi "dos/mbr\|x86 boot" ; then
        ok "ISO is bootable (MBR present)"
    else
        warn "Could not verify MBR — might not be bootable on BIOS"
    fi

    # Check for EFI partition
    if fdisk -l "$OUTPUT_ISO" 2>/dev/null | grep -qi "EFI\|GPT"; then
        ok "ISO has EFI boot support"
    fi

    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ISO ready!${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  File: $OUTPUT_ISO"
    echo "  Size: ${iso_size_mb}MB"
    echo ""
    echo "  Write to USB:"
    echo "    sudo dd if=$OUTPUT_ISO of=/dev/sdX bs=4M status=progress conv=fsync"
    echo ""
    echo "  Features pre-installed:"
    echo "    - ibus-handwrite-chinese engine (v0.3.0)"
    echo "    - PP-OCRv6 ONNX recognition model (small)"
    echo "    - python3-evdev, GTK3, IBus, ONNX Runtime"
    echo ""
    echo "  After boot:"
    echo "    ibus engine handwrite-chinese"
    echo "    # Start drawing on the trackpad"
    echo ""
}

# ── Main ───────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  Custom Linux Mint 22 ISO with ibus-handwrite-chinese   ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    preflight "$@"
    resolve_iso "$@"
    extract_iso
    unsquash_fs
    customize_chroot
    repack_squashfs
    rebuild_iso
    verify_iso
}

main "$@"
