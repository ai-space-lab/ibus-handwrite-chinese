# Anchored Summary — ibus-handwrite-chinese

*Generated: 2026-07-08*

## Project Overview

A Chinese handwriting input method for Linux with a macOS-style floating panel, evdev trackpad integration, and PP-OCRv6 ONNX deep-learning recognition (18,710 chars).

---

## Completed Work (Timeline)

### Phase 1: Foundation & Bootstrapping

| Plan | What | Status |
|------|------|--------|
| `fix-bootstrap-errors` | Fixed `bootstrap.sh` / `install.sh` crashes: CD-ROM apt source error, missing `ibus` dependency, root-elevation guard issues | ✅ Done |
| `fix-root-ibus-daemon` | Fixed stale root `ibus-daemon` left behind by `sudo`-wrapped install scripts — ibus commands now run as the real user via `sudo -u "$REAL_USER"` | ✅ Done |
| `sudo-less-install` | Removed "must run as root" guard from `install.sh`/`restore.sh`/`bootstrap.sh` — individual privileged commands get `sudo` internally | ✅ Done |

### Phase 2: PP-OCRv6 Recognition Pipeline

| Plan | What | Status |
|------|------|--------|
| `06-character-data-collection-and-analysis` | Built data collection tools (`collect_ppocr_data.py`, `analyze_ppocr_data.py`) for real handwriting vs synthetic strokes | ✅ Done |
| `07-ppocr-pipeline-fixes-and-validation` | 3 bugs fixed: (1) Dict index corruption — `strip()` eating U+3000; (2) Confidence pooling — `np.mean`→`np.max`; (3) Stroke line width 6→8px. Validated 40/40 characters = **100% top-1 accuracy** | ✅ Done |

### Phase 3: Engine Unification

| Plan | What | Status |
|------|------|--------|
| `08-unify-ime-engines` | Merged simplified/traditional engines into one ONNX-only `handwrite-chinese` engine. Removed Zinnia/tegaki (`~88 LOC`), new `中` icon in chop red `#c41e3a`. Single XML, single SVG | ✅ Done |

### Phase 4: CI & Documentation

| Plan | What | Status |
|------|------|--------|
| `09-fix-ci-model-downloads` | Fixed broken model download URLs in CI (pointed to nonexistent GitHub Release assets instead of upstream HuggingFace/PaddlePaddle) | ✅ Done |
| `10-normalize-documentation` | Normalized terminology (touchpad→trackpad), CJK README filenames (汉/漢), fixed badge URLs, corrected hardware claims | ✅ Done |

### Phase 5: ESC & Post-Install Experience

| Plan | What | Status |
|------|------|--------|
| `11-esc-key-reliability-after-install` | Root-caused ESC not working: (1) `input` group not active until logout; (2) stale root ibus-daemon blocking D-Bus. Documented both issues | ✅ Investigated |
| `12-ibus-restart-in-packages` | Added `ibus restart` to package postinsts (`.deb`, `.rpm`, Arch). **Later reversed** in Plan 13 — postinst is root-level, session operations don't belong there | ✅ Done → Reverted |
| `13-revise-postinstall-to-match-install-sh` | Ported system-level blocks from `install.sh` to all 3 packages: `sg input` wrapper fallback, PP-OCRv6 model download, venv+onnxruntime, diagnose_trackpad.sh. **Removed** automated `ibus restart`. Added consistent post-install message. **Reverted `exec sg` bug** → wrapper wasn't catching failures with `|| true`. **v0.5.0 released** | ✅ Done |

### Phase 6: Trackpad & Firefox Focus Fixes

| Plan | What | Status |
|------|------|--------|
| `14-fix-touchpad-not-working-after-deb-install` | **Root cause**: Missing `handwrite_evdev.py` symlink in engine directory → `import handwrite_evdev` fails → engine starts in mouse-only mode. **Fix**: Added `ln -sf` symlink to `.deb` postinst and Arch `.install`. RPM left as-is (Option A). Commit `71aa1df` | ✅ Done |
| `15-firefox-esc-not-working` | Moved ESC handler before `RELEASE_MASK` filter in `do_process_key_event` so Firefox ESC key events (sent with release mask) are caught. Added 150ms debounce. Validated in Firefox via `/tmp/hw.log` | ✅ Done |
| `16-auto-pause-on-focus-loss` | Implemented `do_focus_out()` (auto-pause) + `do_focus_in()` (auto-resume) in `HandwriteEngine`. When clicking Firefox title bar, writing UI auto-pauses. Click back into input field → auto-resumes. Commit `8809bf7` | ✅ Done |

### Phase 7: ESC Pause Without Text Field Focus + Candidate Tap Regression

| Plan | What | Status |
|------|------|--------|
| `17-focus-in-debounce` | Added 300ms debounce in `do_focus_in` to prevent immediate auto-resume after focus-out flicker. Commit `ca5c4e2` | ✅ Done |
| `18-startup-grace-period-for-do-focus-out` | Added 1s startup grace period in `do_focus_out` + `_has_drawn` guard to prevent auto-pause on engine startup before user interacts. Commits `681a199`, `70defeb` | ✅ Done |
| *ESC no-text-focus fix* **→ regressed** | First attempt: set `set_accept_focus(True)` before `present()` in `do_enable` so GTK `on_key` catches ESC when no IBus context exists. **Regression**: candidate taps don't output to focused text fields because focus steal kills IBus input context. Commits `7836f39`, `03cffa3` | ⚠️ **Regressed** |
| `fix-candidate-tap-regression` | Third attempt after dual review: remove unconditional `present()` from `do_enable()` — defer focus grab to `_grab_focus_if_needed()` guarded by `_focused_since_enable` + `screen.get_active_window()`. Plan has comparison table (with/without), todos, Wayland limitation accepted. | ✅ **Planned, awaiting approval** |

---

## Key Technical Decisions Made

1. **Single ONNX-only engine** — removed Zinnia/tegaki fallback (Plan 08)
2. **No `usermod` in postinst** — `TAG+="uaccess"` udev rule grants device access via systemd-logind ACLs (Plan 14 architectural decision)
3. **No automated `ibus restart` in postinst** — postinst runs as root, has no D-Bus session context (Plan 13)
4. **No stale root ibus-daemon cleanup in postinst** — belongs in install scripts, not package lifecycle (Plan 13)
5. **RPM left as-is** — installs `handwrite_evdev.py` directly in engine directory, no symlink needed (Plan 14 Option A)
6. **Auto-pause via focus events, not global key grab** — uses IBus `do_focus_out`/`do_focus_in` API. Doesn't steal keyboard focus or require X11-specific code (Plan 16)
7. **`_focused_since_enable` guard instead of unconditional focus grab** — tracks whether any text field currently has IBus focus. Only grabs GTK keyboard focus (for `on_key` ESC handling) when `_focused_since_enable` is False, preserving IBus `commit_text()` path for candidate taps (Phase 7)
8. **`GLib.idle_add` at `GLib.PRIORITY_LOW`** — ensures `do_focus_in` (delivered by IBus in same event loop iteration) sets `_focused_since_enable = True` before the idle callback runs, preventing a race condition where the grab fires before the focus-in event is processed (Phase 7)
9. **Auto-pause guards** — 1s startup grace period + `_has_drawn` flag prevent auto-pause from firing on engine boot when no text field has focus yet (Phase 7)
10. **do_focus_in 300ms debounce** — prevents rapid focus-out/focus-in flicker from triggering spurious auto-resume (Phase 7)

## Current State

- **Latest release**: `v0.5.0` (rebuilt) — includes symlink fix for trackpad access on .deb and Arch
- **Last commit**: `a9857fd` — `fix: gate focus grab behind _focused_since_enable guard to restore candidate taps`
- **Working tree**: Clean — all changes committed
- **Pending**: Push to `origin/main`, real hardware verification of candidate tap + ESC scenarios
- **Release workflow**: `28764127515` — **16/16 all passed ✅**
