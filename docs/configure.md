# Configuration

The Chinese Handwriting input method can be configured through:

1. **Preference Dialog** — GUI with 6 tabs (accessible from IBus menu or `--setup`)
2. **TOML Config File** — `~/.config/ibus-handwrite-chinese/config.toml`
3. **Environment Variables** — `IBUS_HANDWRITE_*` overrides (highest priority)
4. **Command-Line Arguments** — `--setup`, `--test`, `--ibus`, `--version`

---

## Preference Dialog

Open the preference dialog from:

- **IBus Menu**: Right-click IBus tray icon → Preferences → Chinese Handwriting
- **Command Line**: `ibus-engine-handwrite-chinese --setup`
- **Desktop Settings**: Search "Chinese Handwriting" in your settings panel

The dialog has 6 tabs:

| Tab | Purpose |
|-----|---------|
| **General** | Theme, logging |
| **Model** | Model tier, custom paths, download |
| **Engine** | Recognition & trackpad behavior |
| **Window** | Window size & layout |
| **User Dictionary** | Learning & boosting |
| **Shortcuts** | All keybindings |

Click **Apply** to save, then run `ibus restart` for changes to take effect.

---

## General Tab

| Setting | Config Key | Default | Description |
|---------|------------|---------|-------------|
| Theme | `general.theme` | `dark` | `dark` \| `light` \| `auto` (detects system theme) |
| Log Level | `general.log_level` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| Log Path | `general.log_path` | `/tmp/ppocr-recognition.log` | Recognition log file path |
| Log Max Size | `general.log_max_mb` | `5` | Max log file size in MB (0 = no rotation) |

**Environment Overrides:**
```bash
IBUS_HANDWRITE_THEME=light
IBUS_HANDWRITE_LOG_LEVEL=DEBUG
IBUS_HANDWRITE_LOG_PATH=/var/log/handwrite.log
```

---

## Model Tab

| Setting | Config Key | Default | Description |
|---------|------------|---------|-------------|
| Tier | `model.tier` | `small` | `tiny` (1.5M) \| `small` (8M) \| `medium` (34.5M) |
| Model Path | `model.path` | `""` | Custom `.onnx` path (empty = auto-detect) |
| Dict Path | `model.dict_path` | `""` | Custom `dict_v6.txt` path (empty = auto-detect) |
| Download Path | `model.download_path` | `/usr/local/share/ibus-handwrite-chinese/models` | Where models are stored |
| Auto-download | `model.auto_download` | `true` | Download missing models automatically |
| Download Timeout | `model.download_timeout` | `30` | Per-URL timeout in seconds |

**Environment Overrides:**
```bash
IBUS_HANDWRITE_PPOCR_MODEL=medium
IBUS_HANDWRITE_PPOCR_MODEL_PATH=/custom/model.onnx
IBUS_HANDWRITE_PPOCR_DICT_PATH=/custom/dict.txt
IBUS_HANDWRITE_DOWNLOAD_PATH=/opt/models
IBUS_HANDWRITE_AUTO_DOWNLOAD=false
IBUS_HANDWRITE_DOWNLOAD_TIMEOUT=60
```

### Model Tiers

| Tier | Parameters | Size | Use Case |
|------|------------|------|----------|
| tiny | 1.5M | ~6 MB | Fast, low-resource |
| small | ~8M | ~32 MB | Balanced (default) |
| medium | 34.5M | ~138 MB | Highest accuracy |

### Model Download

1. Select a tier from the dropdown
2. If not downloaded, a dialog prompts to download now
3. Click **Download Model** — progress bar pulses during download
4. Downloads to `/tmp` first, then moves to target (uses `pkexec` if needed)
5. Dictionary (`dict_v6.txt`) is shared across all tiers
6. Restart IBus after download: `ibus restart`

### Auto-detection Paths (in order)

```
$PROJECT_ROOT/data/models/ppocrv6_{tier}_rec.onnx
/usr/local/share/ibus-handwrite-chinese/models/ppocrv6_{tier}_rec.onnx
/tmp/models/ppocrv6_{tier}.onnx
```

---

## Engine Tab

| Setting | Config Key | Default | Range | Description |
|---------|------------|---------|-------|-------------|
| Stroke Width | `engine.stroke_width` | `8` | 1–20 | Stroke line width in pixels (display & recognition) |
| Page Size | `engine.page_size` | `8` | 4–20 | Candidates per page |
| Max Candidates | `engine.max_candidates` | `24` | 8–100 | Max candidates from recognition |
| Min Redraw (ms) | `engine.min_redraw_ms` | `16` | 8–100 | Throttle redraw during drawing |
| Momentum Decay | `engine.momentum_decay` | `0.65` | 0.0–1.0 | Velocity decay per tick |
| Momentum Threshold | `engine.momentum_threshold` | `0.3` | 0.0–1.0 | Stop momentum below this |
| Momentum Tick (ms) | `engine.momentum_tick_ms` | `50` | 10–200 | Momentum animation interval |
| Auto-pause Debounce (ms) | `engine.auto_pause_debounce_ms` | `50` | 10–500 | Delay before auto-pause on focus loss |
| Delete Hold (ms) | `engine.delete_hold_ms` | `500` | 100–2000 | Hold ⌫ to clear all + backspace |

**Environment Override:**
```bash
IBUS_HANDWRITE_STROKE_WIDTH=10
```

---

## Window Tab

| Setting | Config Key | Default | Range | Description |
|---------|------------|---------|-------|-------------|
| Width | `window.width` | `400` | 200–1200 | Window width in pixels |
| Height | `window.height` | `360` | 200–800 | Window height in pixels |
| Drawing Height | `window.drawing_height` | `300` | 100–600 | Drawing area height |
| Drag Handle Height | `window.drag_handle_height` | `24` | 10–50 | Top bar drag handle height |
| Candidate Button Width | `window.candidate_button_width` | `36` | 20–80 | Width of each candidate button |

---

## User Dictionary Tab

| Setting | Config Key | Default | Range | Description |
|---------|------------|---------|-------|-------------|
| Enabled | `user_dict.enabled` | `true` | on/off | Learn selected characters |
| Boost Strength | `user_dict.boost_strength` | `1.5` | 1.0–5.0 | Score multiplier for learned chars |
| Max Entries | `user_dict.max_entries` | `10000` | 100–100000 | SQLite database limit |

**Database Location:** `~/.local/share/ibus-handwrite-chinese/userdict.sqlite`

---

## Shortcuts Tab

All keybindings are customizable. Click a row to capture a new key.

| Action | Default | Description |
|--------|---------|-------------|
| Escape | `Escape` | Pause / close window |
| Commit | `Return` | Select first candidate |
| Delete Stroke | `BackSpace` | Undo last stroke (hold = clear all + backspace) |
| Page Up | `Left` | Previous candidate page |
| Page Down | `Right` | Next candidate page |
| Cycle Theme | `<Control><Shift>T` | Toggle dark/light/auto |
| Open Settings | `<Control><Shift>S` | Open preference dialog |

**Format:** GTK accelerator notation — `<Control><Shift>T`, `<Alt>Escape`, `F1`, etc.

---

## Configuration File

**Location:** `~/.config/ibus-handwrite-chinese/config.toml`

Only non-default values are written (keeps file clean). Example:

```toml
# ibus-handwrite-chinese configuration
# Auto-generated by handwrite_prefs.py

[general]
theme = "auto"
log_level = "DEBUG"

[model]
tier = "medium"
download_path = "/opt/my-models"

[engine]
stroke_width = 10
page_size = 10
momentum_decay = 0.7

[window]
width = 480
height = 420

[user_dict]
boost_strength = 2.0

[shortcuts]
escape = "Escape"
commit = "Return"
delete_stroke = "BackSpace"
page_up = "Left"
page_down = "Right"
cycle_theme = "<Control><Shift>T"
open_settings = "<Control><Shift>S"
```

---

## Environment Variables

All `IBUS_HANDWRITE_*` variables override the TOML config. Priority:

1. Environment variable (highest)
2. TOML config file
3. Built-in defaults (lowest)

| Variable | Config Key | Type |
|----------|------------|------|
| `IBUS_HANDWRITE_THEME` | `general.theme` | string |
| `IBUS_HANDWRITE_LOG_LEVEL` | `general.log_level` | string |
| `IBUS_HANDWRITE_LOG_PATH` | `general.log_path` | string |
| `IBUS_HANDWRITE_PPOCR_MODEL` | `model.tier` | string |
| `IBUS_HANDWRITE_PPOCR_MODEL_PATH` | `model.path` | string |
| `IBUS_HANDWRITE_PPOCR_DICT_PATH` | `model.dict_path` | string |
| `IBUS_HANDWRITE_DOWNLOAD_PATH` | `model.download_path` | string |
| `IBUS_HANDWRITE_AUTO_DOWNLOAD` | `model.auto_download` | bool |
| `IBUS_HANDWRITE_DOWNLOAD_TIMEOUT` | `model.download_timeout` | int |
| `IBUS_HANDWRITE_STROKE_WIDTH` | `engine.stroke_width` | int |

---

## Command-Line Arguments

```bash
ibus-engine-handwrite-chinese [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--ibus` | Run as IBus engine (default when launched by IBus) |
| `--setup` | Open preference dialog |
| `--test` | Standalone GTK window (no IBus) for testing |
| `--version` | Print version and exit |
| `--help` | Show help |

**Standalone Test Mode:**
```bash
/usr/local/share/ibus-handwrite-chinese/venv/bin/python3 \
  /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese --test
```
- Opens a GTK window without IBus
- Draw with mouse (trackpad not required)
- Recognition logged to `/tmp/ppocr-recognition.log`
- Window logs to `/tmp/hw.log`

---

## Trackpad Requirements

The engine uses **evdev** to read trackpad events directly. Your trackpad must support:

- `BTN_TOUCH` **or** `ABS_MT_TRACKING_ID` (finger-on-surface detection)
- `ABS_X` **or** `ABS_MT_POSITION_X` (X position)
- `ABS_Y` **or** `ABS_MT_POSITION_Y` (Y position)

**Tested Trackpads:**
- Acer Aspire AL16-54P (HTIX5288)
- MacBook Pro (bcm5974)

**Access Permission:**
The installer adds a udev rule (`/etc/udev/rules.d/99-trackpad-handwrite.rules`) granting `uaccess` to touchpad/trackpad devices. You must:

1. Add your user to the `input` group:
   ```bash
   sudo usermod -a -G input $USER
   ```
2. **Log out and back in** (or run `newgrp input`)

Verify with:
```bash
getfacl /dev/input/event*  # your user should have rw on trackpad device
```

If no evdev trackpad is available, the engine falls back to mouse drawing.

---

## Theme Auto-Detection

When `theme = "auto"` (default), the engine detects:

1. **GNOME/Unity**: `gsettings get org.gnome.desktop.interface color-scheme`
2. **KDE/Plasma**: `kreadconfig5 --file ~/.config/kdeglobals --group General --key ColorScheme`
3. **GTK_THEME** env var fallback
4. Default: `dark`

---

## Reset to Defaults

- **Preference Dialog**: Click "Reset to Defaults" button
- **Command Line**: Delete the config file:
  ```bash
  rm ~/.config/ibus-handwrite-chinese/config.toml
  ibus restart
  ```

---

## Advanced: Direct Config Editing

Edit `~/.config/ibus-handwrite-chinese/config.toml` directly with any text editor. Changes take effect after `ibus restart`.

The config is loaded by `handwrite_config.py` which:
- Uses `tomllib` (Python 3.11+) or `tomli` backport
- Merges file config with defaults
- Applies environment overrides last
- Resolves `"auto"` theme via system detection