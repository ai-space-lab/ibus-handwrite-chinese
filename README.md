# IBus Chinese Handwriting Input Method

[![CI](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/ci.yml/badge.svg)](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/ci.yml)
[![v0.1.0 Release Test](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/test-release-v0.1.0.yml/badge.svg)](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/test-release-v0.1.0.yml)
[![Build Packages](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/build-packages.yml/badge.svg)](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/build-packages.yml)

**English** · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

A Chinese handwriting input method for Linux with a macOS-style floating panel, evdev touchpad integration, and Zinnia-based recognition.

![screenshot](docs/screenshot.png)

## Features

- **macOS-style popup**: dark floating window with embedded candidates at the top
- **evdev touchpad input**: draw characters on your laptop's touchpad — works on any touchpad with BTN_TOUCH + ABS_X/ABS_MT_POSITION_X support (all modern Synaptics, ELAN, ALPS, and bcm5974 touchpads)
- **Tap to select**: quickly tap on the touchpad to pick a candidate — spatial mapping matches candidate position
- **Two-finger swipe**: swipe left/right with two fingers to page through candidates
- **Delete stroke**: ⌫ button to undo the last stroke
- **Close button**: × button always visible at top-left, closes and restores previous input method
- **ESC state machine**: one ESC pauses (ungrab touchpad, show "Paused" overlay), another ESC closes and restores the previous input method; click the window to resume
- **Cursor-proximity positioning**: popup appears near the text cursor, not at a fixed screen position
- **Drag handle**: custom drag handle in the top bar to reposition the window
- **Mouse fallback**: if no evdev touchpad is available, draw with the mouse

## Cross-Distro Support

`bootstrap.sh` auto-detects your Linux distribution and installs everything:

| Distro | Method | Models |
|--------|--------|--------|
| Debian 12+, Ubuntu 22.04+, Mint 21+ | `apt` + Gitee download | System packages + 幽兰百合 from Gitee (fallback: GitHub download) |
| Fedora 39+ | `dnf` + GitHub/Gitee download | tegaki + 幽兰百合 models downloaded |
| Arch Linux, Manjaro | `pacman` + `yay` (AUR) + download | tegaki + 幽兰百合 models downloaded |
| openSUSE Tumbleweed | `zypper` + download | tegaki + 幽兰百合 models downloaded |

The installer fetches tegaki v0.3 models (`zh_CN.model` — 6763 chars, `zh_TW.model` — 11853 chars) from [tegaki GitHub releases](https://github.com/tegaki/tegaki-models/releases), and the **幽兰百合 Community v1.1.0** model (`ZJHandWriting-zh_CN.model` — 9374 chars) from [Gitee](https://gitee.com/LZQingXi/handwriting-zh_CN_Community). For Simplified Chinese, 幽兰百合 is the primary recognizer with tegaki zh_CN as fallback.

## Requirements

- Linux with a touchpad (or touchscreen)
- IBus input method framework (default on most desktops)
- **Debian family**: Debian 11+, Ubuntu 22.04+, Linux Mint 21+
- **Fedora**: Fedora 40+
- **Arch**: Arch Linux, Manjaro (zinnia from AUR)
- **openSUSE**: Tumbleweed (zinnia not available on Leap)

## Quick Install

```bash
bash <(curl -s https://raw.githubusercontent.com/vinceyap88/ibus-handwrite-chinese/main/bootstrap.sh)
ibus restart
```

**Debian/Ubuntu/Mint** users can also use the traditional method:

```bash
sudo apt install python3-evdev tegaki-zinnia-simplified-chinese tegaki-zinnia-traditional-chinese
git clone https://github.com/vinceyap88/ibus-handwrite-chinese
cd ibus-handwrite-chinese
sudo ./install.sh          # add --skip-deps if you already installed dependencies
ibus restart
```

`install.sh` automatically downloads missing models: tegaki traditional from GitHub and the 幽兰百合 Community v1.1.0 model (9374 chars) from Gitee for improved Simplified Chinese accuracy.

Then switch the engine:

```bash
ibus engine handwrite-chinese-simplified   # Simplified Chinese
ibus engine handwrite-chinese-traditional  # Traditional Chinese
```

Or select **Chinese Handwriting (Simplified)** or **Chinese Handwriting (Traditional)** from your desktop's IBus menu.

## Packages

Pre-built packages are available on the [GitHub Release](https://github.com/vinceyap88/ibus-handwrite-chinese/releases) page:

| Format | Command | Distros |
|--------|---------|---------|
| `.deb` | `sudo dpkg -i <file> && sudo apt install -f` | Debian 11+, Ubuntu 22.04+, Mint 21+ |
| `.rpm` | `sudo rpm -i <file>` | Fedora 40+, openSUSE Tumbleweed |
| `PKGBUILD` | Reference in `packaging/PKGBUILD` | Arch Linux (submit to AUR manually) |

Packages are built automatically by CI on tag push. Post-install downloads tegaki models from GitHub and 幽兰百合 from Gitee (best-effort, non-fatal if Gitee is unreachable).

## Usage

1. Switch to **Chinese Handwriting (Simplified)** or **Chinese Handwriting (Traditional)** from your IBus menu
2. A dark floating panel appears near your text cursor
3. Draw Chinese characters on your laptop's touchpad with one finger
4. Candidate characters appear at the top of the panel
5. Tap on the touchpad to select a candidate (spatial mapping)
6. Use two-finger swipe left/right to page through candidates
7. Press **⌫** to undo the last stroke
8. Click **×** at top-left to close and restore previous input method, or press **ESC** once to pause
9. **ESC** again closes and restores previous input method
10. Click the window to resume after pausing

## Troubleshooting

- **Touchpad not accessible**: Run `sudo udevadm trigger` to apply the udev rule, or add your user to the `input` group: `sudo usermod -a -G input $USER && reboot`
- **IBus not seeing the engine**: Run `ibus restart` after installation
- **Engine won't start**: Check `journalctl -f` while switching to the engine for error messages
- **Permission denied**: Verify with `getfacl /dev/input/event*` — your user should have `rw` access on the touchpad device

## Testing

Two CI workflows run on every push:

### Main CI

[Main CI](.github/workflows/ci.yml) runs across 5 Docker containers:
- **lint**: shellcheck, xmllint, Python syntax checks
- **test-install**: installs dependencies per distro, verifies `libzinnia.so` loads, checks Python syntax
- **test-bootstrap**: full bootstrap.sh end-to-end run, verifies installed files and model placement, runs recognition smoke test

Containers tested: `debian:bookworm`, `ubuntu:24.04`, `fedora:latest`, `archlinux:latest`, `opensuse/tumbleweed`.

### v0.1.0 Release Test

The [v0.1.0 release test](.github/workflows/test-release-v0.1.0.yml) validates the release across **10 distro versions**:

| Distro | libzinnia | evdev | Model | Engine |
|--------|-----------|-------|-------|--------|
| Debian 11 | ✅ | ✅ | ✅ | ✅ |
| Debian 12 | ✅ | ✅ | ✅ | ✅ |
| Ubuntu 22.04 | ✅ | ✅ | ✅ | ✅ |
| Ubuntu 24.04 | ✅ | ✅ | ✅ | ✅ |
| Fedora 40 | ✅ | ✅ | ✅ | ✅ |
| Fedora 41 | ✅ | ✅ | ✅ | ✅ |
| Fedora latest | ✅ | ✅ | ✅ | ✅ |
| Arch Linux | ✅ | ✅ | ✅ | ✅ |
| openSUSE Leap | ❌ (not in repos) | ✅ | ✅ | ✅ |
| openSUSE Tumbleweed | ✅ | ✅ | ✅ | ✅ |

The test installs engine files to `/usr/local/bin`, verifies libzinnia loading via ctypes, checks Python syntax, confirms model placement, and validates module imports.

### Recognition Smoke Test

The recognition smoke test (`tests/test_recognition.py`) creates synthetic strokes:
- Horizontal line → recognized as **一** (score > 0.9)
- Cross shape → recognized as **十** (score > 0.95)

CI does not test IBus, evdev, or GTK (no display/hardware in containers).

## Known Limitations

- **Real hardware**: Tested on MacBook Pro (bcm5974) — should work on any touchpad with `BTN_TOUCH + ABS_X`, but Wayland popup positioning and SELinux evdev access are untested on Fedora/Arch.
- **Recognition accuracy**: Simplified Chinese uses the 幽兰百合 Community v1.1.0 model (9374 chars) as primary with tegaki zh_CN (6763 chars) as fallback. Tested at ~80% top-1 accuracy on real handwriting (MacBook trackpad, 20 common characters). Traditional Chinese uses tegaki zh_TW (11853 chars).
- **Single character**: No multi-character composition yet (one character at a time). V2 may add spatial segmentation for sequential input.
- **openSUSE Leap**: `zinnia` library not available in Leap 16.0 default repos. Use openSUSE Tumbleweed instead, or install zinnia from OBS manually.
- **Third-party model**: The 幽兰百合 model is hosted on Gitee (China). If Gitee is unreachable, the installer falls back to the local `models/` cache or warns and continues. CI containers skip the download gracefully.

## License

GPLv3 — required by dependencies (libzinnia, python3-evdev, ibus).

## Traditional Chinese

The engine supports both Simplified and Traditional Chinese as separate IBus engines. After installing, select from your IBus menu or switch with:

```bash
ibus engine handwrite-chinese-simplified   # Simplified (幽兰百合 9374 chars + tegaki zh_CN fallback)
ibus engine handwrite-chinese-traditional  # Traditional (tegaki zh_TW model, 11853 chars)
```

Both engines can be added to your input sources simultaneously — switch between them like any two input methods.

## Repository Structure

```
├── src/
│   ├── ibus-engine-handwrite-chinese    Main engine (Python, Zinnia ctypes, GTK popup, evdev integration)
│   └── handwrite_evdev.py               Evdev multitouch reader module
├── xml/
│   ├── handwrite-chinese-simplified.xml IBus component: Simplified Chinese
│   └── handwrite-chinese-traditional.xml IBus component: Traditional Chinese
├── icons/
│   ├── handwrite-chinese-simplified.svg Engine icon: Simplified
│   └── handwrite-chinese-traditional.svg Engine icon: Traditional
├── tools/
│   ├── install.sh                       Install script (Debian-native, accepts `--skip-deps`)
│   ├── restore.sh                       Rollback/restore script
│   └── 99-trackpad-handwrite.rules      Udev rule for touchpad access
├── tests/
│   ├── test_recognition.py             Synthetic stroke recognition smoke test
│   └── test_data/                      Test stroke data
├── docs/
│   └── screenshot.png                  App screenshot
│   ├── plan-handwriting-accuracy-test.md Methodology for comparing tegaki vs 幽兰百合 accuracy
│   └── multi-char-composition-with-phrase-boost-plan.md  V2 feature plan
├── models/                              Local model cache (gitignored)
├── packaging/                            Debian packaging, RPM spec, PKGBUILD
├── .github/workflows/
│   ├── ci.yml                          Main CI — 5 distros
│   └── test-release-v0.1.0.yml         v0.1.0 release test — 10 distro versions
├── bootstrap.sh                        Cross-distro install entry point
├── README.md
├── README.zh-CN.md
└── README.zh-TW.md
```
