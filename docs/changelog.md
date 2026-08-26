# Changelog

All notable changes to this project are documented here. Follows [Keep a Changelog](https://keepachangelog.com/) format.

---

## [v0.6.0] - 2025-01-15

### Major Features

- **Complete ESC/Enter key handling rewrite** — fixes 5 critical bugs in key routing
- **Firefox ESC compatibility** — handles `IBUS_RELEASE_MASK` on ESC events
- **Auto-pause on focus loss** — pauses panel when clicking Firefox title bar / desktop
- **Window focus management fixes** — ensures keyboard focus on every activation cycle
- **Model download with pkexec** — permission elevation for system-wide model install
- **Preference dialog download button** — pulsing progress bar, auto-prompt on tier change
- **User dictionary** — SQLite-backed learning with configurable boost strength
- **Configurable shortcuts** — 6-tab GTK3 preference dialog with key capture UI
- **PP-OCRv6 MAX pooling** — fixed confidence calculation (was averaging, now max over time steps)
- **Dict index corruption fix** — preserves ideographic space (U+3000) in dictionary

### Added

- `--setup` CLI flag opens preference dialog
- `--test` standalone mode improvements (keyboard focus fixed)
- `IBUS_HANDWRITE_AUTO_DOWNLOAD` env var
- `engine.auto_pause_debounce_ms` config (default 50ms)
- `engine.delete_hold_ms` config (default 500ms)
- `model.download_timeout` config (default 30s)
- Theme auto-detection via `gsettings` / `kreadconfig5` / `GTK_THEME`
- SHA256 verification for model downloads (primary + fallback URLs)
- Drag handle hover effect in window top bar
- Candidate highlight via 1-finger drag in top trackpad zone
- Swipe momentum with configurable decay/threshold/tick
- Non-destructive multitouch (2nd finger during stroke saves/restores state)
- Udev rule for trackpad `uaccess` (`99-trackpad-handwrite.rules`)
- Input group auto-add during install
- Stale root `ibus-daemon` detection & kill
- `diagnose_trackpad.sh` diagnostic script
- `restore.sh` uninstall script with user data preservation prompt
- Cross-distro `bootstrap.sh` installer
- GitHub Actions CI across 5 distros (Debian, Ubuntu, Fedora, Arch, openSUSE)
- Release workflow building `.deb`, `.rpm`, source tarball

### Fixed

| # | Bug | Root Cause | Fix |
|---|-----|------------|-----|
| 1 | Dict index corruption | `line.strip()` removed U+3000 | `line.rstrip('\n')` |
| 2 | Confidence pooling | `np.mean()` diluted by blanks | `np.max()` (MAX pooling) |
| 3 | Stroke line width | Hardcoded 6px vs training data | Configurable `stroke_width` (default 8) |
| 4 | ESC/Enter key handling | Intercepted regardless of state | State-machine: ESC always handled; Enter/Backspace only in active state with candidates |
| 5 | `--test` keyboard focus | `set_accept_focus(False)` | `set_accept_focus(True)` before `present()` |
| 6 | Firefox ESC compatibility | `RELEASE_MASK` bypassed ESC check | Check ESC before `RELEASE_MASK` filter; 150ms debounce |
| 7 | ESC pause without text focus | No IBus context + no GTK focus | `set_accept_focus(True)` in `do_enable()`; removed focus-grab timer |
| 8 | Auto-pause on non-text focus | No key event path available | GTK `focus-out-event` → 50ms debounce → `on_key_esc()` |
| 9 | `present()` skipped on 2nd activation | `_focused_since_enable` race | Always call `present()` in idle handler |
| 10 | X11 property flush timing | `accept_focus` not flushed before `present()` | Set `accept_focus(True)` in `do_enable()` before `idle_add` |
| 11 | Model download permission | `tempfile.mkdtemp()` in root dir | Download to `/tmp`, move with `pkexec cp` fallback |
| 12 | Display stroke width ignored | Hardcoded `3 * scale` in Cairo | Use `CONFIG["engine"]["stroke_width"]` |
| 13 | Dead config keys | `model.variant`, `engine.max_strokes` | Removed from config & UI |

### Changed

- Default model tier: `small` (was `medium` in early versions)
- Default stroke width: 8px (was 6px)
- Momentum decay: 0.65 (was 0.5)
- Log format: JSON lines (was plain text)
- Config file: TOML (was JSON-like custom format)
- Model naming: `ppocrv6_{tier}_rec.onnx` (unified)
- Dictionary: `dict_v6.txt` (shared across tiers)

### Removed

- Legacy `model.variant` config key
- Legacy `engine.max_strokes` config key
- `--prompt` / `--free` CLI modes (use `--test` instead)

---

## [v0.5.0] - 2024-10-01

### Added

- PP-OCRv6 ONNX recognition (replaced legacy template matching)
- 18,710 character support via PP-OCRv6 dictionary
- ONNX Runtime inference backend
- Model tier selection (tiny/small/medium)
- On-demand model download from HuggingFace
- evdev trackpad integration with multitouch
- Tap-to-select with spatial mapping
- Two-finger swipe paging
- macOS-style floating panel with embedded candidates
- Cursor-proximity window positioning
- Drag handle for window repositioning
- Close button (×) with previous IME restore
- Delete stroke button (⌫)
- Dark theme (default)
- IBus component registration
- Debian packaging (`.deb`)
- Install script with dependency management

### Fixed

- Initial trackpad grab/ungrab sequence
- IBus engine lifecycle (enable/disable/focus)
- Candidate button click handling
- Window positioning near cursor
- Stroke rendering with Cairo

---

## [v0.4.0] - 2024-07-15

### Added

- Basic IBus engine skeleton
- GTK3 drawing area for handwriting
- Simple template-based recognition (pre-PP-OCR)
- Mouse fallback drawing
- Basic candidate display
- IBus key event handling (ESC, Enter, Backspace)

---

## [v0.3.0] - 2024-05-01

### Added

- Project structure
- IBus component XML
- Basic install script
- README with install instructions

---

## Breaking Changes by Version

### v0.6.0

| Change | Migration |
|--------|-----------|
| Config format: JSON-like → TOML | Delete `~/.config/ibus-handwrite-chinese/config.toml` and reconfigure |
| Model naming: `ppocrv6_{variant}.onnx` → `ppocrv6_{tier}_rec.onnx` | Re-download models via preference dialog |
| `model.variant` removed | Use `model.tier` (tiny/small/medium) |
| `engine.max_strokes` removed | No action needed (was unused) |
| Stroke width default: 6 → 8 | Adjust in Engine tab if needed |
| ESC behavior: single press closed | Now: 1×ESC = pause, 2×ESC = close |

### v0.5.0

| Change | Migration |
|--------|-----------|
| Recognition engine: template → PP-OCRv6 ONNX | Full reinstall required (run `restore.sh` then `install.sh`) |
| Model files: bundled → downloaded | Installer handles download |

---

## Upgrade Instructions

### From v0.5.x to v0.6.0

```bash
# 1. Uninstall old version
/usr/local/share/ibus-handwrite-chinese/restore.sh

# 2. Install new version
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh)

# 3. Reconfigure preferences
ibus-engine-handwrite-chinese --setup
ibus restart
```

### From v0.4.x or earlier

Full reinstall required — recognition engine completely changed.

```bash
# If restore.sh exists
/usr/local/share/ibus-handwrite-chinese/restore.sh

# Clean any remaining files
sudo rm -rf /usr/local/share/ibus-handwrite-chinese
sudo rm -f /usr/local/bin/ibus-engine-handwrite-chinese
sudo rm -f /usr/share/ibus/component/handwrite-chinese.xml
sudo rm -f /etc/udev/rules.d/99-trackpad-handwrite.rules

# Fresh install
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh)
```

---

## Release Checklist

Each release includes:

- [ ] Version bump in `VERSION` file
- [ ] Changelog updated
- [ ] Git tag `vX.Y.Z` pushed
- [ ] GitHub Release created with:
  - `.deb` package
  - `.rpm` package
  - Source tarball
  - SHA256 checksums
- [ ] CI passes on all 5 distros
- [ ] Manual test on Linux Mint 22 XFCE (reference platform)

---

## Contributors

- **ai-space-lab** — Core development, architecture, PP-OCR integration, IBus/GTK/evdev engineering
- **PaddlePaddle** — PP-OCRv6 model (Apache 2.0)
- **Microsoft** — ONNX Runtime (MIT)
- **IBus Project** — Input method framework
- **GTK Project** — UI toolkit

---

## Links

- [GitHub Releases](https://github.com/ai-space-lab/ibus-handwrite-chinese/releases)
- [GitHub Issues](https://github.com/ai-space-lab/ibus-handwrite-chinese/issues)
- [PP-OCRv6 Model Card](https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx)
- [ONNX Runtime](https://onnxruntime.ai/)