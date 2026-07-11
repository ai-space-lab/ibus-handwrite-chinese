%global srcname ibus-handwrite-chinese
%global srcver 0.1.0

Name:           ibus-handwrite-chinese
Version:        %{srcver}
Release:        1%{?dist}
Summary:        Chinese handwriting input with macOS-style floating panel

License:        GPLv3
URL:            https://github.com/ai-space-lab/ibus-handwrite-chinese
Source0:        %{srcname}-%{srcver}.tar.gz

BuildArch:      noarch
BuildRequires:  python3

Requires:       python3-evdev
Requires:       python3-gobject
Requires:       python3-numpy
# python3-venv not needed on RPM distros (venv is part of python3-libs)
# Debian-specific python3-venv is handled in the .deb's Depends field
Requires:       ibus
Requires:       wget
Requires:       unzip

%description
A Chinese handwriting input method for Linux with a macOS-style floating
panel, evdev touchpad integration, and PP-OCRv6 ONNX-based recognition.

Features:
- macOS-style dark floating popup with embedded candidates
- evdev touchpad input (works on any touchpad with BTN_TOUCH support)
- Tap-to-select candidates via spatial trackpad mapping
- ESC pause/resume/close state machine
- Delete button and always-visible close button
- Chinese Handwriting (single unified IBus engine)

%prep
%autosetup -n %{srcname}-%{version}

%build
python3 -c "compile(open('src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"
python3 -c "compile(open('src/handwrite_evdev.py').read(), 'evdev', 'exec')"

%install
mkdir -p %{buildroot}/usr/local/bin
mkdir -p %{buildroot}/usr/local/share/ibus-handwrite-chinese/icons
mkdir -p %{buildroot}/usr/share/ibus/component
mkdir -p %{buildroot}/etc/udev/rules.d

install -m 755 src/ibus-engine-handwrite-chinese %{buildroot}/usr/local/share/ibus-handwrite-chinese/
install -m 644 src/handwrite_evdev.py %{buildroot}/usr/local/share/ibus-handwrite-chinese/
install -m 644 xml/handwrite-chinese.xml %{buildroot}/usr/share/ibus/component/
install -m 644 icons/handwrite-chinese.svg %{buildroot}/usr/local/share/ibus-handwrite-chinese/icons/
install -m 755 tools/restore.sh %{buildroot}/usr/local/share/ibus-handwrite-chinese/
install -m 755 tools/diagnose_trackpad.sh %{buildroot}/usr/local/share/ibus-handwrite-chinese/
install -m 644 tools/99-trackpad-handwrite.rules %{buildroot}/etc/udev/rules.d/

%post
SHARE_DIR="/usr/local/share/ibus-handwrite-chinese"
MODEL_DIR="$SHARE_DIR/models"
VENV_DIR="$SHARE_DIR/venv"
WRAPPER="/usr/local/bin/ibus-engine-handwrite-chinese"
CHECKSUMS_FILE="$MODEL_DIR/checksums.sha256"

# --- Helper: verify SHA256 ---
verify_sha256() {
    _file="$1"
    _expected_name="$2"
    [ -f "$CHECKSUMS_FILE" ] || return 0
    _expected_hash=$(awk -v name="$_expected_name" '$2 == name {print $1}' "$CHECKSUMS_FILE" 2>/dev/null)
    [ -n "$_expected_hash" ] || return 0
    _actual_hash=$(sha256sum "$_file" | awk '{print $1}')
    if [ "$_actual_hash" != "$_expected_hash" ]; then
        echo "  ERROR: SHA256 mismatch for $_expected_name" >&2
        echo "    Expected: $_expected_hash" >&2
        echo "    Actual:   $_actual_hash" >&2
        echo "    The downloaded file is corrupted or has been tampered with." >&2
        exit 1
    fi
    echo "  SHA256 OK: $_expected_name"
    return 0
}

# --- Helper: download with fallback ---
download_with_fallback() {
    _url1="$1"
    _url2="$2"
    _output="$3"
    _desc="$4"
    if wget -q --timeout=30 -O "$_output" "$_url1"; then
        return 0
    fi
    echo "  Warning: Primary download failed for $_desc, trying fallback..."
    if wget -q --timeout=60 -O "$_output" "$_url2"; then
        return 0
    fi
    return 1
}

# --- Model download ---
mkdir -p "$MODEL_DIR"

PPOCR_TIER="${IBUS_HANDWRITE_PPOCR_MODEL:-small}"
case "$PPOCR_TIER" in
    tiny|small|medium) ;;
    *)
        echo "Warning: Unknown PP-OCRv6 model tier '$PPOCR_TIER'. Defaulting to small."
        PPOCR_TIER="small"
        ;;
esac

MODEL_FILE="$MODEL_DIR/ppocrv6_${PPOCR_TIER}_rec.onnx"
DICT_FILE="$MODEL_DIR/dict_v6.txt"

if [ ! -f "$MODEL_FILE" ] || [ ! -f "$DICT_FILE" ]; then
    echo "Downloading PP-OCRv6 ($PPOCR_TIER) recognition model..."
    if command -v wget >/dev/null 2>&1; then
        if [ ! -f "$MODEL_FILE" ]; then
            MODEL_URL1="https://huggingface.co/PaddlePaddle/PP-OCRv6_${PPOCR_TIER}_rec_onnx/resolve/main/inference.onnx"
            MODEL_URL2="https://hf-mirror.com/PaddlePaddle/PP-OCRv6_${PPOCR_TIER}_rec_onnx/resolve/main/inference.onnx"
            if download_with_fallback "$MODEL_URL1" "$MODEL_URL2" \
                "$MODEL_DIR/ppocrv6_${PPOCR_TIER}_rec.onnx" "PP-OCRv6 model"; then
                verify_sha256 "$MODEL_DIR/ppocrv6_${PPOCR_TIER}_rec.onnx" \
                    "ppocrv6_${PPOCR_TIER}_rec.onnx" || :
            else
                echo "Warning: Failed to download PP-OCRv6 model (primary and fallback)"
            fi
        fi
        if [ ! -f "$DICT_FILE" ]; then
            DICT_URL1="https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt"
            DICT_URL2="https://cdn.jsdelivr.net/gh/PaddlePaddle/PaddleOCR@main/ppocr/utils/dict/ppocrv6_dict.txt"
            if download_with_fallback "$DICT_URL1" "$DICT_URL2" \
                "$MODEL_DIR/dict_v6.txt" "PP-OCRv6 dictionary"; then
                verify_sha256 "$MODEL_DIR/dict_v6.txt" "dict_v6.txt" || :
            else
                echo "Warning: Failed to download PP-OCRv6 dictionary (primary and fallback)"
            fi
        fi
    else
        echo "Warning: wget not available, cannot download PP-OCRv6 model"
        echo "Manual download: https://huggingface.co/PaddlePaddle/PP-OCRv6_${PPOCR_TIER}_rec_onnx"
    fi
else
    echo "PP-OCRv6 $PPOCR_TIER model already installed"
fi

# --- Python venv with onnxruntime ---
if command -v python3 >/dev/null 2>&1; then
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating Python virtual environment with onnxruntime..."
        if python3 -m venv --system-site-packages "$VENV_DIR"; then
            "$VENV_DIR/bin/pip" install onnxruntime 2>&1 | tail -3 || \
                echo "Warning: onnxruntime install in venv failed"
        else
            echo "Warning: venv creation failed. Will use system Python."
            rm -rf "$VENV_DIR"
        fi
    fi
else
    echo "Warning: python3 not available. Engine will not work."
fi

# --- Wrapper script ---
cat > "$WRAPPER" << 'WRAPPER_EOF'
#!/usr/bin/env bash
set -eu
VENV="/usr/local/share/ibus-handwrite-chinese/venv"
ENGINE_DIR="/usr/local/share/ibus-handwrite-chinese"

# If the 'input' group is not active in this session, re-exec under 'sg input'
if ! groups | grep -q '\binput\b'; then
    sg input -c "exec $0 $*" 2>/dev/null || true
fi

if [ -x "$VENV/bin/python3" ]; then
    exec "$VENV/bin/python3" "$ENGINE_DIR/ibus-engine-handwrite-chinese" "$@"
else
    exec /usr/bin/python3 "$ENGINE_DIR/ibus-engine-handwrite-chinese" "$@"
fi
WRAPPER_EOF
chmod 755 "$WRAPPER"
echo "Engine wrapper installed"

# --- Reload udev rules ---
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true
fi

# --- Post-install message ---
echo ""
echo "  ────────────────────────────────────────────"
echo "  Chinese Handwriting installed!"
echo "  To activate:  ibus restart"
echo "  Then select Chinese Handwriting from your IBus menu."
echo "  ────────────────────────────────────────────"

%preun
rm -f /etc/udev/rules.d/99-trackpad-handwrite.rules
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
fi

%postun
if [ $1 -eq 0 ]; then
    # Real uninstall (not upgrade: $1 >= 1 during upgrade)
    SHARE_DIR="/usr/local/share/ibus-handwrite-chinese"
    MODEL_DIR="$SHARE_DIR/models"

    # Best-effort: restore previous IBus engine
    if command -v ibus >/dev/null 2>&1; then
        CURRENT=$(ibus engine 2>/dev/null || echo "")
        if [ "$CURRENT" = "handwrite-chinese" ]; then
            ibus engine xkb:us::eng 2>/dev/null || true
        fi
    fi

    if [ -d "$MODEL_DIR" ]; then
        echo "Model data preserved at $MODEL_DIR."
        echo "To remove: sudo rm -rf $SHARE_DIR"
    fi
fi

%files
%license LICENSE
%doc README.md README.zh-Hans-汉.md README.zh-Hant-汉.md
/usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese
/usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py
/usr/local/share/ibus-handwrite-chinese/restore.sh
/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh
/usr/local/share/ibus-handwrite-chinese/models/checksums.sha256
/usr/local/share/ibus-handwrite-chinese/icons/handwrite-chinese.svg
/usr/share/ibus/component/handwrite-chinese.xml
/etc/udev/rules.d/99-trackpad-handwrite.rules

%changelog
* Sun Jun 14 2026 ibus-handwrite-chinese developers <dev@ibus-handwrite-chinese.example.com> - 0.1.0-1
- Initial Beta release.
