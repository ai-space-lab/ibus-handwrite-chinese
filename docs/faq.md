# Frequently Asked Questions

## Installation

### Q: Which installation method should I use?

**Quick answer:** Use the one-command bootstrap:

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh)
ibus restart
```

It auto-detects your distro (Debian/Ubuntu/Mint, Fedora, Arch/Manjaro, openSUSE) and installs everything.

**Other options:**
- **Pre-built packages**: Download `.deb` / `.rpm` from [GitHub Releases](https://github.com/ai-space-lab/ibus-handwrite-chinese/releases)
- **Build from source**: Clone the repo and run `./tools/install.sh`

---

### Q: My distro isn't listed. Will it work?

The bootstrap script supports:
- Debian 12+, Ubuntu 22.04+, Linux Mint 21+
- Fedora 40+
- Arch Linux, Manjaro
- openSUSE Tumbleweed

Other distros may work if they have:
- IBus 1.5+
- Python 3.8+ with `python3-venv`
- `python3-evdev` (or equivalent)
- GTK3, Cairo, GObject Introspection

Try the bootstrap script — it will tell you what's missing.

---

### Q: Do I need to build the ONNX model myself?

No. The installer downloads pre-built PP-OCRv6 ONNX models from HuggingFace (with hf-mirror.com fallback). Three tiers are available: tiny (1.5M params), small (~8M), medium (34.5M).

---

### Q: Installation fails with "python3-evdev not found"

Install the system package first:

```bash
# Debian/Ubuntu/Mint
sudo apt install python3-evdev

# Fedora
sudo dnf install python3-evdev

# Arch/Manjaro
sudo pacman -S python-evdev

# openSUSE
sudo zypper install python3-evdev
```

Then re-run the installer with `--skip-deps`:
```bash
./tools/install.sh --skip-deps
```

---

### Q: Can I install without sudo?

No. The engine needs:
- System-wide IBus component registration (`/usr/share/ibus/component/`)
- Udev rule for trackpad access (`/etc/udev/rules.d/`)
- Model files in `/usr/local/share/ibus-handwrite-chinese/models/`
- Python venv with onnxruntime in `/usr/local/share/ibus-handwrite-chinese/venv/`

All require root. The bootstrap script uses `sudo` internally.

---

## Trackpad & Hardware

### Q: Will it work on my trackpad?

**Tested & working:**
- Acer Aspire AL16-54P (HTIX5288)
- MacBook Pro (bcm5974)

**Should work on any trackpad with:**
- `BTN_TOUCH` or `ABS_MT_TRACKING_ID` (finger detection)
- `ABS_X`/`ABS_MT_POSITION_X` and `ABS_Y`/`ABS_MT_POSITION_Y` (position)

Run the diagnostic to check:
```bash
/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh
```

---

### Q: My trackpad isn't detected / "No trackpad detected"

1. **Check the diagnostic:**
   ```bash
   /usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh
   ```

2. **Verify udev rule is applied:**
   ```bash
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```

3. **Check group membership:**
   ```bash
   groups | grep input
   # If missing: sudo usermod -a -G input $USER && reboot
   ```

4. **Verify device ACL:**
   ```bash
   getfacl /dev/input/event*
   # Your user should have rw on the trackpad device
   ```

5. **Some trackpads need a physical click** to register touches. The engine now also tracks `ABS_MT_TRACKING_ID` — try touching lightly without clicking.

---

### Q: Does it work on Wayland?

**Popup positioning and evdev access are untested on Wayland.** The engine uses X11-specific APIs for cursor-proximity window positioning. On Wayland:
- Window may appear at wrong position
- evdev access may be blocked by compositor

**Workaround:** Run on X11 session (log out → select "Xorg" / "X11" at login).

---

### Q: Can I use a touchscreen instead of trackpad?

The engine reads evdev events. If your touchscreen exposes the same event codes (`ABS_MT_POSITION_X/Y`, `ABS_MT_TRACKING_ID`), it may work. Not officially tested.

---

### Q: Does it work with external drawing tablets (Wacom, etc.)?

Only if the tablet appears as a standard evdev touchpad device with the required event codes. Most drawing tablets use different event types and won't work without modification.

---

## Usage

### Q: How do I switch to Chinese Handwriting?

- **IBus Menu**: Click tray icon → Chinese Handwriting
- **Keyboard**: `Super+Space` (or your configured IBus trigger)
- **Command**: `ibus engine handwrite-chinese`

---

### Q: How do I draw characters?

1. Switch to Chinese Handwriting IME
2. Floating panel appears near text cursor
3. **Draw with one finger** on trackpad
4. Candidates appear at top of panel
5. **Tap trackpad** to select candidate (spatial mapping)
6. **Two-finger swipe** left/right to page candidates
7. **Fast swipe** = momentum (advances multiple pages)
8. **Drag finger in top 5%** of trackpad to highlight candidate by position
9. **⌫ button** = undo last stroke
10. **× button** = close & restore previous IME

---

### Q: What do the keyboard shortcuts do?

| Key | Action |
|-----|--------|
| `ESC` (once) | Pause panel, show "click to resume" |
| `ESC` (twice) | Close panel, restore previous IME |
| `Enter` (with candidates) | Commit first candidate |
| `Enter` (no candidates) | Pass through to app |
| `Backspace` | Undo last stroke |
| `Backspace` (hold 500ms) | Clear all strokes + send backspace to app |
| `Left` / `Right` | Page candidates |
| `Ctrl+Shift+T` | Cycle theme |
| `Ctrl+Shift+S` | Open settings |

All shortcuts are customizable in the **Shortcuts** tab.

---

### Q: How does tap-to-select work?

Tap anywhere on the trackpad. The X position maps spatially to candidates:
- Left side → first candidate
- Right side → last candidate
- Far right (82%+) → triggers ⌫ (delete stroke)

---

### Q: How does two-finger swipe paging work?

- **Swipe left** → next page
- **Swipe right** → previous page
- **Fast swipe** → momentum: continues paging after lift, decelerating
- Velocity and decay configurable in **Engine** tab

---

### Q: Can I type normally (English) while the panel is open?

**Yes.** When no strokes are drawn (no candidates), `Enter` passes through to the application. You can type English normally. The panel only intercepts keys when actively writing.

---

### Q: How do I close the panel?

- Click **×** button (top-left)
- Press **ESC** twice
- Switch to another IME from IBus menu

The previous IME is automatically restored.

---

### Q: What is "Paused" mode?

Press **ESC** once → panel shows "click to resume" overlay, trackpad ungrabbed. Click the panel or press **ESC** again to close. Useful for temporarily using trackpad for cursor movement.

---

## Models & Recognition

### Q: Which model tier should I use?

| Tier | Speed | Accuracy | Best For |
|------|-------|----------|----------|
| tiny | Fastest | Good | Low-end hardware, battery saving |
| small | Balanced | Very Good | **Default** — most users |
| medium | Slowest | Best | High accuracy needs, powerful hardware |

The **small** tier (default) achieves >99% top-1 accuracy on common characters.

---

### Q: How do I change the model tier?

1. Open preferences: `ibus-engine-handwrite-chinese --setup`
2. Go to **Model** tab
3. Select tier from dropdown
4. If not downloaded, click **Download Model** (or accept prompt)
5. Click **Apply**
6. Run `ibus restart`

---

### Q: Model download fails / "Permission denied"

The downloader uses `/tmp` for temporary files, then moves to target with `pkexec` if needed. If it fails:

1. **Manual download:**
   ```bash
   # Download from HuggingFace
   wget https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/main/inference.onnx
   wget https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt
   
   # Install
   sudo mkdir -p /usr/local/share/ibus-handwrite-chinese/models
   sudo cp inference.onnx /usr/local/share/ibus-handwrite-chinese/models/ppocrv6_small_rec.onnx
   sudo cp dict_v6.txt /usr/local/share/ibus-handwrite-chinese/models/dict_v6.txt
   ```

2. **Or set custom path** in Model tab → "Model Path" / "Dict Path"

---

### Q: Can I use my own ONNX model?

Yes. In the **Model** tab:
- **Model Path**: Path to your `.onnx` file
- **Dict Path**: Path to your dictionary `.txt` (one char per line, matching model vocab)

Leave empty for auto-detection. The model must be compatible with PP-OCRv6 architecture (CNN + CTC, 48px height input).

---

### Q: Recognition accuracy is poor. What can I do?

1. **Use medium tier** for highest accuracy
2. **Draw larger, clearer strokes** — small/cramped strokes reduce accuracy
3. **Check stroke width** in Engine tab (default 8px, try 10–12)
4. **Enable User Dictionary** — learned characters get boosted
5. **Verify model matches dict** — they must be from same PP-OCRv6 version

---

## Configuration

### Q: Where is the config file?

`~/.config/ibus-handwrite-chinese/config.toml`

Only non-default values are stored. Delete it to reset.

---

### Q: How do I override settings via environment variables?

Prefix with `IBUS_HANDWRITE_` and use uppercase with underscores:

```bash
IBUS_HANDWRITE_THEME=light
IBUS_HANDWRITE_PPOCR_MODEL=medium
IBUS_HANDWRITE_STROKE_WIDTH=10
ibus restart
```

See [Configuration](configure.md#environment-variables) for full list.

---

### Q: Can I have different settings per user?

Yes. Each user has their own:
- Config: `~/.config/ibus-handwrite-chinese/config.toml`
- User dictionary: `~/.local/share/ibus-handwrite-chinese/userdict.sqlite`
- Log: `/tmp/ppocr-recognition.log` (shared)

System-wide model files in `/usr/local/share/...` are shared.

---

### Q: How do I backup/restore my settings?

```bash
# Backup
cp ~/.config/ibus-handwrite-chinese/config.toml ~/config-backup.toml
cp ~/.local/share/ibus-handwrite-chinese/userdict.sqlite ~/userdict-backup.sqlite

# Restore
cp ~/config-backup.toml ~/.config/ibus-handwrite-chinese/config.toml
cp ~/userdict-backup.sqlite ~/.local/share/ibus-handwrite-chinese/userdict.sqlite
ibus restart
```

---

## Troubleshooting

### Q: "Cannot find engine handwrite-chinese"

```bash
ibus restart
ibus engine handwrite-chinese
```

The engine component XML must be registered at `/usr/share/ibus/component/handwrite-chinese.xml` (done by installer).

---

### Q: Trackpad doesn't work / "Permission denied"

See [Trackpad not detected](#q-my-trackpad-isnt-detected--no-trackpad-detected) above. Key steps:
1. `sudo usermod -a -G input $USER && reboot`
2. `sudo udevadm trigger`
3. Verify with `getfacl /dev/input/event*`

---

### Q: ESC key doesn't work in Firefox

Fixed in v0.6.0. Firefox sends ESC with `IBUS_RELEASE_MASK`. The engine now handles ESC regardless of press/release state with a 150ms debounce.

If still broken:
```bash
# Check for stale root ibus-daemon
sudo pkill -u root ibus-daemon
ibus restart
```

---

### Q: Enter key doesn't reach terminal after pressing ESC

Fixed in v0.6.0. Enter now passes through when:
- No candidates exist
- Panel is paused (after first ESC)

Update to latest version.

---

### Q: Panel doesn't appear / window not showing

1. Check IBus is running: `ibus-daemon --daemonize --replace`
2. Check engine registered: `ibus list-engine | grep handwrite`
3. Run manually to see errors:
   ```bash
   /usr/local/share/ibus-handwrite-chinese/venv/bin/python3 \
     /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese --test
   ```

---

### Q: onnxruntime errors on startup

The installer creates a Python venv with onnxruntime. If it failed:

```bash
sudo python3 -m venv --system-site-packages /usr/local/share/ibus-handwrite-chinese/venv
sudo /usr/local/share/ibus-handwrite-chinese/venv/bin/pip install onnxruntime tomli
```

Then `ibus restart`.

---

### Q: IBus indicator not showing in panel

```bash
# Restart IBus
ibus-daemon --daemonize --replace

# Cinnamon: ensure panel shows
gsettings set org.freedesktop.ibus.panel show 1
```

---

### Q: Ctrl+Space / IBus trigger not working

1. Check trigger shortcut: `ibus-setup` or `dconf read /desktop/ibus/general/hotkey/trigger`
2. Kill stale root daemon: `sudo pkill -u root ibus-daemon`
3. Restart: `ibus restart`

---

## Uninstallation

### Q: How do I uninstall?

```bash
/usr/local/share/ibus-handwrite-chinese/restore.sh
```

This removes:
- Engine binary & wrapper
- IBus component XML
- Udev rule
- Model files & venv
- Optionally: user config & dictionary

Then `ibus restart`.

---

### Q: Will uninstall remove my learned characters?

Only if you confirm at the prompt. By default, user data is **preserved**.

---

## Development & Testing

### Q: How do I test without installing?

```bash
# From repo root
python3 src/ibus-engine-handwrite-chinese --test
```

Opens standalone GTK window with mouse drawing. No IBus required.

---

### Q: How do I collect handwriting data for analysis?

```bash
# Interactive collection
python3 scripts/collect_ppocr_data.py --help

# Single capture
python3 scripts/capture_one.py

# Batch collection (uses --test mode logs)
python3 scripts/gtk_collect_loop.py
```

See `scripts/` directory for analysis tools.

---

### Q: Where are logs stored?

| Log | Path |
|-----|------|
| Recognition | `/tmp/ppocr-recognition.log` (configurable) |
| Window events | `/tmp/hw.log` |
| Engine debug | `journalctl -u ibus` or run manually |

Set log level to `DEBUG` in General tab for more detail.

---

## License & Credits

### Q: What license?

**GPLv3** — required by dependencies (`python3-evdev`, IBus).

### Q: What models are used?

**PP-OCRv6** by PaddlePaddle/Baidu — Apache 2.0 license. Downloaded from HuggingFace at runtime, not bundled.

### Q: How can I contribute?

- Report issues on GitHub
- Submit PRs for bug fixes
- Test on new hardware/distros
- Improve documentation
- Donate via USDC addresses in README

---

## Still Have Questions?

- **GitHub Issues**: [Report a bug](https://github.com/ai-space-lab/ibus-handwrite-chinese/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ai-space-lab/ibus-handwrite-chinese/discussions)
- **Diagnostic Script**: Run `/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh` and include output in bug reports