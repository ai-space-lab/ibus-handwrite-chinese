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
Requires:       python3-venv
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
install -m 644 tools/99-trackpad-handwrite.rules %{buildroot}/etc/udev/rules.d/

%post
SHARE_DIR="/usr/local/share/ibus-handwrite-chinese"
MODEL_DIR="$SHARE_DIR/models"
VENV_DIR="$SHARE_DIR/venv"
WRAPPER="/usr/local/bin/ibus-engine-handwrite-chinese"

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
            wget -q --timeout=60 -O "$MODEL_DIR/ppocrv6_${PPOCR_TIER}_rec.onnx" \
                "https://huggingface.co/PaddlePaddle/PP-OCRv6_${PPOCR_TIER}_rec_onnx/resolve/main/inference.onnx" \
                && echo "PP-OCRv6 model downloaded" \
                || echo "Warning: PP-OCRv6 model download failed"
        fi
        if [ ! -f "$DICT_FILE" ]; then
            wget -q --timeout=60 -O "$MODEL_DIR/dict_v6.txt" \
                "https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt" \
                && echo "PP-OCRv6 dictionary downloaded" \
                || echo "Warning: PP-OCRv6 dictionary download failed"
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

%preun
rm -f /etc/udev/rules.d/99-trackpad-handwrite.rules
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
fi

%files
%license LICENSE
%doc README.md README.zh-Hans-汉.md README.zh-Hant-漢.md
/usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese
/usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py
/usr/local/share/ibus-handwrite-chinese/restore.sh
/usr/local/share/ibus-handwrite-chinese/icons/handwrite-chinese.svg
/usr/share/ibus/component/handwrite-chinese.xml
/etc/udev/rules.d/99-trackpad-handwrite.rules

%changelog
* Sun Jun 14 2026 ibus-handwrite-chinese developers <dev@ibus-handwrite-chinese.example.com> - 0.1.0-1
- Initial Beta release.
