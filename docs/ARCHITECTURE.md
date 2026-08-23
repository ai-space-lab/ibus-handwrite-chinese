# Architecture

## Three-Layer Model

The system breaks into three cooperating layers, each with a distinct responsibility.

### 1. IBus Layer

`src/ibus-engine-handwrite-chinese` contains the `HandwriteEngine` class, a subclass of `IBus.Engine`. It registers with the IBus input method framework, receives key events (`do_process_key_event`), manages cursor position (`do_set_cursor_location`), and controls the engine lifecycle (`do_enable`, `do_disable`). When activated, it creates the `HandwriteWin` GTK window and starts the evdev trackpad reader. On deactivation it tears down both.

The IBus component XML at `xml/handwrite-chinese.xml` declares the engine name, executable path, and supported language to the IBus daemon.

### 2. GTK Panel + Evdev Input

The `HandwriteWin` class (in `src/ibus-engine-handwrite-chinese`, ~1100 lines) draws the macOS-style floating panel:

- A dark (or light) GTK3 window positioned near the text cursor
- Candidate buttons rendered across the top of the window
- A drawing area that renders stroke points as they arrive
- Delete (backspace) and close buttons
- A drag handle to reposition the window
- A "Paused" overlay for the ESC state machine

The evdev integration module `src/handwrite_evdev.py` (`TrackpadReader` class) runs a background thread that reads raw multitouch events from the trackpad device. It tracks finger touches, strokes, taps, two-finger swipes, and candidate-zone drags. All callbacks are dispatched to the GTK main thread via `GLib.idle_add`.

Key event types from evdev flow:

- **One-finger stroke** in the drawing zone: captured as point sequences, rendered via Cairo on the GTK drawing area
- **Tap** (quick touch and lift within 250ms): triggers a candidate selection based on the X coordinate
- **Two-finger swipe**: detected as 2+ active MT slots, computes velocity and momentum for multi-page candidate navigation
- **One-finger drag in top 5% zone**: highlights candidates by position without selecting

### 3. PP-OCRv6 Recognition

The `OnnxHandle` class (embedded in `src/ibus-engine-handwrite-chinese`) wraps an ONNX Runtime inference session loaded with a PP-OCRv6 MobileNetV3-small model (18,710-character vocabulary). The recognition pipeline:

1. Stroke points are rendered to an offscreen Cairo surface (ARGB32)
2. The red channel is extracted, resized bilinearly to 48px height
3. Pixels are normalized to [-1, 1] and stacked into a [1, 3, 48, W] tensor
4. ONNX session runs with CPUExecutionProvider
5. CTC decoding uses MAX-pooled confidence (not mean) across time steps, excluding blank and unknown classes
6. Top-N candidates (default 24) are returned as `[(char, confidence), ...]`

The model and character dictionary (`dict_v6.txt`) are downloaded at install time via `tools/install.sh` or `bootstrap.sh`.

## Data Flow

```
User draws on trackpad
       │
       ▼
evdev event loop (TrackpadReader thread)
  ─ ABS_MT_TRACKING_ID / BTN_TOUCH → detect finger
  ─ ABS_MT_POSITION_X/Y → capture points
  ─ SYN_REPORT → process gesture state machine
       │
       ▼  GLib.idle_add dispatch
       │
       ▼
HandwriteWin: draw strokes on Cairo surface
  ─ on_stroke_begin / on_stroke_point / on_stroke_end
  ─ queue_draw() → Gtk.Widget.draw update
       │
       ▼
OnnxHandle.classify_async() [background thread]
  ─ Render strokes to offscreen bitmap
  ─ Bilinear resize to 48px height
  ─ Normalize to [-1, 1]
  ─ ONNX session.run("x", input_tensor)
  ─ CTC decode with MAX-pooled confidence
       │
       ▼  GLib.idle_add callback
       │
       ▼
HandwriteWin: update candidate buttons
  ─ Create/destroy Gtk.Button widgets
  ─ Show with (char, confidence) labels
       │
       ▼
User taps on trackpad
  ─ tap X coordinate → spatial map to candidate index
  ─ commit_selection() → IBus.commit_text()
```

## File Roles

| File | Role |
|---|---|
| `src/ibus-engine-handwrite-chinese` | Main engine (~1400 lines). Contains `OnnxHandle` (recognition), `HandwriteWin` (GTK panel), `HandwriteEngine` (IBus engine), and `main()`. |
| `src/handwrite_evdev.py` | Evdev multitouch reader. `TrackpadReader` maps raw evdev events to gestures. `TouchpadCapture` helper for data collection. |
| `src/handwrite_config.py` | TOML config loader with IBUS_HANDWRITE_* env var overrides. Manages theme, model paths, engine tuning, window dimensions. |
| `xml/handwrite-chinese.xml` | IBus component registration. Declares the `handwrite-chinese` engine name, executable, language (zh), and icon path. |
| `tools/install.sh` | System installer. Downloads model + dict, creates venv with onnxruntime, installs engine files, registers IBus component, sets up udev rule. |
| `bootstrap.sh` | Cross-distro entry point. Detects distro (apt/dnf/pacman/zypper), installs dependencies, delegates to install.sh. |
| `packaging/debian/` | Debian packaging control files: control, copyright, changelog, postinst, prerm, postrm. |
| `packaging/ibus-handwrite-chinese.spec` | RPM spec file for Fedora/openSUSE. |
| `packaging/PKGBUILD` | Arch Linux PKGBUILD reference for AUR submission. |
| `packaging/build-deb.sh` | Standalone .deb builder (source → binary .deb, used by CI). |
| `packaging/build-rpm.sh` | Standalone .rpm builder (source → .rpm, used by CI). |
| `tests/test_recognition.py` | Synthetic stroke recognition smoke test (一 → horizontal, 十 → cross). |
| `tests/test_esc_key_routing.py` | ESC state machine automated test under Xvfb. |
| `tests/test_gtk_write_phrase.py` | GTK writing simulation for UI regression. |
| `tools/restore.sh` | Rollback script: removes installed files, IBus component, udev rule. |
| `tools/99-trackpad-handwrite.rules` | Udev rule granting ACL-based trackpad access without root. |
| `tools/diagnose_trackpad.sh` | Diagnoses trackpad device, input group membership, IBus health. |

## Key Dependencies

| Dependency | Purpose |
|---|---|
| `python3-evdev` | Read raw multitouch events from trackpad device files (`/dev/input/event*`) |
| `ibus` + `gi` (PyGObject) | IBus input method framework integration; GTK3 window for the floating panel |
| `onnxruntime` | CPU-based ONNX model inference for PP-OCRv6 character recognition |
| `numpy` | Image tensor manipulation, bilinear resize, CTC decode |
| `pycairo` | Render stroke points to offscreen bitmap for recognition input |
| `sqlite3` (stdlib) | User dictionary: per-user stroke-to-character learning in SQLite database |
| `tomllib` / `tomli` | Parse TOML config file from `~/.config/ibus-handwrite-chinese/config.toml` |

## Build / Install Pipeline

```
Source tree
       │
       ▼
tools/install.sh (or bootstrap.sh → install.sh)
       │
       ├── Download PP-OCRv6 model + dict from HuggingFace / PaddlePaddle
       ├── SHA256 verification of downloaded files
       ├── Create venv at /usr/local/share/ibus-handwrite-chinese/venv/
       ├── pip install onnxruntime tomli in venv
       ├── Copy engine files to /usr/local/share/ibus-handwrite-chinese/
       ├── Create wrapper at /usr/local/bin/ibus-engine-handwrite-chinese
       ├── Copy IBus component XML to /usr/share/ibus/component/
       ├── Install udev rule at /etc/udev/rules.d/99-trackpad-handwrite.rules
       ├── Add user to 'input' group
       ├── Kill stale root ibus-daemon
       └── ibus-daemon --replace + ibus engine handwrite-chinese
```

### CI Build Pipeline (on `v*` tag push)

```
Release workflow (.github/workflows/release.yml)
       │
       ├── Resolve version from tag (e.g., v0.6.0)
       ├── packaging/build-deb.sh → .deb
       ├── packaging/build-rpm.sh → .rpm
       ├── tar --exclude=.git → source tarball
       ├── Verify artifacts
       └── Upload to GitHub Release
```

Packages install files to the same paths as `install.sh`. The `postinst` script
handles model download, venv creation, and udev setup at package install time.

## State Machine: ESC Key

The ESC state machine has two states, managed by `HandwriteWin._state`:

| State | ESC press | Enter press | Backspace |
|---|---|---|---|
| **0 (Active)** | Pause: ungrab trackpad, show "Paused" overlay, set state=1 | Commit first candidate (if exists); else pass through | Delete last stroke |
| **1 (Paused)** | Close + restore previous IME via `restore_previous_engine()` | Pass through to app | Pass through to app |

Auto-pause (state=0→1) also triggers on GTK `focus-out-event` after a 50ms
debounce, gated by `_has_drawn` to avoid pausing at startup.

## Future / V2

Multi-character composition with spatial segmentation and phrase-boost via a
SQLite user dictionary is planned. See `docs/multi-char-composition-with-phrase-boost-plan.md`.
