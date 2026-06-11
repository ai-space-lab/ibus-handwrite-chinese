# IBus Chinese Handwriting Input Method

A Chinese handwriting input method for Linux with a macOS-style floating panel, evdev touchpad integration, and Zinnia-based recognition.

![screenshot](screenshot.png)

## Features

- **macOS-style popup**: dark semi-translucent floating window with embedded candidates at the top
- **evdev touchpad input**: draw characters on your laptop's touchpad — works on any touchpad with BTN_TOUCH + ABS_X/ABS_MT_POSITION_X support (all modern Synaptics, ELAN, ALPS, and bcm5974 touchpads)
- **Tap to select**: quickly tap on the touchpad to pick a candidate — spatial mapping matches candidate position
- **Two-finger swipe**: swipe left/right with two fingers to page through candidates
- **Delete stroke**: ⌫ button to undo the last stroke
- **ESC state machine**: one ESC pauses (ungrab touchpad, dim window), another ESC closes; click the window to resume
- **Cursor-proximity positioning**: popup appears near the text cursor, not at a fixed screen position
- **Drag handle**: custom drag handle at the bottom to reposition the window
- **Mouse fallback**: if no evdev touchpad is available, draw with the mouse

## Requirements

- Debian 12 / Ubuntu 24.04 / Linux Mint 22 or similar
- A laptop with a touchpad (or a touchscreen)
- IBus input method framework (default on most Linux desktops)

## Quick Install

```bash
sudo apt install python3-evdev tegaki-zinnia-simplified-chinese
git clone https://github.com/vinceyap88/ibus-handwrite-chinese
cd ibus-handwrite-chinese
sudo ./install.sh
ibus restart
```

Then switch the engine:

```bash
ibus engine handwrite-chinese-simplified   # Simplified Chinese
ibus engine handwrite-chinese-traditional  # Traditional Chinese
```

Or select **Chinese Handwriting (Simplified)** or **Chinese Handwriting (Traditional)** from your desktop's IBus menu.

## Usage

1. Switch to **Chinese Handwriting (Simplified)** or **Chinese Handwriting (Traditional)** from your IBus menu
2. A dark floating panel appears near your text cursor
3. Draw Chinese characters on your laptop's touchpad with one finger
4. Candidate characters appear at the top of the panel
5. Tap on the touchpad to select a candidate (spatial mapping)
6. Use two-finger swipe left/right to page through candidates
7. Press **⌫** to undo the last stroke
8. **ESC** once to pause (window dims), **ESC** again to close
9. Click the window to resume after pausing

## Troubleshooting

- **Touchpad not accessible**: Run `sudo udevadm trigger` to apply the udev rule, or add your user to the `input` group: `sudo usermod -a -G input $USER && reboot`
- **IBus not seeing the engine**: Run `ibus restart` after installation
- **Engine won't start**: Check `journalctl -f` while switching to the engine for error messages
- **Permission denied**: Verify with `getfacl /dev/input/event*` — your user should have `rw` access on the touchpad device

## Known Limitations

- Only verified on MacBook Pro (bcm5974). Should work on any touchpad with BTN_TOUCH + ABS_X, but untested on other hardware.
- Zinnia uses a 2009 handwriting recognition model — accuracy is limited for complex characters. See [accuracy-improvement-plan](https://github.com/vinceyap88/ibus-handwrite-chinese/wiki) for potential improvements.
- No multi-character composition yet (you write one character at a time). V2 may add spatial segmentation for sequential character input.

## License

GPLv3 — required by dependencies (libzinnia, python3-evdev, ibus).

## Traditional Chinese

The engine supports both Simplified and Traditional Chinese as separate IBus engines. After installing, select from your IBus menu or switch with:

```bash
ibus engine handwrite-chinese-simplified   # Simplified (zh_CN model, 6763 chars)
ibus engine handwrite-chinese-traditional  # Traditional (zh_TW model, 11853 chars)
```

Both engines can be added to your input sources simultaneously — switch between them like any two input methods.

## Files

| File | Purpose |
|------|---------|
| `ibus-engine-handwrite-chinese` | Main engine (Python, Zinnia ctypes, GTK popup, evdev integration) |
| `handwrite_evdev.py` | Evdev multitouch reader module |
| `handwrite-chinese.xml` | IBus component registration |
| `99-trackpad-handwrite.rules` | Udev rule for touchpad access |
| `install.sh` | One-command install script |
| `restore.sh` | Rollback/restore script |
