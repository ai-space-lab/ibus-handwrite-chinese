%global srcname ibus-handwrite-chinese
%global srcver 0.1.0

Name:           ibus-handwrite-chinese
Version:        %{srcver}
Release:        1%{?dist}
Summary:        Chinese handwriting input with macOS-style floating panel

License:        GPLv3
URL:            https://github.com/vinceyap88/ibus-handwrite-chinese
Source0:        %{srcname}-%{srcver}.tar.gz

BuildArch:      noarch
BuildRequires:  python3

Requires:       python3-evdev
Requires:       python3-gobject
Requires:       python3-numpy
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

install -m 755 src/ibus-engine-handwrite-chinese %{buildroot}/usr/local/bin/
install -m 644 src/handwrite_evdev.py %{buildroot}/usr/local/bin/
install -m 644 xml/handwrite-chinese.xml %{buildroot}/usr/share/ibus/component/
install -m 644 icons/handwrite-chinese.svg %{buildroot}/usr/local/share/ibus-handwrite-chinese/icons/
install -m 755 tools/restore.sh %{buildroot}/usr/local/share/ibus-handwrite-chinese/
install -m 644 tools/99-trackpad-handwrite.rules %{buildroot}/etc/udev/rules.d/

%post
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
/usr/local/bin/ibus-engine-handwrite-chinese
/usr/local/bin/handwrite_evdev.py
/usr/share/ibus/component/handwrite-chinese.xml
/usr/local/share/ibus-handwrite-chinese/icons/handwrite-chinese.svg
/usr/local/share/ibus-handwrite-chinese/restore.sh
/etc/udev/rules.d/99-trackpad-handwrite.rules

%changelog
* Sun Jun 14 2026 ibus-handwrite-chinese developers <dev@ibus-handwrite-chinese.example.com> - 0.1.0-1
- Initial Beta release.
