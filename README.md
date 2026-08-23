# IBus Chinese Handwriting Input Method

[![CI](https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/ci.yml/badge.svg)](https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/ci.yml)
[![Release](https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/release.yml/badge.svg)](https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/release.yml)

**English** · [简体中文](README.zh-Hans-汉.md) · [繁體中文](README.zh-Hant-漢.md)

A Chinese handwriting input method for Linux with a macOS-style floating panel, evdev trackpad integration, and PP-OCRv6 ONNX deep-learning recognition (18710 chars).

![screenshot](docs/screenshot.png)

## Features

- **macOS-style popup**: dark floating window with embedded candidates at the top
- **evdev trackpad input**: draw characters on your laptop's trackpad — works on any trackpad with touch detection (BTN_TOUCH or ABS_MT_TRACKING_ID) + ABS_X/ABS_MT_POSITION_X support (tested on Acer Aspire AL16-54P (HTIX5288) and MacBook Pro bcm5974 — other trackpads may work but are untested)
- **Tap to select**: quickly tap on the trackpad to pick a candidate — spatial mapping matches candidate position
- **Two-finger swipe**: swipe left/right with two fingers to page through candidates
- **Swipe momentum**: fast two-finger swipe decelerates through multiple pages — the faster you swipe, the more pages it advances
- **1-finger candidate drag**: drag one finger in the top 5% trackpad zone to highlight candidates by position, lift to select
- **Non-destructive multitouch**: accidental second finger during a stroke won't destroy the partial stroke — the engine saves and restores stroke state
- **Delete stroke**: ⌫ button to undo the last stroke
- **Close button**: × button always visible at top-left, closes and restores previous input method
- **ESC state machine**: one ESC pauses (ungrab trackpad, show "Paused" overlay), another ESC closes and restores the previous input method; click the window to resume. **Enter with candidates** commits the first candidate; **Enter with no candidates** passes through to the underlying application.
- **Cursor-proximity positioning**: popup appears near the text cursor, not at a fixed screen position
- **Drag handle**: custom drag handle in the top bar to reposition the window
- **Mouse fallback**: if no evdev trackpad is available, draw with the mouse
- **Preference dialog**: 6-tab GTK3 settings UI (General, Model, Engine, Window, User Dictionary, Shortcuts) — accessible from IBus menu or via `ibus-engine-handwrite-chinese --setup`
- **On-demand model download**: Download PP-OCRv6 models (tiny/small/medium) directly from the preference dialog, with automatic pkexec permission elevation for system-wide install
- **Auto-download prompt**: Selecting a missing model tier automatically asks if you want to download it
- **Configurable keyboard shortcuts**: Customize all keybindings (ESC, Enter, Backspace, page up/down, theme cycling, settings) via the Shortcuts tab
- **User dictionary**: Learns characters you select and boosts them in future recognition, via local SQLite database
- **TOML configuration**: All settings stored in `~/.config/ibus-handwrite-chinese/config.toml`, overridable via `IBUS_HANDWRITE_*` environment variables
- **PP-OCRv6 deep-learning engine**: ONNX-based CNN recognition covering 18,710 characters, with MAX-pooled confidence scoring for reliable top-1 predictions
- **'--test' mode**: standalone GTK window (no IBus dependency) for quick testing, data collection, and debugging

## Cross-Distro Support

`bootstrap.sh` auto-detects your Linux distribution and installs everything:

| Distro | Method |
|--------|--------|
| Debian 12+, Ubuntu 22.04+, Mint 21+ | `apt` + model download |
| Fedora 40+ | `dnf` + model download |
| Arch Linux, Manjaro | `pacman` + `yay` (AUR) + download |
| openSUSE Tumbleweed | `zypper` + download |

The installer downloads the PP-OCRv6 ONNX model and character dictionary for recognition.

## Requirements

- Linux with a trackpad (or touchscreen)
- IBus input method framework (default on most desktops)
- Python 3.8+ with `python3-venv` (for onnxruntime virtual environment)
- **Debian family**: Debian 11+, Ubuntu 22.04+, Linux Mint 21+
- **Fedora**: Fedora 40+
- **Arch**: Arch Linux, Manjaro
- **openSUSE**: Tumbleweed

The engine uses **ONNX Runtime** for PP-OCRv6 recognition. The install script
automatically creates a Python venv with onnxruntime — no manual pip needed.

## Quick Install

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh)
ibus restart
```

**Debian/Ubuntu/Mint** users can also use the traditional method:

```bash
sudo apt install python3-evdev python3-venv
git clone https://github.com/ai-space-lab/ibus-handwrite-chinese
cd ibus-handwrite-chinese
./tools/install.sh         # add --skip-deps if deps already installed (sudo used internally)
ibus restart
```

`install.sh` automatically:
- Downloads the PP-OCRv6 ONNX model and character dictionary
- Creates a Python virtual environment with onnxruntime installed
- Installs a wrapper script as the engine binary
- Restarts IBus and activates Chinese Handwriting as the current IME

Or select **Chinese Handwriting** from your desktop's IBus menu.

To switch back to your previous IME later, use your IBus menu or:
```bash
ibus engine <previous-engine>
```

## Packages

Pre-built packages are available on the [GitHub Release](https://github.com/ai-space-lab/ibus-handwrite-chinese/releases) page:

| Format | Command | Distros |
|--------|---------|---------|
| `.deb` | `sudo dpkg -i <file> && sudo apt install -f` | Debian 11+, Ubuntu 22.04+, Mint 21+ |
| `.rpm` | `sudo rpm -i <file>` | Fedora 40+, openSUSE Tumbleweed |
| `PKGBUILD` | Reference in `packaging/PKGBUILD` | Arch Linux (submit to AUR manually) |

Packages are built automatically by CI on tag push. Post-install downloads the PP-OCRv6 ONNX model and character dictionary.

## Usage

1. Switch to **Chinese Handwriting** from your IBus menu
2. A dark floating panel appears near your text cursor
3. Draw Chinese characters on your laptop's trackpad with one finger
4. Candidate characters appear at the top of the panel
5. Tap on the trackpad to select a candidate (spatial mapping)
6. Use two-finger swipe left/right to page through candidates — swipe faster to advance more pages with momentum
7. Drag one finger near the top edge of the trackpad to highlight candidates by position; lift to select
8. Press **⌫** to undo the last stroke
9. Press **ESC** once to pause (window shows "Paused" overlay)
10. **ESC** again closes and restores previous input method
11. Click the window to resume after pausing
12. When no candidates are displayed (no strokes drawn), **Enter** passes through to the app — type normally in your terminal
13. For testing without IME switching, use the venv Python:
    ```bash
    /usr/local/share/ibus-handwrite-chinese/venv/bin/python3 \
      /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese --test
    ```
    Recognition results logged to `/tmp/ppocr-recognition.log`.

## Troubleshooting

- **Trackpad not accessible**: Run `sudo udevadm trigger` to apply the udev rule, or add your user to the `input` group: `sudo usermod -a -G input $USER && reboot`. Verify with `getfacl /dev/input/event*` — your user should have `rw` access on the trackpad device.
- **Engine won't start / "Cannot find engine handwrite-chinese"**: Run `ibus restart` after installation, then try `ibus engine handwrite-chinese`. The engine needs IBus to recognize the component XML at `/usr/share/ibus/component/handwrite-chinese.xml`.
- **onnxruntime errors on startup**: The install script creates a Python venv with onnxruntime at `/usr/local/share/ibus-handwrite-chinese/venv/`. If this step failed, re-run `./tools/install.sh` or manually create the venv: `sudo python3 -m venv --system-site-packages /usr/local/share/ibus-handwrite-chinese/venv && sudo /usr/local/share/ibus-handwrite-chinese/venv/bin/pip install onnxruntime`.
- **Ctrl+Space / Switch key not working**: Check that IBus trigger shortcut is configured (`ibus-setup` or `dconf read /desktop/ibus/general/hotkey/trigger`). A stale root-owned `ibus-daemon` can intercept key events — kill it with `sudo pkill -u root ibus-daemon`.
- **Must click trackpad to draw**: If your trackpad requires a physical click to register touches, the engine now also tracks via `ABS_MT_TRACKING_ID` (finger-on-surface) — try just touching the trackpad lightly. If it still requires clicking, your trackpad firmware may need a higher sensitivity setting.
- **Permission denied**: Verify with `getfacl /dev/input/event*` — your user should have `rw` access on the trackpad device. If the udev rule (`/etc/udev/rules.d/99-trackpad-handwrite.rules`) is present but ACLs aren't applied, reload with: `sudo udevadm control --reload-rules && sudo udevadm trigger`.
- **IBus indicator not showing in panel**: Run `ibus-daemon --daemonize --replace` to restart IBus. In Cinnamon, the IBus icon appears in the system tray — if missing, toggle the setting: `gsettings set org.freedesktop.ibus.panel show 1` (always-visible language bar).
- **ESC not working / Enter consumed by engine**: If Enter doesn't reach the terminal after pressing ESC to pause, re-install with the latest `install.sh`. The fix ensures that (1) Enter passes through when no candidates are present, (2) pressing ESC in paused state closes and restores the previous IME, and (3) ESC now works in Firefox and other applications that send key events with IBUS_RELEASE_MASK set.

## Testing

Two workflows cover development and releases:

### Main CI

[Main CI](.github/workflows/ci.yml) runs on every push/PR to `main` across 5 Docker containers:
- **lint**: shellcheck, xmllint, Python syntax checks
- **test-install**: installs dependencies per distro, checks Python syntax
- **test-bootstrap**: full bootstrap.sh end-to-end run, verifies installed files and model placement, runs recognition smoke test
- **test-gtk-write**: GTK writing simulation across 10 distro versions, captures screenshots as artifacts

Containers tested: `debian:bookworm`, `ubuntu:24.04`, `fedora:latest`, `archlinux:latest`, `opensuse/tumbleweed`.

### Release

[Release](.github/workflows/release.yml) runs on `v*` tag pushes or manual dispatch:
- resolve release tag/version
- build `.deb`, `.rpm`, and source tarball
- verify packaged artifacts
- upload release assets to GitHub Release

### Recognition Smoke Test

The recognition smoke test (`tests/test_recognition.py`) creates synthetic strokes:
- Horizontal line → recognized as **一** (score > 0.9)
- Cross shape → recognized as **十** (score > 0.95)

CI tests GTK under Xvfb, but not live IBus, evdev, or real trackpad hardware in containers.

### Manual Test Environment

The recent ESC/Enter fixes were validated on this environment:

| Component | Detail |
|-----------|--------|
| OS | Linux Mint 22.3 (Zena) XFCE |
| Kernel | 6.14.0-37-generic (x86_64) |
| Desktop | XFCE on X11 |
| IBus | 1.5.29-rc2 |
| Python | 3.12.3 |
| Trackpad | bcm5974 (MacBook Pro, USB) |
| Install method | `sudo ./tools/install.sh` or `.deb` package |

### PP-OCRv6 Accuracy Validation

Analysis scripts for validating PP-OCRv6 recognition accuracy:
- `scripts/collect_ppocr_data.py` — Interactive data collection via `--test` mode (or `--prompt` / `--free` modes)
- `scripts/analyze_ppocr_data.py` — Accuracy, confidence histogram, calibration, stroke complexity, and dict index analysis
- `scripts/capture_one.py` — Single-stroke capture and recognition test
- `scripts/gtk_collect_loop.py` — Batch collection using log-file polling with `--test` mode

Run the full analysis pipeline:
```bash
python3 scripts/analyze_ppocr_data.py --input .omo/evidence/ppocr-handwriting-dataset/dataset-chat-v1.json --verbose
```

## Known Limitations

- **Real hardware**: Tested on Acer Aspire AL16-54P (HTIX5288) and MacBook Pro (bcm5974) — should work on any touchpad with `ABS_MT_TRACKING_ID` or `BTN_TOUCH` + `ABS_X`, but Wayland popup positioning and SELinux evdev access are untested on Fedora/Arch.
- **Recognition accuracy**: Pure PP-OCRv6 ONNX recognition (18710 chars). Validated at 100% top-1 accuracy on 40 real handwriting characters (36 distinct chars, including 7 similar-pair groups: 土/士, 未/末, 日/曰, 人/入, 大/太, 已/己, 上/下). Average confidence: 94.97%.
- **Single character**: No multi-character composition yet (one character at a time). V2 may add spatial segmentation for sequential input.

## Acknowledgments

- **PP-OCRv6** — text recognition model by [PaddlePaddle](https://github.com/PaddlePaddle/PaddleOCR) / Baidu, licensed under [Apache 2.0](https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE).
- **ONNX Runtime** — cross-platform inference engine by Microsoft, licensed under [MIT](https://github.com/microsoft/onnxruntime/blob/main/LICENSE).

## License

GPLv3 — required by dependencies (python3-evdev, ibus).

## Configuration

### Preference Dialog

Open the 6-tab preference dialog from your IBus menu:
- Right-click IBus tray icon > Preferences > Chinese Handwriting
- Or run: `ibus-engine-handwrite-chinese --setup`
- Or search "Chinese Handwriting" in your desktop settings

The dialog has these tabs:

| Tab | Settings |
|-----|----------|
| **General** | Theme (dark/light/auto), log level, log path |
| **Model** | Model tier (tiny/small/medium), custom model/dict paths, auto-download toggle, download button with progress indicator |
| **Engine** | Stroke width (px), page size, max candidates, momentum settings, debounce timers |
| **Window** | Window width/height, drawing height, drag handle height, candidate button width |
| **User Dict** | Enable/disable user dictionary, boost strength, max entries |
| **Shortcuts** | Customize all keybindings (ESC, Enter, Backspace, page up/down, cycle theme, open settings) |

Changes take effect after clicking **Apply** and restarting IBus (`ibus restart`).

### Environment Variables

All settings can be overridden via `IBUS_HANDWRITE_*` environment variables, which take precedence over the TOML config file:

| Variable | Config Key | Example |
|----------|-----------|---------|
| `IBUS_HANDWRITE_THEME` | general.theme | `dark` |
| `IBUS_HANDWRITE_LOG_LEVEL` | general.log_level | `DEBUG` |
| `IBUS_HANDWRITE_PPOCR_MODEL` | model.tier | `small` |
| `IBUS_HANDWRITE_PPOCR_MODEL_PATH` | model.path | `/path/to/model.onnx` |
| `IBUS_HANDWRITE_PPOCR_DICT_PATH` | model.dict_path | `/path/to/dict.txt` |
| `IBUS_HANDWRITE_DOWNLOAD_PATH` | model.download_path | `/usr/local/share/ibus-handwrite-chinese/models` |
| `IBUS_HANDWRITE_AUTO_DOWNLOAD` | model.auto_download | `true` |
| `IBUS_HANDWRITE_STROKE_WIDTH` | engine.stroke_width | `12` |

### Model Management

Models are downloaded via the preference dialog's **Model** tab:

1. Select a tier (tiny / small / medium) from the dropdown
2. If the model is not yet downloaded, a dialog asks if you want to download it now
3. Click **Download Model** to start — a pulsing progress bar shows activity
4. The model downloads to the system temp directory, then is copied to the target location (uses `pkexec` for permission elevation if needed)
5. The dictionary (`dict_v6.txt`) is shared across all tiers
6. Restart IBus after downloading for the engine to pick up the new model

You can also set a custom model path via the **Model Path** / **Dict Path** fields to use a model stored elsewhere.

### Model Tiers

| Tier | Params | Use Case |
|------|--------|----------|
| tiny | 1.5M | Fast, low-resource environments |
| small | ~8M | Balanced speed/accuracy (default) |
| medium | 34.5M | Highest accuracy |

### Bug Fixes Applied

Thirteen bugs were identified and fixed across the PP-OCRv6 pipeline, ESC state machine, Firefox compatibility, desktop/Firefox non-text area auto-pause, model download, configuration, and preference dialog:

1. **Dict index corruption** (line 290): `line.strip()` stripped U+3000 (ideographic space) from a dict entry, shifting all subsequent character indices by 1. Fixed with `line.rstrip('\n')`.
2. **Confidence pooling** (line 405): `np.mean(probs, axis=0)` averaged across all CTC time steps including blank frames, diluting true confidence by ~10×. Fixed with `np.max(probs, axis=0)` (MAX pooling) which matches CTC argmax behavior for single-character recognition.
3. **Stroke line width** (line 364): `cr.set_line_width(6)` rendered strokes thinner than the training data distribution. Increased to `set_line_width(8)`.

### 4. ESC key reliability & Enter pass-through (PR #1)
The ESC state machine was refined to handle the Enter key correctly in all states:

| Key | Active (state 0) | Paused (state 1) |
|---|---|---|
| ESC | Pause panel, show overlay | Close + restore previous IME |
| Enter + candidates | Commit first candidate | ✅ Pass through to app |
| Enter + no candidates | ✅ Pass through to app | ✅ Pass through to app |
| Backspace | Clear strokes (passes through) | ✅ Pass through to app |

**Root cause**: `do_process_key_event` intercepted Enter/Backspace/ESC whenever the window was visible, regardless of the paused state or whether candidates existed. Fixed by:
- Separating ESC (always handled) from Enter/Backspace (only intercepted in active state 0)
- Adding `self.last_results` guard: Enter only consumed when candidates exist
- Applying the same guards to the GTK `on_key` handler used by `--test` mode

### 5. `--test` mode keyboard focus fix
The standalone `--test` mode window could not receive GTK keyboard events because `set_accept_focus(False)` was set in `__init__`. Fixed by calling `win.set_accept_focus(True)` before `win.present()` in `main()`.

### 6. Firefox ESC compatibility
Firefox sends ESC key events through IBus with `IBUS_RELEASE_MASK` (1 << 30) set, which bypassed the original ESC handler that checked for `RELEASE_MASK` before handling ESC. Fixed by:
- Moving the ESC check before the `RELEASE_MASK` filter in `do_process_key_event` — ESC is now handled regardless of press/release state
- Adding a 150ms debounce in `on_key_esc()` to prevent double-fire from press-plus-release event pairs
- Verified working via `/tmp/hw.log` log analysis showing correct ESC → pause → close state transitions in Firefox

### 7. ESC pause when no text field has focus
Pressing ESC to pause the panel did not work when no text field was focused (e.g., Firefox title bar, desktop). Two key event paths exist: the IBus path (`do_process_key_event`) requires an active IBus input context (only created by text-entry widgets), and the GTK path (`on_key` handler) requires the panel to have keyboard focus — which was blocked by `set_accept_focus(False)`.

**Root cause**: A previous fix attempted a 50ms delayed focus grab (`_grab_focus_if_needed`) but immediately reverted `set_accept_focus(False)` before the window manager processed the focus grant. Logs showed the grab ran but ESC never arrived.

**Fix**: Removed the timer entirely. In `do_enable()`, call `set_accept_focus(True)` before `present()` and leave it True for the session — matching what `--test` mode already does. In `do_disable()`, reset to `False`. Verified via xdotool: `on_key_esc: _state=0` logged when pressing ESC with desktop focused.

### 8. Auto-pause on non-text area focus loss (Firefox title bar, desktop background)
When the user clicked Firefox's title bar or the desktop background while the handwriting window was open, no ESC or keyboard event could reach the window — the IBus context was inactive (no text field) and the window had no keyboard focus. Pressing ESC did nothing.

**Root cause**: Two event paths exist — IBus's `do_process_key_event` (requires an active IBus input context, only created by text-entry widgets) and GTK's `on_key` handler (requires the window to have keyboard focus). After clicking a non-text area, neither path was available.

**Fix**: Added GTK `focus-out-event` handler (`on_focus_out_event`) that schedules a 50ms debounce timer. On expiry, `_handle_focus_lost` calls `on_key_esc()` to auto-pause the window. The 50ms debounce absorbs spurious XFCE `do_focus_in` signals that fire ~20ms after desktop clicks. The auto-pause is gated by `_has_drawn` — no auto-pause if the user hasn't drawn any strokes (avoids confusing startup behavior).

### 9. `present()` skipped on second activation due to `_focused_since_enable` race
After closing the handwriting window (via double-ESC or switching IME) and reactivating it a second time, ESC and auto-pause silently stopped working. The window appeared but had no keyboard focus.

**Root cause**: `_grab_focus_if_needed` is scheduled via `GLib.idle_add` during `do_enable()`. On the second activation, a spurious XFCE `do_focus_in` signal fired before the idle handler ran, setting `_focused_since_enable=True`. The old code then skipped `self.win.present()` entirely — the window was visible but had no keyboard focus, so GTK `focus-out-event` never fired and ESC key events never arrived.

**Fix**: Always call `self.win.present()` in `_grab_focus_if_needed`, regardless of `_focused_since_enable`. This is safe because in handwriting mode the user interacts via trackpad/mouse, not keyboard — the window needs focus only for ESC routing and GTK focus events.

### 10. X11 property flush timing prevents `present()` from granting focus
Even after fix #9, some second-activation attempts still failed to get keyboard focus. Investigation revealed `on_focus_in_event` was missing from the activation sequence, even though `present()` was called.

**Root cause**: `set_accept_focus(True)` and `present()` were both called inside `_grab_focus_if_needed` (the GLib idle handler). GTK batches X11 `WM_HINTS` property changes — when the idle handler ran, `accept_focus=True` had not been flushed to the X server yet. The window manager still saw `accept_focus(False)` (still in effect from the preceding `do_disable()`) and denied the focus request.

**Fix**: Call `self.win.set_accept_focus(True)` in `do_enable()` before `show_all()` and `GLib.idle_add`. By the time the idle handler fires and calls `present()`, the X11 property change is already flushed to the server. The WM sees `accept_focus(True)` and grants focus, producing `on_focus_in_event` and enabling ESC and `on_focus_out_event` on every activation cycle.

### Validation Results

40 real handwriting characters collected via `--test` mode and trackpad input:

| Metric | Result |
|--------|--------|
| Top-1 accuracy | 40/40 (100%) |
| Top-5 accuracy | 40/40 (100%) |
| Average confidence | 94.97% |
| Min confidence | 34.47% (小) |
| Max confidence | 100.00% (月, 女, etc.) |
| Similar pairs tested | 7 groups, 14/14 correct |

Characters tested: 一 七 三 上 下 不 中 九 二 五 人 入 八 六 十 口 四 土 士 大 天 太 女 好 小 山 己 已 心 文 日 曰 月 木 未 末 水 火 王 田

Full analysis report: `.omo/evidence/ppocr-handwriting-dataset/analysis-report.json`
Bottleneck report: `.omo/evidence/ppocr-handwriting-dataset/bottleneck-report.txt`

### 11. Model download permission error
Downloading models from the preference dialog failed with `PermissionError` because
`tempfile.mkdtemp()` created temp directories inside the root-owned `/usr/local/share/.../models/`
directory. Fixed by downloading to system tempdir (`/tmp`) instead, and using `shutil.move()`
with a `pkexec cp` fallback for the final copy to the target directory.

### 12. Display stroke width ignored preference
Changing the stroke width in the Engine tab had no visible effect — the display drawing
hardcoded `3 * scale` instead of reading `CONFIG["engine"]["stroke_width"]`. Fixed at
two places in the Cairo drawing code: `rebuild_pix()` (completed strokes) and `on_draw()`
(live stroke). Recognition rendering (line 183) already used the config value.

### 13. Config cleanup
Removed two dead config keys: `model.variant` (legacy from pre-PP-OCRv6 naming) and
`engine.max_strokes` (defined in config + prefs UI but never read by the engine).

## Repository Structure

```
├── scripts/
│   ├── analyze_ppocr_data.py          PP-OCRv6 accuracy analysis pipeline
│   ├── collect_ppocr_data.py          Interactive handwriting data collection
│   ├── capture_one.py                 Single-shot capture helper
│   ├── gtk_collect_loop.py            Log-based GTK collection script
│   └── read_last_log.py               Recognition log reader
├── src/
│   ├── ibus-engine-handwrite-chinese    Main engine (Python, GTK popup, evdev integration)
│   ├── handwrite_config.py              TOML/ENV configuration loader
│   ├── handwrite_model_download.py      PP-OCRv6 model downloader with SHA256 verification
│   ├── handwrite_prefs.py               6-tab GTK3 preference dialog
│   ├── handwrite_shortcuts.py           Configurable keybinding system
│   ├── handwrite_userdict.py            SQLite-backed per-user character learning
│   └── handwrite_evdev.py               Evdev multitouch reader module
├── xml/
│   └── handwrite-chinese.xml               IBus component XML
├── icons/
│   └── handwrite-chinese.svg               Engine icon
├── tools/
│   ├── install.sh                       Install script (Debian-native, accepts `--skip-deps`)
│   ├── restore.sh                       Rollback/restore script
│   ├── 99-trackpad-handwrite.rules      Udev rule for trackpad access
│   └── diagnose_trackpad.sh            ESC + input group + IBus diagnostics
├── tests/
│   ├── test_recognition.py             Synthetic stroke recognition smoke test
│   ├── test_esc_key_routing.py         ESC key routing automated test
│   └── test_data/                      Test stroke data
├── docs/
│   └── screenshot.png                  App screenshot
│   ├── plan-handwriting-accuracy-test.md Historical accuracy test methodology
│   └── multi-char-composition-with-phrase-boost-plan.md  V2 feature plan
├── models/                              Local model cache (gitignored)
├── packaging/                            Debian packaging, RPM spec, PKGBUILD
├── .github/workflows/
│   ├── ci.yml                          Main CI — 5 distros
│   └── release.yml                     Release build, verify, upload
├── .omo/
│   └── evidence/ppocr-handwriting-dataset/  Accuracy validation evidence
│       ├── dataset-chat-v1.json             40 handwriting samples, 100% accuracy
│       ├── analysis-report.json             Full analysis report with metrics
│       └── bottleneck-report.txt            Bug fix and validation report
├── bootstrap.sh                        Cross-distro install entry point
├── README.md
├── README.zh-Hans-汉.md
└── README.zh-Hant-漢.md
```
