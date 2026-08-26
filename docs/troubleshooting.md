# Troubleshooting

## Quick Diagnostic

Run the built-in diagnostic script:

```bash
/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh
```

Output includes:
- Trackpad detection results
- Input group membership
- Udev rule status
- IBus engine registration
- ESC key routing test

Include this output when reporting issues.

---

## Trackpad Issues

### Trackpad not detected / "No trackpad detected by current filter"

**Symptoms:** Engine falls back to mouse; trackpad drawing doesn't work.

**Causes & Fixes:**

1. **Udev rule not applied**
   ```bash
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```

2. **User not in `input` group**
   ```bash
   sudo usermod -a -G input $USER
   # Log out and back in (or: newgrp input)
   ```

3. **Verify device ACL**
   ```bash
   getfacl /dev/input/event*
   # Your user should have rw on trackpad device
   ```

4. **Trackpad requires physical click**
   - Some trackpads only register touches after a click
   - Engine now also tracks `ABS_MT_TRACKING_ID` — try light touch
   - If still requires click, firmware sensitivity may need adjustment

5. **Wrong device matched**
   - Diagnostic shows all input devices
   - Udev rule matches: `*[Tt]ouchpad*`, `*[Tt]rackpad*`, `*bcm5974*`
   - If your trackpad has different name, add a rule:
     ```bash
     # /etc/udev/rules.d/99-trackpad-handwrite.rules
     SUBSYSTEM=="input", KERNEL=="event*", ATTRS{name}=="*YourTrackpadName*", TAG+="uaccess"
     ```

---

### Trackpad works but drawing is offset / wrong coordinates

**Symptoms:** Strokes appear in wrong position relative to finger.

**Fixes:**
1. **Restart IBus** — `ibus restart`
2. **Check HiDPI scale** — `GDK_SCALE` env var or GTK monitor scale factor
3. **Run diagnostic** — verify trackpad resolution matches screen

---

### "Permission denied" opening trackpad device

**Symptoms:** Engine starts but trackpad events not received; errors in `/tmp/hw.log`.

**Fix:**
```bash
# Immediate fix (current session)
sudo chmod 666 /dev/input/eventXX  # replace XX with your trackpad event number

# Permanent fix
sudo usermod -a -G input $USER
# Log out and back in
```

---

## IBus Integration Issues

### "Cannot find engine handwrite-chinese"

**Symptoms:** `ibus engine handwrite-chinese` fails; not in IBus menu.

**Fixes:**
```bash
# 1. Restart IBus
ibus restart

# 2. Verify component XML exists
ls -la /usr/share/ibus/component/handwrite-chinese.xml

# 3. Check engine registration
ibus list-engine | grep handwrite

# 4. If missing, reinstall
./tools/install.sh --skip-deps
```

---

### Engine won't start / crashes on activation

**Symptoms:** Panel doesn't appear; IBus switches back to previous IME.

**Debug:**
```bash
# Run engine manually to see errors
/usr/local/share/ibus-handwrite-chinese/venv/bin/python3 \
  /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese --test

# Check logs
tail -f /tmp/hw.log
tail -f /tmp/ppocr-recognition.log
```

**Common causes:**
1. **onnxruntime not installed in venv**
   ```bash
   sudo /usr/local/share/ibus-handwrite-chinese/venv/bin/pip install onnxruntime tomli
   ```

2. **Model file missing**
   ```bash
   ls -la /usr/local/share/ibus-handwrite-chinese/models/
   # Should have ppocrv6_*_rec.onnx and dict_v6.txt
   ```

3. **GTK/Cairo import error**
   ```bash
   sudo apt install python3-gi-cairo gir1.2-gtk-3.0  # Debian/Ubuntu
   ```

---

### IBus indicator not showing in panel

**Fixes:**
```bash
# Restart IBus daemon
ibus-daemon --daemonize --replace

# Cinnamon: force show
gsettings set org.freedesktop.ibus.panel show 1

# GNOME: check IBus is in startup applications
```

---

### Ctrl+Space / IBus trigger not working

**Symptoms:** Can't switch IME with keyboard shortcut.

**Fixes:**
```bash
# 1. Check trigger shortcut
ibus-setup
# Or:
dconf read /desktop/ibus/general/hotkey/trigger

# 2. Kill stale root-owned ibus-daemon (intercepts keys)
sudo pkill -u root ibus-daemon
ibus restart

# 3. Verify user ibus-daemon is running
pgrep -u $USER ibus-daemon
```

---

### "Stale root ibus-daemon" warning during install

**Symptoms:** Install script warns: "Could not kill root ibus-daemon. ESC may not work."

**Fix:**
```bash
sudo pkill -9 -u root ibus-daemon
ibus-daemon --daemonize --replace
```

Root-owned ibus-daemon intercepts key events before they reach your session's IBus.

---

## Key Event Issues

### ESC key doesn't work (especially in Firefox)

**Symptoms:** Pressing ESC doesn't pause/close panel.

**Root cause:** Firefox sends ESC with `IBUS_RELEASE_MASK` (1<<30). Fixed in v0.6.0.

**Fixes:**
1. **Update to v0.6.0+**
2. **Kill root ibus-daemon:**
   ```bash
   sudo pkill -u root ibus-daemon
   ibus restart
   ```
3. **Check ESC binding** in Shortcuts tab — should be `Escape`

**Debug:** Watch `/tmp/hw.log`:
```
on_key_esc: _state=0  # ESC pressed in active state → should pause
on_key_esc: _state=1  # ESC pressed in paused state → should close
```

---

### Enter key doesn't reach application after ESC

**Symptoms:** After pressing ESC to pause, Enter key is consumed by engine.

**Fixed in v0.6.0.** Enter now passes through when:
- No candidates exist
- Panel is paused (state 1)

**Workaround for older versions:** Press ESC twice to fully close panel.

---

### Backspace doesn't delete text in application

**Symptoms:** Backspace only clears strokes, doesn't send backspace to app.

**Behavior:** 
- Tap Backspace → undo last stroke
- Hold Backspace (500ms default) → clear all strokes + send backspace to app

**Adjust hold time** in Engine tab: `Delete Hold (ms)`

---

### Shortcuts not working / wrong keys

**Fixes:**
1. Check **Shortcuts** tab in preferences — customize bindings
2. Verify no conflict with desktop/global shortcuts
3. Reset to defaults: "Reset All to Defaults" button

---

## Window / Display Issues

### Panel doesn't appear / window not showing

**Symptoms:** Engine activates but no floating panel.

**Debug:**
```bash
# Run test mode
/usr/local/share/ibus-handwrite-chinese/venv/bin/python3 \
  /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese --test

# Check window focus logs
tail -f /tmp/hw.log | grep -i focus
```

**Fixes:**
1. **Restart IBus:** `ibus restart`
2. **Check for Wayland** — positioning untested on Wayland; use X11 session
3. **Kill root ibus-daemon:** `sudo pkill -u root ibus-daemon`
4. **Run with `--test`** to verify GTK window works

---

### Window appears at wrong position

**Symptoms:** Panel not near text cursor.

**Causes:**
- **Wayland**: Cursor proximity positioning uses X11 APIs
- **No cursor location**: Falls back to primary monitor center
- **Active window detection failed**: Falls back to cursor or center

**Workaround:** Drag panel by handle to reposition. Position persists per session.

---

### Panel appears but trackpad/mouse doesn't draw

**Symptoms:** Window visible but no strokes appear.

**Fixes:**
1. **Check trackpad started:** `/tmp/hw.log` should show trackpad init
2. **Verify window has focus** for mouse fallback (click in drawing area)
3. **Check evdev reader:** Run diagnostic script

---

### Theme not applying / wrong colors

**Fixes:**
1. **Restart IBus** after theme change: `ibus restart`
2. **Check `theme` config:** `dark`, `light`, or `auto`
3. **Auto-detection:** Requires `gsettings` (GNOME) or `kreadconfig5` (KDE)
4. **Force theme via env:**
   ```bash
   IBUS_HANDWRITE_THEME=light ibus restart
   ```

---

## Model / Recognition Issues

### "PP-OCRv6 model not found" error

**Symptoms:** Engine fails to start; logs show model not found.

**Fixes:**
1. **Auto-download via preferences:**
   - Open preferences: `ibus-engine-handwrite-chinese --setup`
   - Model tab → select tier → click **Download Model**
   - Restart IBus

2. **Manual download:**
   ```bash
   # Create directory
   sudo mkdir -p /usr/local/share/ibus-handwrite-chinese/models
   
   # Download model (example: small tier)
   wget https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/main/inference.onnx
   wget https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt
   
   # Install
   sudo cp inference.onnx /usr/local/share/ibus-handwrite-chinese/models/ppocrv6_small_rec.onnx
   sudo cp dict_v6.txt /usr/local/share/ibus-handwrite-chinese/models/dict_v6.txt
   ```

3. **Set custom paths** in Model tab if stored elsewhere

---

### Model download fails / "Permission denied"

**Symptoms:** Download button spins but fails; error in dialog.

**Cause:** Target directory (`/usr/local/share/.../models/`) is root-owned.

**Fix:** The downloader uses `/tmp` + `pkexec cp`. If `pkexec` fails:
```bash
# Manual copy after download to /tmp
sudo cp /tmp/inference.onnx /usr/local/share/ibus-handwrite-chinese/models/ppocrv6_small_rec.onnx
sudo cp /tmp/dict.txt /usr/local/share/ibus-handwrite-chinese/models/dict_v6.txt
```

Or set `model.download_path` to a user-writable directory.

---

### Poor recognition accuracy

**Symptoms:** Wrong characters recognized; low confidence scores.

**Improvements:**
| Setting | Try |
|---------|-----|
| Model tier | Upgrade to `medium` |
| Stroke width | Increase to 10–12 (Engine tab) |
| Draw larger | Use more trackpad area |
| Slower strokes | Reduce speed for clarity |
| User dictionary | Enable + use frequently |

**Debug:** Check `/tmp/ppocr-recognition.log` for confidence scores:
```json
{"time": "2024-01-15T10:30:00", "level": "INFO", "msg": "decode: top5=[[\"一\", 0.99], [\"二\", 0.01]] ..."}
```

---

### onnxruntime errors / "Failed to load model"

**Symptoms:** Engine crashes on recognition; Python traceback mentions onnxruntime.

**Fixes:**
```bash
# Reinstall onnxruntime in venv
sudo /usr/local/share/ibus-handwrite-chinese/venv/bin/pip install --force-reinstall onnxruntime

# Or use system Python if venv broken
# Edit /usr/local/bin/ibus-engine-handwrite-chinese wrapper to use /usr/bin/python3
```

**Note:** onnxruntime version must be compatible with PP-OCRv6 ONNX model (tested with onnxruntime 1.16+).

---

## User Dictionary Issues

### User dictionary not learning / not boosting

**Symptoms:** Selected characters don't appear more frequently.

**Fixes:**
1. **Check enabled:** User Dictionary tab → "Enable user dictionary" checked
2. **Check database:** `~/.local/share/ibus-handwrite-chinese/userdict.sqlite` exists
3. **View stats:** User Dictionary tab shows "Learned characters: N"
4. **Reset if corrupted:**
   ```bash
   rm ~/.local/share/ibus-handwrite-chinese/userdict.sqlite
   ibus restart
   ```

---

### "User dictionary database locked"

**Symptoms:** Errors about SQLite lock.

**Fix:** Only one engine instance should run. Kill duplicates:
```bash
pkill -f ibus-engine-handwrite-chinese
ibus restart
```

---

## Configuration Issues

### Settings not taking effect

**Symptoms:** Changed preferences but behavior unchanged.

**Fixes:**
1. **Click Apply** in preferences dialog
2. **Restart IBus:** `ibus restart`
3. **Check env overrides:** `IBUS_HANDWRITE_*` variables take precedence over config file
   ```bash
   env | grep IBUS_HANDWRITE
   ```

---

### Config file corrupted / engine won't start

**Fix:** Delete config file to reset:
```bash
rm ~/.config/ibus-handwrite-chinese/config.toml
ibus restart
```

---

### Environment variables not working

**Checklist:**
- Variable name: `IBUS_HANDWRITE_` prefix (uppercase, underscores)
- Exported: `export IBUS_HANDWRITE_THEME=light` or set in shell rc file
- Restarted IBus after change: `ibus restart`
- Type matches: integers for numeric, `true/false` for bool

---

## Wayland-Specific Issues

### Window positioning broken on Wayland

**Status:** Untested/unsupported. Engine uses X11 APIs for cursor-proximity positioning.

**Workaround:** Use X11 session (select "Xorg" / "X11" at login).

---

### Trackpad access blocked on Wayland

**Status:** Wayland compositors may block evdev access for security.

**Workaround:** Use X11 session. Or configure compositor to allow evdev (compositor-specific).

---

### IBus not working on Wayland

**Status:** IBus Wayland support varies by compositor.

**Workaround:** Use X11 session. Ensure `ibus-daemon` runs with `--xim` for X11 apps.

---

## Installation/Update Issues

### Install script fails on non-Debian distro

**Symptoms:** `apt` not found; dependency install skipped.

**Fix:** Install dependencies manually, then run with `--skip-deps`:
```bash
# Fedora
sudo dnf install python3-evdev python3-venv python3-gobject cairo-gobject

# Arch
sudo pacman -S python-evdev python-gobject cairo

# openSUSE
sudo zypper install python3-evdev python3-venv python3-gobject python3-cairo

# Then
./tools/install.sh --skip-deps
```

---

### Model download fails in CI / headless environment

**Symptoms:** `wget` fails; no display.

**Fix:** The bootstrap script detects CI and skips trackpad detection. For model download in CI:
```bash
# Set tier and run download manually
IBUS_HANDWRITE_PPOCR_MODEL=small python3 -c "
import handwrite_model_download
handwrite_model_download.ensure_model({
    'tier': 'small',
    'download_path': '/tmp/models',
    'auto_download': True,
    'download_timeout': 60
})
"
```

---

### Package install fails (dpkg/rpm)

**Fixes:**
```bash
# Debian/Ubuntu: fix broken deps
sudo dpkg -i package.deb
sudo apt install -f

# Fedora/openSUSE: verify dependencies
sudo rpm -i package.rpm
# Or:
sudo dnf install ./package.rpm  # pulls deps
```

---

## Uninstallation Issues

### Restore script fails / files not removed

**Manual cleanup:**
```bash
sudo rm -f /usr/local/bin/ibus-engine-handwrite-chinese
sudo rm -f /usr/local/bin/handwrite_evdev.py
sudo rm -f /usr/share/ibus/component/handwrite-chinese.xml
sudo rm -f /etc/udev/rules.d/99-trackpad-handwrite.rules
sudo rm -rf /usr/local/share/ibus-handwrite-chinese
sudo udevadm control --reload-rules
ibus restart
```

---

### User data not removed

**By design:** Restore script prompts before removing user data. To fully remove:
```bash
rm -rf ~/.config/ibus-handwrite-chinese
rm -rf ~/.local/share/ibus-handwrite-chinese
```

---

## Getting Help

### Before Reporting an Issue

1. **Run diagnostic:**
   ```bash
   /usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh > diag.txt 2>&1
   ```

2. **Collect logs:**
   ```bash
   cp /tmp/hw.log ~/hw.log
   cp /tmp/ppocr-recognition.log ~/ppocr.log
   ```

3. **Note:**
   - Distro & version (`lsb_release -a` or `cat /etc/os-release`)
   - Desktop environment (GNOME, KDE, XFCE, etc.)
   - Session type: `echo $XDG_SESSION_TYPE` (x11/wayland)
   - Trackpad model: `cat /proc/bus/input/devices | grep -A5 Touchpad`

### Where to Report

- **GitHub Issues**: [https://github.com/ai-space-lab/ibus-handwrite-chinese/issues](https://github.com/ai-space-lab/ibus-handwrite-chinese/issues)
- Include: diagnostic output, logs, distro/DE, steps to reproduce

### Useful Commands for Debugging

```bash
# Engine version
/usr/local/share/ibus-handwrite-chinese/venv/bin/python3 \
  /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese --version

# List IBus engines
ibus list-engine

# Current engine
ibus engine

# IBus status
ibus-daemon --version

# Check evdev devices
python3 -c "import evdev; [print(d.path, d.name) for d in [evdev.InputDevice(p) for p in evdev.list_devices()]]"

# Test trackpad grab
python3 -c "
import evdev
for p in evdev.list_devices():
    d = evdev.InputDevice(p)
    if 'touchpad' in d.name.lower() or 'trackpad' in d.name.lower():
        print('Found:', d.path, d.name)
        try:
            d.grab()
            print('Grab OK')
            d.ungrab()
        except Exception as e:
            print('Grab failed:', e)
        d.close()
"
```