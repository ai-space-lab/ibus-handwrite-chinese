# Plan: Restore previous IBus engine on Esc×2 (Completed)

## Problem
Pressing Esc×2 to close the handwriting window hides the GTK popup but leaves the handwriting engine active in IBus. The IBus panel icon stays on "写" instead of returning to "EN".

## Root Cause
`HandwriteWin.on_key_esc()` calls `_do_disable()` which only stops the trackpad and hides the window — it never calls `set_global_engine()` to switch back to the English keyboard.

## Changes

### Change 1: `restore_previous_engine()` in `HandwriteEngine`
Reads `preload-engines` via `Gio.Settings`, finds first non-handwriting engine, calls `IBus.Bus.set_global_engine()`. Falls back to `xkb:us::eng`.

### Change 2: Call from `HandwriteWin.on_key_esc()`
After `self._do_disable()`, calls `self.engine.restore_previous_engine()`.

### Change 3: Pause overlay instead of opacity
`Gtk.Window.set_opacity` is deprecated AND broken in GTK 3.24 (no-op). Replaced with a Cairo-drawn "Paused – click to resume" overlay on the drawing area during pause mode (`_state == 1`).

### Change 4: `_write_log` added to `HandwriteWin`
`on_key_esc()` was silently failing because `_write_log()` was only defined on `HandwriteEngine`, not `HandwriteWin`. The `AttributeError` killed the entire method before any state changes took effect.

### Change 5: RELEASE_MASK filtering
`IBus.Engine.do_process_key_event` fires once for key-press AND once for key-release. The release event also matched `keyval=65307` (Escape), causing `on_key_esc` to be called twice: first pause, then immediately close. Fixed by filtering `state & IBus.ModifierType.RELEASE_MASK`.

### Change 6: Window type POPUP → TOPLEVEL + UTILITY hint
`Gtk.WindowType.POPUP` causes GTK to automatically perform a pointer grab, blocking mouse clicks on all other windows while the handwriting panel is visible. Changed to `Gtk.WindowType.TOPLEVEL` with `set_type_hint(Gdk.WindowTypeHint.UTILITY)` — no input grab, no decorations, no taskbar entry.

### Change 7: Close button at top-left
Added `×` button to candidate bar top-left, hidden by default. It appears only after first Esc enters pause mode. Clicking it directly calls `_do_reset()`, `_do_disable()`, and `restore_previous_engine()` — same close behavior as second Esc press.

### Change 8: `_state` reset in `_do_disable` and `do_enable`
`_state` wasn't reset after `_do_disable()`, causing the first Esc after re-activation to close instead of pause. Fixed by adding `self._state = 0` in `_do_disable()` and `self.win._state = 0` in `do_enable()`.

## Verification
```bash
ibus engine handwrite-chinese-simplified  # activate
# Press Esc once: "Paused" overlay appears, mouse clicks still work elsewhere
# Click overlay: resumes normal input
# Press Esc twice: closes window, restores EN
ibus engine           # should show xkb:us::eng
```
